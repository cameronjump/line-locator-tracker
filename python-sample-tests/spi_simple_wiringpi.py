#!/usr/bin/env python
#
# Bitbang'd SPI interface with an MCP3008 ADC device
# MCP3008 is 8-channel 10-bit analog to digital converter
#  Connections are:
#     CLK => 18  
#     DOUT => 23 (chip's data out, RPi's MISO)
#     DIN => 24  (chip's data in, RPi's MOSI)
#     CS => 25 

import wiringpi
import time
import sys


OUTPUT = 1
INPUT = 0
HIGH = 1
LOW = 0

CLK = 11
MISO = 9
MOSI = 10
CS = 8

def setupSpiPins(clkPin, misoPin, mosiPin, csPin):
    ''' Set all pins as an output except MISO (Master Input, Slave Output)'''
    wiringpi.pinMode(clkPin, OUTPUT)
    wiringpi.pinMode(misoPin, INPUT)
    wiringpi.pinMode(mosiPin, OUTPUT)
    wiringpi.pinMode(csPin, OUTPUT)
     

def readAdc(channel, clkPin, misoPin, mosiPin, csPin):
    if (channel < 0) or (channel > 1):
        print("Invalid ADC Channel number, must be between [0,7]")
        return -1
        
    # Datasheet says chip select must be pulled high between conversions
    wiringpi.digitalWrite(csPin, HIGH)
    
    # Start the read with both clock and chip select low
    wiringpi.digitalWrite(csPin, LOW)
    wiringpi.digitalWrite(clkPin, HIGH)
    
    # read command is:
    # start bit = 1
    # single-ended comparison = 1 (vs. pseudo-differential)
    # channel num bit 2
    # channel num bit 1
    # channel num bit 0 (LSB)
    read_command = 0b1100
    read_command |= channel
    
    sendBits(read_command, 5, clkPin, mosiPin)
    
    adcValue = recvBits(12, clkPin, misoPin)
    
    # Set chip select high to end the read
    wiringpi.digitalWrite(csPin, HIGH)
  
    return adcValue
    
def sendBits(data, numBits, clkPin, mosiPin):
    ''' Sends 1 Byte or less of data'''
    
    data <<= (8 - numBits)
    
    for bit in range(numBits):
        # Set RPi's output bit high or low depending on highest bit of data field
        if data & 0x80:
            wiringpi.digitalWrite(mosiPin, HIGH)
        else:
            wiringpi.digitalWrite(mosiPin, LOW)
        
        # Advance data to the next bit
        data <<= 1
        
        # Pulse the clock pin HIGH then immediately low
        wiringpi.digitalWrite(clkPin, HIGH)
        wiringpi.digitalWrite(clkPin, LOW)

def recvBits(numBits, clkPin, misoPin):
    '''Receives arbitrary number of bits'''
    retVal = 0
    
    for bit in range(numBits):
        # Pulse clock pin 
        wiringpi.digitalWrite(clkPin, HIGH)
        wiringpi.digitalWrite(clkPin, LOW)
        
        # Read 1 data bit in
        if wiringpi.digitalRead(misoPin):
            retVal |= 0x1
        
        # Advance input to next bit
        retVal <<= 1
    
    # Divide by two to drop the NULL bit
    return (retVal/2)
    
    
if __name__ == '__main__':
    try:
        wiringpi.wiringPiSetupGpio()
        setupSpiPins(CLK, MISO, MOSI, CS)
    
        while True:
            val = readAdc(0, CLK, MISO, MOSI, CS)
            print("ADC Result: ", str(val))
            time.sleep(.1)
    except KeyboardInterrupt:
        sys.exit(0)
