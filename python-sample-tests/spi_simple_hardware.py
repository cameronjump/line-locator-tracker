import Adafruit_GPIO.SPI as SPI

# Hardware SPI configuration:
SPI_PORT   = 0
SPI_DEVICE = 1
spi = SPI.SpiDev(SPI_PORT, SPI_DEVICE)
spi.set_bit_order(SPI.MSBFIRST)

def read_adc(spi, adc_number):
    spi.transfer([0x00])
    resp = spi.transfer([0xC0,0x00,0x00])
    print(resp)

read_adc(spi, 0)
spi.close()


# import spidev as spidev
# spi = spidev.SpiDev() 
# spi.open(0, 1)
# spi.max_speed_hz=100000 # set 1Mbps
# to_send = [0x08, 0xF, 0x00]
# resp = spi.xfer3(to_send)
# print(resp)