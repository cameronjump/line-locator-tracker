#!/usr/bin/env python
#
# Bitbang'd SPI interface with an MCP3202 ADC device
# MCP3008 is 8-channel 10-bit analog to digital converter
#  Connections are:
#     CLK => 18  
#     DOUT => 23 (chip's data out, RPi's MISO)
#     DIN => 24  (chip's data in, RPi's MOSI)
#     CS => 25 

import RPi.GPIO as GPIO
import time
import sys

CLK = 11
MISO = 9
MOSI = 10
CS = 8

def setupSpiPins(clkPin, misoPin, mosiPin, csPin):
    ''' Set all pins as an output except MISO (Master Input, Slave Output)'''
    GPIO.setup(clkPin, GPIO.OUT)
    GPIO.setup(misoPin, GPIO.IN)
    GPIO.setup(mosiPin, GPIO.OUT)
    GPIO.setup(csPin, GPIO.OUT)


def readAdc(channel, clkPin, misoPin, mosiPin, csPin):
    if (channel < 0) or (channel > 1):
        print "Invalid ADC Channel number, must be between [0,7]"
        return -1
        
    # Datasheet says chip select must be pulled high between conversions
    GPIO.output(csPin, GPIO.HIGH)
    
    # Start the read with both clock and chip select low
    GPIO.output(csPin, GPIO.LOW)
    GPIO.output(clkPin, GPIO.HIGH)
    
    # read command is:
    # start bit = 1
    # single-ended comparison = 1 (vs. pseudo-differential)
    # channel num bit = 0 or 1
    # msb first = 1
    read_command = None
    if channel == 0:
        read_command = 0b1101
    else:
        read_command = 0b1111
    
    sendBits(read_command, 4, clkPin, mosiPin)
    
    adcValue = recvBits(13, clkPin, misoPin)
    
    # Set chip select high to end the read
    GPIO.output(csPin, GPIO.HIGH)
  
    return adcValue
    
def sendBits(data, numBits, clkPin, mosiPin):
    ''' Sends 1 Byte or less of data'''
    
    data <<= (8 - numBits)
    
    for bit in range(numBits):
        # Set RPi's output bit high or low depending on highest bit of data field
        if data & 0x80:
            GPIO.output(mosiPin, GPIO.HIGH)
        else:
            GPIO.output(mosiPin, GPIO.LOW)
        
        # Advance data to the next bit
        data <<= 1
        
        # Pulse the clock pin HIGH then immediately low
        GPIO.output(clkPin, GPIO.HIGH)
        GPIO.output(clkPin, GPIO.LOW)

def recvBits(numBits, clkPin, misoPin):
    '''Receives arbitrary number of bits'''
    retVal = 0
    string = ""
    
    for bit in range(numBits):
        
        # Pulse clock pin 
        GPIO.output(clkPin, GPIO.HIGH)
        GPIO.output(clkPin, GPIO.LOW)
        
        # Read 1 data bit in
        if GPIO.input(misoPin):
            string += "1"
            retVal |= 0x1
        else:
            string += "0"
        
        # Advance input to next bit
        retVal <<= 1
    
    # Divide by two to drop the NULL bit
    return string,(retVal/2)
    
    
if __name__ == '__main__':
    try:
        GPIO.setmode(GPIO.BCM)
        setupSpiPins(CLK, MISO, MOSI, CS)
    
        while True:
            val = readAdc(1, CLK, MISO, MOSI, CS)
            print "ADC Result: ", str(val)
            time.sleep(1)
    except KeyboardInterrupt:
        GPIO.cleanup()
sys.exit(0)