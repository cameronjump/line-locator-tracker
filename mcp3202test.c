/*
2014-08-10

gcc -o minimal_spi minimal_spi.c -lrt
sudo ./minimal_spi
*/

#include <stdio.h>
#include <unistd.h>
#include <stdint.h>
#include <string.h>
#include <fcntl.h>
#include <time.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/types.h>

/* Peripherals */

#define SYST_BASE  0x20003000
#define DMA_BASE   0x20007000
#define PADS_BASE  0x20100000
#define CLK_BASE   0x20101000
#define GPIO_BASE  0x20200000
#define UART0_BASE 0x20201000
#define PCM_BASE   0x20203000
#define SPI_BASE   0x20204000
#define I2C0_BASE  0x20205000
#define PWM_BASE   0x2020C000
#define UART1_BASE 0x20215000
#define I2C1_BASE  0x20804000
#define I2C2_BASE  0x20805000
#define DMA15_BASE 0x20E05000

#define DMA_LEN   0x1000 /* allow access to all channels */
#define CLK_LEN   0xA8
#define GPIO_LEN  0xB4
#define SYST_LEN  0x1C
#define PCM_LEN   0x24
#define PWM_LEN   0x28
#define I2C_LEN   0x1C
#define SPI_LEN   0x18
#define PADS_LEN  0x1000

/* GPIOs */

#define GPSET0 7
#define GPSET1 8

#define GPCLR0 10
#define GPCLR1 11

#define GPLEV0 13
#define GPLEV1 14

#define GPPUD     37
#define GPPUDCLK0 38
#define GPPUDCLK1 39

/* System 1us clock */

#define SYST_CS  0
#define SYST_CLO 1
#define SYST_CHI 2

/* SPI */

#define SPI_CS   0
#define SPI_FIFO 1
#define SPI_CLK  2
#define SPI_DLEN 3
#define SPI_LTOH 4
#define SPI_DC   5

#define SPI_CS_LEN_LONG  (1<<25)
#define SPI_CS_DMA_LEN   (1<<24)
#define SPI_CS_CSPOL2    (1<<23)
#define SPI_CS_CSPOL1    (1<<22)
#define SPI_CS_CSPOL0    (1<<21)
#define SPI_CS_RXF       (1<<20)
#define SPI_CS_RXR       (1<<19)
#define SPI_CS_TXD       (1<<18)
#define SPI_CS_RXD       (1<<17)
#define SPI_CS_DONE      (1<<16)
#define SPI_CS_LEN       (1<<13)
#define SPI_CS_REN       (1<<12)
#define SPI_CS_ADCS      (1<<11)
#define SPI_CS_INTR      (1<<10)
#define SPI_CS_INTD      (1<<9)
#define SPI_CS_DMAEN     (1<<8)
#define SPI_CS_TA        (1<<7)
#define SPI_CS_CSPOL(x)  ((x)<<6)
#define SPI_CS_CLEAR(x)  ((x)<<4)
#define SPI_CS_MODE(x)   ((x)<<2)
#define SPI_CS_CS(x)     ((x)<<0)

#define SPI_DC_RPANIC(x) ((x)<<24)
#define SPI_DC_RDREQ(x)  ((x)<<16)
#define SPI_DC_TPANIC(x) ((x)<<8)
#define SPI_DC_TDREQ(x)  ((x)<<0)

#define SPI_MODE0 0
#define SPI_MODE1 1
#define SPI_MODE2 2
#define SPI_MODE3 3

#define SPI_CS0     0
#define SPI_CS1     1
#define SPI_CS2     2

static volatile uint32_t *gpioReg = MAP_FAILED;
static volatile uint32_t *systReg = MAP_FAILED;
static volatile uint32_t *pwmReg  = MAP_FAILED;
static volatile uint32_t *clkReg  = MAP_FAILED;
static volatile uint32_t *padsReg = MAP_FAILED;
static volatile uint32_t *spiReg  = MAP_FAILED;
static volatile uint32_t *i2c0Reg = MAP_FAILED;
static volatile uint32_t *i2c1Reg = MAP_FAILED;

#define PI_BANK (gpio>>5)
#define PI_BIT  (1<<(gpio&0x1F))

/* SPI gpios. */

#define PI_SPI_CE0   8
#define PI_SPI_CE1   7
#define PI_SPI_SCLK 11
#define PI_SPI_MISO  9
#define PI_SPI_MOSI 10

/* gpio levels. */

#define PI_LOW  0
#define PI_HIGH 1

/* gpio modes. */

#define PI_INPUT  0
#define PI_OUTPUT 1
#define PI_ALT0   4
#define PI_ALT1   5
#define PI_ALT2   6
#define PI_ALT3   7
#define PI_ALT4   3
#define PI_ALT5   2

void gpioSetMode(unsigned gpio, unsigned mode)
{
   int reg, shift;

   reg   =  gpio/10;
   shift = (gpio%10) * 3;

   gpioReg[reg] = (gpioReg[reg] & ~(7<<shift)) | (mode<<shift);
}

int gpioGetMode(unsigned gpio)
{
   int reg, shift;

   reg   =  gpio/10;
   shift = (gpio%10) * 3;

   return (*(gpioReg + reg) >> shift) & 7;
}

/* Values for pull-ups/downs off, pull-down and pull-up. */

#define PI_PUD_OFF  0
#define PI_PUD_DOWN 1
#define PI_PUD_UP   2

void gpioSetPullUpDown(unsigned gpio, unsigned pud)
{
   *(gpioReg + GPPUD) = pud;

   usleep(20);

   *(gpioReg + GPPUDCLK0 + PI_BANK) = PI_BIT;

   usleep(20);
  
   *(gpioReg + GPPUD) = 0;

   *(gpioReg + GPPUDCLK0 + PI_BANK) = 0;
}

int gpioRead(unsigned gpio)
{
   if ((*(gpioReg + GPLEV0 + PI_BANK) & PI_BIT) != 0) return 1;
   else                                         return 0;
}

void gpioWrite(unsigned gpio, unsigned level)
{
   if (level == 0) *(gpioReg + GPCLR0 + PI_BANK) = PI_BIT;
   else            *(gpioReg + GPSET0 + PI_BANK) = PI_BIT;
}

void gpioTrigger(unsigned gpio, unsigned pulseLen, unsigned level)
{
   if (level == 0) *(gpioReg + GPCLR0 + PI_BANK) = PI_BIT;
   else            *(gpioReg + GPSET0 + PI_BANK) = PI_BIT;

   usleep(pulseLen);

   if (level != 0) *(gpioReg + GPCLR0 + PI_BANK) = PI_BIT;
   else            *(gpioReg + GPSET0 + PI_BANK) = PI_BIT;
}

/* Bit (1<<x) will be set if gpio x is high. */

uint32_t gpioReadBank1(void) { return (*(gpioReg + GPLEV0)); }
uint32_t gpioReadBank2(void) { return (*(gpioReg + GPLEV1)); }

/* To clear gpio x bit or in (1<<x). */

void gpioClearBank1(uint32_t bits) { *(gpioReg + GPCLR0) = bits; }
void gpioClearBank2(uint32_t bits) { *(gpioReg + GPCLR1) = bits; }

/* To set gpio x bit or in (1<<x). */

void gpioSetBank1(uint32_t bits) { *(gpioReg + GPSET0) = bits; }
void gpioSetBank2(uint32_t bits) { *(gpioReg + GPSET1) = bits; }

unsigned gpioHardwareRevision(void)
{
   static unsigned rev = 0;

   FILE * filp;
   char buf[512];
   char term;

   if (rev) return rev;

   filp = fopen ("/proc/cpuinfo", "r");

   if (filp != NULL)
   {
      while (fgets(buf, sizeof(buf), filp) != NULL)
      {
         if (!strncasecmp("revision\t", buf, 9))
         {
            if (sscanf(buf+strlen(buf)-5, "%x%c", &rev, &term) == 2)
            {
               if (term == '\n') break;
               rev = 0;
            }
         }
      }
      fclose(filp);
   }
   return rev;
}

/* Returns the number of microseconds after system boot. Wraps around
   after 1 hour 11 minutes 35 seconds.
*/

uint32_t gpioTick(void) { return systReg[SYST_CLO]; }


double time_time(void)
{
   struct timeval tv;
   double t;

   gettimeofday(&tv, 0);

   t = (double)tv.tv_sec + ((double)tv.tv_usec / 1E6);

   return t;
}

void time_sleep(double seconds)
{
   struct timespec ts, rem;

   if (seconds > 0.0)
   {
      ts.tv_sec = seconds;
      ts.tv_nsec = (seconds-(double)ts.tv_sec) * 1E9;

      while (clock_nanosleep(CLOCK_REALTIME, 0, &ts, &rem))
      {
         /* copy remaining time to ts */
         ts.tv_sec  = rem.tv_sec;
         ts.tv_nsec = rem.tv_nsec;
      }
   }
}

/*SPI */

static unsigned old_mode_ce0;
static unsigned old_mode_ce1;
static unsigned old_mode_sclk;
static unsigned old_mode_miso;
static unsigned old_mode_mosi;

static uint32_t old_spi_cs;
static uint32_t old_spi_clk;

void spiInit(void)
{
   old_mode_ce0  = gpioGetMode(PI_SPI_CE0);
   old_mode_ce1  = gpioGetMode(PI_SPI_CE1);
   old_mode_sclk = gpioGetMode(PI_SPI_SCLK);
   old_mode_miso = gpioGetMode(PI_SPI_MISO);
   old_mode_mosi = gpioGetMode(PI_SPI_MOSI);

   gpioSetMode(PI_SPI_CE0, PI_ALT0);
   gpioSetMode(PI_SPI_CE1, PI_ALT0);
   gpioSetMode(PI_SPI_SCLK, PI_ALT0);
   gpioSetMode(PI_SPI_MISO, PI_ALT0);
   gpioSetMode(PI_SPI_MOSI, PI_ALT0);

   old_spi_cs  = spiReg[SPI_CS];
   old_spi_clk = spiReg[SPI_CLK];
}

void spiTerm(void)
{  
   gpioSetMode(PI_SPI_CE0, old_mode_ce0);
   gpioSetMode(PI_SPI_CE1, old_mode_ce1);
   gpioSetMode(PI_SPI_SCLK, old_mode_sclk);
   gpioSetMode(PI_SPI_MISO, old_mode_miso);
   gpioSetMode(PI_SPI_MOSI, old_mode_mosi);

   spiReg[SPI_CS]  = old_spi_cs;
   spiReg[SPI_CLK] = old_spi_clk;
}

void spiXfer(
   unsigned speed,    /* bits per second        */
   unsigned channel,  /* 0 or 1                 */
   unsigned mode,     /* 0 - 3                  */
   unsigned cspol,    /* 0 = active low         */
   char     *txBuf,   /* tx buffer              */
   char     *rxBuf,   /* rx buffer              */
   unsigned cnt4w,    /* number of 4-wire bytes */
   unsigned cnt3w)    /* number of 3-wire bytes */
{
   unsigned txCnt=0;
   unsigned rxCnt=0;
   unsigned cnt;
   uint32_t spiDefaults;

   spiDefaults = SPI_CS_MODE(mode)   |
                 SPI_CS_CS(channel)  |
                 SPI_CS_CSPOL(cspol) |
                 SPI_CS_CLEAR(3);

   spiReg[SPI_CLK] = 250000000/speed;

   spiReg[SPI_CS] = spiDefaults | SPI_CS_TA; /* start */

   cnt = cnt4w;

   while((txCnt < cnt) || (rxCnt < cnt))
   {
      while((txCnt < cnt) && ((spiReg[SPI_CS] & SPI_CS_TXD)))
      {
         spiReg[SPI_FIFO] = txBuf[txCnt++];
      }

      while((rxCnt < cnt) && ((spiReg[SPI_CS] & SPI_CS_RXD)))
      {
         rxBuf[rxCnt++] = spiReg[SPI_FIFO];
      }
   }

   while (!(spiReg[SPI_CS] & SPI_CS_DONE)) ;

   /* now switch to 3-wire bus */

   cnt += cnt3w;

   while((txCnt < cnt) || (rxCnt < cnt))
   {
      spiReg[SPI_CS] |= SPI_CS_REN;

      while((txCnt < cnt) && ((spiReg[SPI_CS] & SPI_CS_TXD)))
      {
         spiReg[SPI_FIFO] = txBuf[txCnt++];
      }

      while((rxCnt < cnt) && ((spiReg[SPI_CS] & SPI_CS_RXD)))
      {
         rxBuf[rxCnt++] = spiReg[SPI_FIFO];
      }
   }

   while (!(spiReg[SPI_CS] & SPI_CS_DONE)) ;

   spiReg[SPI_CS] = spiDefaults; /* stop */
}

/* Map in registers. */

static uint32_t * initMapMem(int fd, uint32_t addr, uint32_t len)
{
    return (uint32_t *) mmap(0, len,
       PROT_READ|PROT_WRITE|PROT_EXEC,
       MAP_SHARED|MAP_LOCKED,
       fd, addr);
}

int gpioInitialise(void)
{
   int fd;

   fd = open("/dev/mem", O_RDWR | O_SYNC) ;

   if (fd < 0)
   {
      fprintf(stderr,
         "This program needs root privileges.  Try using sudo\n");
      return -1;
   }

   gpioReg = initMapMem(fd, GPIO_BASE, GPIO_LEN);
   systReg = initMapMem(fd, SYST_BASE, SYST_LEN);
   pwmReg  = initMapMem(fd, PWM_BASE,  PWM_LEN);
   clkReg  = initMapMem(fd, CLK_BASE,  CLK_LEN);
   padsReg = initMapMem(fd, PADS_BASE, PADS_LEN);
   spiReg  = initMapMem(fd, SPI_BASE,  SPI_LEN);

   close(fd);

   if ((gpioReg == MAP_FAILED) || (systReg == MAP_FAILED))
   {
      fprintf(stderr,
         "Bad, mmap failed\n");
      return -1;
   }
   return 0;
}

int read_mcp3202(
   unsigned speed,
   unsigned spi_channel,
   unsigned mode,
   unsigned adc_channel)
{
   const int msglen = 3;

   char txBuf[msglen];
   char rxBuf[msglen];

   txBuf[0] = 1;
   if (adc_channel == 0) txBuf[1] = 0x80; else txBuf[1] = 0xC0;
   txBuf[2] = 0;

   /* speed, channel, mode, cspol, *txBuf,*rxBuf,cnt4w,cnt3w */

   spiXfer(speed, spi_channel, mode, 0, txBuf, rxBuf, msglen, 0); /* SPI xfer */

   return ((rxBuf[1]&0x0F)<<8) + rxBuf[2];
}

int mcp3202_test(int argc, char *argv[])
{
   int i;

   int speed, iters, maxsps, pf;

   unsigned divider;

   unsigned reading[4096];
   unsigned val;

   double start, duration;

   uint32_t nt, micros;
   int tdiff;

   if (argc >= 4)
   {
      speed  = atoi(argv[1]);
      iters  = atoi(argv[2]);
      maxsps = atoi(argv[3]);
      micros = 1000000 / maxsps;
      if (argc > 4) pf = 1; else pf = 0;
   }
   else
   {
      fprintf(stderr, "need Speed(bps), Samples, Max sps.\n");
      fprintf(stderr, "sudo ./spi 2500000 1000000 100000\n");
      return 1;
   }

   for (i=0; i<4096; i++) reading[i]= 0;

   /* An MCP3202 is being used for testing.  Read channel 0 */
   /* Max speed 2.5MHz clock, 100ksps @ 5V                  */

   divider = 250000000/speed;
   if (divider % 1) divider++;

   spiInit(); /* save old SPI settings, initialise */

   printf ("selected speed=%d (set=%u) iters=%d xfer=3 mingap=%d\n",
      speed, 250000000/divider, iters, micros);

   start = time_time();

   for (i=0; i<iters; i++)
   {
      nt = gpioTick() + micros;

      val = read_mcp3202(speed, 1, 0, 0);

      if (pf) printf("%u\n", val);

      reading[(val/10)*10]++;

      do /* rate limit */
      {
         tdiff = nt - gpioTick();
      } while (tdiff > 0);
   }

   duration = time_time()  - start;

   spiTerm(); /* restore old SPI settings */

   for (i=0; i<4096; i++)
   {
      if (reading[i]) printf("%d %d\n", i, reading[i]);
   }

   printf("%.0f sps over %.1f seconds\n", ((float)iters)/(duration), duration);

   return 0;
}

int mcp4131_test(int argc, char *argv[])
{
   int i;

   int speed, iters, maxsps, pf;

   const int msglen = 2;
   const int maxset = 129;
   const int maxreading = 1024;
   unsigned divider;
   char txBuf[msglen];
   char rxBuf[msglen];

   unsigned reading[maxreading];

   unsigned val;

   double start, duration;

   uint32_t nt, micros;
   int tdiff;

   if (argc >= 4)
   {
      speed  = atoi(argv[1]);
      iters  = atoi(argv[2]);
      maxsps = atoi(argv[3]);
      micros = 1000000 / maxsps;
      if (argc > 4) pf = 1; else pf = 0;
   }
   else
   {
      fprintf(stderr, "need Speed(bps), Samples, Max sps.\n");
      fprintf(stderr, "sudo ./spi 2500000 1000000 100000\n");
      return 1;
   }

   divider = 250000000/speed;
   if (divider % 1) divider++;

   for (i=0; i<maxreading; i++) reading[i] = 0;

   spiInit(); /* save old SPI settings, initialise */

   printf ("selected speed=%d (set=%u) iters=%d xfer=%d mingap=%d\n",
      speed, 250000000/divider, iters, msglen, micros);

   start = time_time();

   for (i=0; i<iters; i++)
   {
      nt = gpioTick() + micros;

      /* set wiper 0 position */

      txBuf[0] = 0; /* write wiper 0 */
      txBuf[1] = i%maxset;

      /* speed, channel, mode, cspol, *txBuf,*rxBuf,cnt4w,cnt3w */

      spiXfer(speed, 0, 0, 0, txBuf, rxBuf, 2, 0); /* SPI xfer */

      /* read position back */

      usleep(1);

      /* see what mcp3202 thinks */

      val = read_mcp3202(1000000, 1, 0, 1);

      usleep(1);

      txBuf[0] = 0x0C; /* read wiper 0 */
      txBuf[1] = 0;

      rxBuf[1] = 0;

      spiXfer(250000, 0, 0, 0, txBuf, rxBuf, 1, 1); /* SPI xfer */

      if (pf) printf("%u %u (%u)\n", i%maxset, rxBuf[1], val);

      do /* rate limit */
      {
         tdiff = nt - gpioTick();
      } while (tdiff > 0);
   }

   duration = time_time()  - start;

   spiTerm(); /* restore old SPI settings */

   for (i=0; i<maxreading; i++)
   {
      if (reading[i]) printf("%d %d\n", i, reading[i]);
   }

   printf("%.0f sps over %.1f seconds\n", ((float)iters)/(duration), duration);

   return 0;
}

main(int argc, char *argv[])
{
   if (gpioInitialise() < 0) return 1;

   return mcp3202_test(argc, argv);
}