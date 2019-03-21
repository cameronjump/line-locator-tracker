#!/usr/bin/env python

import pigpio
import time
import sys
from datetime import datetime

CLK = 11
MISO = 9
MOSI = 10
CS = 8

pi = pigpio.pi()
if not pi.connected:
   exit()

#pi.bb_spi_open(CS, MISO, MOSI, CLK, 500000, 0)
pi.spi_open(0, 500000)

#count, data = pi.bb_spi_xfer(CS, [0xC0, 0x00, 0x00,0x0])
#print(count, data)

before = time.time()
SAMPLE_RANGE = 10000
for i in range(0,SAMPLE_RANGE):

    #count, data = pi.bb_spi_xfer(CS, [0xC0, 0x00, 0x00])
    count, data = pi.spi_xfer(0, [0xC0, 0x00, 0x00])

after = time.time()

print ("ADC Result: ", str(data))
period = (after-before)/SAMPLE_RANGE
print ("Samples: ", SAMPLE_RANGE, "\nTotal time: ", str(after-before), "\nSeconds/Sample: ", str(period), "\nFrequency: "+ str(1/period))

pi.spi_close(0)
pi.stop()