/*

rawMCP3202.c
Public Domain
2016-03-20

gcc -Wall -pthread -o read_adc_daemon read_adc_daemon.c -lpigpio

This code shows how to bit bang SPI using DMA.

Using DMA to bit bang allows for two advantages

1) the time of the SPI transaction can be guaranteed to within a
   microsecond or so.

2) multiple devices of the same type can be read or written
  simultaneously.

This code shows how to read more than one MCP3202 at a time.

Each MCP3202 shares the SPI clock, MOSI, and slave select lines but has
a unique MISO line.
*/

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include <pigpio.h>
#include <time.h>

#include <sys/time.h>
#include <sys/resource.h>


#define SPI_SS 8 // GPIO for slave select.

#define BITS 12            // Bits per reading.
#define BX 6               // Bit position of data bit B11.
#define B0 (BX + BITS - 1) // Bit position of data bit B0.

#define MISO1 9   // ADC 1 MISO.
#define MISO2 26  //     2
#define MISO3 19  //     3

#define BUFFER 250       // Generally make this buffer as large as possible.

#define ADCS 3

int REPEAT_MICROS = 40 ;

int SAMPLES = 10000;  // Number of samples to take,

int SAMPLE_SET_FREQUENCY = 30;

int MISO[ADCS]={MISO1, MISO2, MISO3};//, MISO2, MISO3, MISO4, MISO5};

rawSPI_t rawSPI =
{
   .clk     =  11, // GPIO for SPI clock.
   .mosi    = 10, // GPIO for SPI MOSI.
   .ss_pol  =  1, // Slave select resting level.
   .ss_us   =  1, // Wait 1 micro after asserting slave select.
   .clk_pol =  0, // Clock resting level.
   .clk_pha =  0, // 0 sample on first edge, 1 sample on second edge.
   .clk_us  =  1, // 2 clocks needed per bit so 500 kbps.
};

/*
   This function extracts the MISO bits for each ADC and
   collates them into a reading per ADC.
*/

long getMicrotime(){
	struct timeval currentTime;
	gettimeofday(&currentTime, NULL);
	return currentTime.tv_sec * (int)1e6 + currentTime.tv_usec;
}

void getReading(
   int adcs,  // Number of attached ADCs.
   int *MISO, // The GPIO connected to the ADCs data out.
   int OOL,   // Address of first OOL for this reading.
   int bytes, // Bytes between readings.
   int bits,  // Bits per reading.
   char *buf) 
{
   int i, a, p;
   uint32_t level;

   p = OOL;

   for (i=0; i<bits; i++)
   {
      level = rawWaveGetOut(p);

      for (a=0; a<adcs; a++)
      {
         putBitInBytes(i, buf+(bytes*a), level & (1<<MISO[a]));
      }

      p--;
   }
}

int performSampleLoop() {
    int i, wid, offset;
    char buf[2];
    gpioPulse_t final[2];
    char rx[8];
    int sample;
    int val;
    int cb, botCB, topOOL, reading, now_reading;
    float cbs_per_reading;
    rawWaveInfo_t rwi;
    double start, end;
    int pause;

    pause = 0;

    gpioWaveAddNew();
    gpioWaveClear();

   offset = 0;

   /*
   MCP3202 12-bit ADC 2 channels

   1  2  3  4  5  6   7   8  9  10 11 12 13 14 15 16 17
   SB SD OS MS NA B11 B10 B9 B8 B7 B6 B5 B4 B3 B2 B1 B0

   SB  1  1
   SD  1  0=differential 1=single
   OS  0  0=ch0, 1=ch1 (in single mode)
   MS  0  0=tx lsb first after tx msb first
   */

   /*
      Now construct lots of bit banged SPI reads.  Each ADC reading
      will be stored separately.  We need to ensure that the
      buffer is big enough to cope with any reasonable rescehdule.

      In practice make the buffer as big as you can.
   */

   for (i=0; i<BUFFER; i++)
   {
      buf[0] = 0xC0; // Start bit, single ended, channel 0.

      rawWaveAddSPI(&rawSPI, offset, SPI_SS, buf, 2, BX, B0, B0);

      /*
         REPEAT_MICROS must be more than the time taken to
         transmit the SPI message.
      */

      offset += REPEAT_MICROS;
   }

   // Force the same delay after the last reading.

   final[0].gpioOn = 0;
   final[0].gpioOff = 0;
   final[0].usDelay = offset;

   final[1].gpioOn = 0; // Need a dummy to force the final delay.
   final[1].gpioOff = 0;
   final[1].usDelay = 0;

   gpioWaveAddGeneric(2, final);

   wid = gpioWaveCreate(); // Create the wave from added data.

   if (wid < 0)
   {
      fprintf(stderr, "Can't create wave, %d too many?\n", BUFFER);
      return 1;
   }

   /*
      The wave resources are now assigned,  Get the number
      of control blocks (CBs) so we can calculate which reading
      is current when the program is running.
   */

   rwi = rawWaveInfo(wid);
   /*
   printf("# cb %d-%d ool %d-%d del=%d ncb=%d nb=%d nt=%d\n",
      rwi.botCB, rwi.topCB, rwi.botOOL, rwi.topOOL, rwi.deleted,
      rwi.numCB,  rwi.numBOOL,  rwi.numTOOL);
   */
   /*
      CBs are allocated from the bottom up.  As the wave is being
      transmitted the current CB will be between botCB and topCB
      inclusive.
   */

   botCB = rwi.botCB;

   /*
      Assume each reading uses the same number of CBs (which is
      true in this particular example).
   */

   cbs_per_reading = (float)rwi.numCB / (float)BUFFER;
   /*
   printf("# cbs=%d per read=%.1f base=%d\n",
      rwi.numCB, cbs_per_reading, botCB);
   */
   /*
      OOL are allocated from the top down. There are BITS bits
      for each ADC reading and BUFFER ADC readings.  The readings
      will be stored in topOOL - 1 to topOOL - (BITS * BUFFER).
   */

   topOOL = rwi.topOOL;

   if (pause) time_sleep(pause); // Give time to start a monitor.

   gpioWaveTxSend(wid, PI_WAVE_MODE_REPEAT);

   reading = 0;

   sample = 0;

   start = time_time();

   fprintf(stderr, "DS;");
   while (sample<SAMPLES)
   {
      // Which reading is current?

      cb = rawWaveCB() - botCB;

      now_reading = (float) cb / cbs_per_reading;

      // Loop gettting the fresh readings.

      while (now_reading != reading)
      {
         /*
            Each reading uses BITS OOL.  The position of this readings
            OOL are calculated relative to the waves top OOL.
         */
         getReading(
            ADCS, MISO, topOOL - ((reading%BUFFER)*BITS) - 1, 2, BITS, rx);

         ++sample;//printf("%d", ++sample);

         for (i=0; i<ADCS; i++)
         {
            //   7   6  5  4  3  2  1  0 |  7  6  5  4  3  2  1  0
            // B11 B10 B9 B8 B7 B6 B5 B4 | B3 B2 B1 B0  X  X  X  X

            val = (rx[i*2]<<4) + (rx[(i*2)+1]>>4);
            long timestamp = getMicrotime();
            fprintf(stderr,"%d,", i);
            fprintf(stderr,"%ld,", timestamp);
            fprintf(stderr,"%d", val);
            fprintf(stderr,";");
         }

         if (++reading >= BUFFER) reading = 0;
      }
   }

   end = time_time();

   fprintf(stderr, "\n");

   printf("last value %d", val);

   printf("# %d samples in %.1f seconds (%.0f/s)\n",
      SAMPLES, end-start, (float)SAMPLES/(end-start));

   //if (pause) time_sleep(pause);

   return 0;
}

int main(int argc, char *argv[])
{
    fprintf(stderr, "My PID:%d\n", getpid());
    setpriority(PRIO_PROCESS, 0, -20);

    if (argc > 3) {
        REPEAT_MICROS = (int) strtol(argv[1], NULL, 10);
        SAMPLES = (int) strtol(argv[2], NULL, 10);
        SAMPLE_SET_FREQUENCY = (int) strtol(argv[3], NULL, 10);
    } 

    int PERIOD = 1000000/SAMPLE_SET_FREQUENCY;

    fprintf(stderr, "REPEAT_MICROS %d SAMPLES %d\n", REPEAT_MICROS, SAMPLES);
    gpioCfgClock(/* micros */ 1, /* PWM */ 1, 0);

    float start_initalize = clock();
    
    if (gpioInitialise() < 0) return 1;

    float end_initalize = clock();
    printf("Initialization time %f, start %f, finish %f\n", end_initalize - start_initalize, start_initalize, end_initalize);

    gpioSetMode(rawSPI.clk,  PI_OUTPUT);
    gpioSetMode(rawSPI.mosi, PI_OUTPUT);
    gpioSetMode(SPI_SS,      PI_OUTPUT);

    while(1) {
      long start = getMicrotime();
      performSampleLoop();
      long finish = getMicrotime();
      int delay = finish - start;
      printf(" execution time %dus\n",delay);
      usleep(PERIOD);
    }

    gpioTerminate();

    return 0;
}

