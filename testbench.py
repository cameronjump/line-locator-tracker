import RPi.GPIO as GPIO
import time
import sys
from datetime import datetime

from spi_simple import *

CLK = 11
MISO = 9
MOSI = 10
CS = 8

try:
    GPIO.setmode(GPIO.BCM)
    setupSpiPins(CLK, MISO, MOSI, CS)

    file = open("sample.txt", "a")
    
    before = time.time()
    sample_range = 50000
    for i in range(0,sample_range):
        val = readAdc(0, CLK, MISO, MOSI, CS)
        now = time.time()
        file.write(str(val)+'\n')
    after = time.time()

    print ("ADC Result: ", str(val))
    period = (after-before)/sample_range
    print ("Samples: ", sample_range, "\nTotal time: ", str(after-before), "\nSeconds/Sample: ", str(period), "\nFrequency: "+ str(1/period))
except KeyboardInterrupt:
    print("Interrupt")
file.close()
GPIO.cleanup()
sys.exit(0)