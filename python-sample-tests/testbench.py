import RPi.GPIO as GPIO
import time
import sys
from datetime import datetime

import numpy as np

from spi_simple_rpi import *
#from spi_simple_wiringpi import *

CLK = 11
MISO = 9
MOSI = 10
CS = 8

SAMPLE_RANGE = 50000
FREQUENCY = 5000
SECOND_WAIT = float(1) / float(FREQUENCY)

try:
    GPIO.setmode(GPIO.BCM)
    #wiringpi.wiringPiSetupGpio()
    setupSpiPins(CLK, MISO, MOSI, CS)

    file = open("sample.txt", "a")
    
    before = time.time()
    SAMPLE_RANGE = 50000
    for i in range(0,SAMPLE_RANGE):
        begin_sample_time = time.time()

        val = readAdc(0, CLK, MISO, MOSI, CS)
        now = time.time()
        file.write(str(now)+','+str(val)+'\n')

        #print(SECOND_WAIT)
        #print(sample_time)
        while(time.time() - begin_sample_time < SECOND_WAIT):
            pass
    after = time.time()

    print ("ADC Result: ", str(val))
    period = (after-before)/SAMPLE_RANGE
    print ("Samples: ", SAMPLE_RANGE, "\nTotal time: ", str(after-before), "\nSeconds/Sample: ", str(period), "\nFrequency: "+ str(1/period))
except KeyboardInterrupt:
    print("Interrupt")
file.close()
sys.exit(0)