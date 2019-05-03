from subprocess import check_output, call, Popen, PIPE, STDOUT
import sys
import time
import os
from enum import Enum

from threading  import Thread
from queue import Queue, Empty

from flask import Flask, jsonify

import pygame
from pygame.locals import *

from helper import *
from pipe import *

import RPi.GPIO as GPIO

app = Flask(__name__)

os.putenv('SDL_FBDEV', '/dev/fb1')
os.putenv('SDL_VIDEODRIVER', 'fbcon')
os.putenv('SDL_MOUSEDRV', 'TSLIB')
os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')

app = Flask(__name__)

past_values0 = []
past_values1 = []
past_values_ref = []

dpsk_array = []

LOCATINGPIN = 12
TRACKING12PIN = 16
TRACKING28PIN = 21

GAINCSPIN = 13
GAINCLKPIN = 5
GAINDATAPIN = 26

calibration_distance = 120 #distance in inches
calibration_value = 1
gain_value = 1

#button update requests
update_mode_request = True
update_calibration_distance_request = True
update_calibration_value_request = True
update_gain_request = True


#frequencies 
#Locating 8.19
#Tracking 12.04
#Tracking 29.43
class Mode(Enum):
        LOCATING = ' Locating 8.19Khz'
        TRACKING12 = 'Tracking 12.04Khz'
        TRACKING29 = 'Tracking 29.43Khz'

message = 'TEAM1FTW'
current_value = 0
value0 = 0
value1 = 0
value_ref = 0
current_mode = Mode.LOCATING


def set_mode_pin(pin):
    global LOCATINGPIN, TRACKING12PIN, TRACKING28PIN
    GPIO.output(LOCATINGPIN, GPIO.LOW)
    GPIO.output(TRACKING12PIN, GPIO.LOW)
    GPIO.output(TRACKING28PIN, GPIO.LOW)
    GPIO.output(pin, GPIO.HIGH)

def set_gain(b):
    if b == 256:
        b == 255
    global GAINCSPIN, GAINCLKPIN, GAINDATAPIN
    b = "0000" "00" "{0:010b}".format(b)

    GPIO.output(GAINCSPIN, GPIO.LOW)
    for x in b:
        GPIO.output(GAINDATAPIN, int(x))
        GPIO.output(GAINCLKPIN, GPIO.HIGH)
        GPIO.output(GAINCLKPIN, GPIO.LOW)

    GPIO.output(GAINCSPIN, GPIO.HIGH)

def enqueue_output(process, queue):
    while process.poll() is None:
        for line in iter(process.stdout.readline, ""):
            line = line.decode('UTF-8').replace('\n', '')
            queue.put(line)
    process.close()

def read_adc_pipe(micros_between_readings, samples):
    process = open_pipe(micros_between_readings, samples)

    while process.poll() is None:
        for line in iter(process.stdout.readline, ""):
            line = line.decode('UTF-8').replace('\n', '')
            process_line(line)

def process_line(line):
    global current_value, value0, value1, value_ref, past_values0, past_values1, dpsk_array, message

    DEBUG = True

    if line[0:2] == 'DS':
        timestamps0 = []
        values0 = []
        timestamps1 = []
        values1 = []
        timestamps2 = []
        values_ref = []

        samples = line.split(';')
        for sample in samples:
            try:
                if DEBUG: print('Sample',sample)
                adc, timestamp, value = sample.split(',') 
                if DEBUG: print('ADC',adc)
                if "A" in adc:
                    sampleset, adc = adc.split('A')
                    print('SAMPLESET ADC',sampleset, adc)
                    if sampleset == 0 and len(dpsk_array) != 0:
                        dpsk_array.clear()
                if adc == '0':
                    timestamps0.append(int(timestamp))
                    values0.append(int(value))
                if adc == '1':
                    timestamps1.append(int(timestamp))
                    values1.append(int(value))
                if adc == '2':
                    timestamps2.append(int(timestamp))
                    values_ref.append(int(value))
            except:
                continue
        
        if len(values0)  == 0 or len(values1) == 0 or len(values_ref) == 0:
            return

        #delete first value
        del values0[0]
        del timestamps0[0]
        del values1[0]
        del timestamps1[0]
        del values_ref[0]
        del timestamps2[0]

        #adjusted_timestamps = adjust_timestamps(timestamps0)
        voltages0 = list_to_voltage(values0)
        voltages1 = list_to_voltage(values1)
        reference_value = sum(values_ref)/len(values_ref)

        adjusted_values0 = list(map(lambda x: x-reference_value, values0))
        adjusted_values1 = list(map(lambda x: x-reference_value, values1))
        adjusted_values0 = list(map(abs, adjusted_values0))
        adjusted_values1 = list(map(abs, adjusted_values1))

        #DPSK
        if current_mode != Mode.LOCATING:
            dpsk_array.append(timestamps0[index_of_max(adjusted_values0)])

            if len(dpsk_array) >= 361:
                if DEBUG: print('DPSK ARRAY', dpsk_array)
                dpsk_array0 = list(map(lambda x: x-dpsk_array[0], dpsk_array))
                lowbound = 21
                highbound = 62
                mod = 83
                if current_mode == Mode.TRACKING29:
                    lowbound = 8
                    highbound = 26
                    mod = 34
                phases = []
                basetime = dpsk_array[0]
                for stamp in dpsk_array:
                    phases.append(inPhase(basetime, stamp, 21, 62, 83))
                dpsk_string = phase_array_to_dpsk_string(phases)
                if DEBUG: print('DPSK ARRAY', dpsk_array)
                try:
                    start_index = dpskstring.index('11111110', lastindex)
                    bits, output = retrieve_message(dpsk_string, start_index)  
                    if DEBUG: print('BITS OUTPUT', bits, output)
                    message = output
                except Exeception as e:
                    print(str(e))
            dpsk_array.clear()


        past_values0.append(max(adjusted_values0))
        past_values1.append(max(adjusted_values1))
        past_values_ref.append(reference_value)

        if(len(past_values0) > 20):
            del past_values0[0]
        if(len(past_values1) > 20):
            del past_values1[0]
        if(len(past_values_ref) > 20):
            del past_values_ref[0]

        value0 = sum(past_values0)/len(past_values0)
        value1 = sum(past_values1)/len(past_values1)
        value_ref = sum(past_values_ref)/len(past_values_ref)

        if current_mode == Mode.LOCATING:
            k = 1.00
            try:
                ratio = to_voltage(value0)/to_voltage(value1)
                d1 = k/ (ratio - 1)
                current_value = d1
            except:
                print('Divide by 0 error')
        else:
            denom = value0 / (gain_value * .390625)
            ratio = calibration_value / denom
            depth = ratio ** (1. / 3)
            current_value = depth / 12




def process_queue(queue):
     while True:
            try:
                line = queue.get_nowait()
            except Empty:
                continue
            else:
                process_line(line)

@app.route('/api', methods=['GET'])
def get_value():
    global current_mode, current_value, value0, value1, value_ref, message, gain_value, calibration_distance, calibration_value
    return '{},{},{},{},{},{},{},{},{}'.format(current_mode.value, current_value, value0, value1, value_ref,message, gain_value, calibration_distance, calibration_value)

def start_app():
    global app
    app.run('0.0.0.0')

@app.route('/minusgain', methods=['POST'])
def minus_gain():
    global update_value, update_gain_request, gain_value
    if gain_value >= 2:
            gain_value = int(gain_value / 2)
            update_gain_request = True

@app.route('/plusgain', methods=['POST'])
def plus_gain():
    global update_value, update_gain_request, gain_value
    if gain_value <= 128:
            gain_value = gain_value * 2
            update_gain_request = True  

@app.route('/locating', methods=['POST'])
def switch_to_locating():
    global current_mode, update_mode_request
    current_mode = Mode.LOCATING
    update_mode_request = True


@app.route('/tracking12', methods=['POST'])
def switch_to_tracking12():
    global current_mode, update_mode_request
    current_mode = Mode.TRACKING12
    update_mode_request = True   

@app.route('/tracking29', methods=['POST'])
def switch_to_tracking29():
    global current_mode, update_mode_request
    current_mode = Mode.TRACKING29
    update_mode_request = True 

@app.route('/calibrate', methods=['POST'])
def calibrate():
    global calibration_value, calibration_distance, update_calibration_value_request, past_values0, gain_value
    sreading = sum(past_values0)/len(past_values0)
    d3 = calibration_distance * calibration_distance * calibration_distance
    calibration_value = d3 * (sreading / (.390625 * gain_value))
    update_calibration_value_request

@app.route('/minuscalibration', methods=['POST'])
def minus_calibration():
    global calibrate, update_calibration_distance_request, calibration_distance
    if calibration_distance > 0:
            calibration_distance -= 1
            update_calibration_distance_request = True

@app.route('/pluscalibration', methods=['POST'])
def plus_calibration():
    global calibrate, update_calibration_distance_request, calibration_distance
    calibration_distance += 1
    update_calibration_distance_request = True  

def main():
    global current_value, value0, value1, value_ref, message, current_mode, calibration_distance, calibration_value, gain_value, update_mode_request, update_calibration_distance_request, update_calibration_distance_request, update_calibration_value_request, dpsk_array

    #colors
    WHITE = (255, 255, 255)
    BLACK = (0,0,0)
    ORANGE = (255, 125, 25)
    BACKGROUND_COLOR = WHITE

    #setup font
    pygame.font.init()
    buttonFont = pygame.font.SysFont('default', 17)
    textFont = pygame.font.SysFont('default', 30)
    numberFont = pygame.font.SysFont('default', 40)

    #setup
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((480,320))
    pygame.mouse.set_visible(False)

    #base sreen
    screen.fill(BACKGROUND_COLOR)
    textsurface = textFont.render('TEAM 1', False, ORANGE)
    screen.blit(textsurface,(20,10))
    textsurface = textFont.render('Depth', False, ORANGE)
    screen.blit(textsurface,(20,50))
    textsurface = textFont.render('Message', False, ORANGE)
    screen.blit(textsurface,(20,130))
    textsurface = textFont.render('Magnitudes', False, ORANGE)
    screen.blit(textsurface,(260,50))
    textsurface = textFont.render('Value 0', False, BLACK)
    screen.blit(textsurface,(260,90))
    textsurface = textFont.render('Value 1', False, BLACK)
    screen.blit(textsurface,(260,130))
    textsurface = textFont.render('Reference', False, BLACK)
    screen.blit(textsurface,(260,170))
    screen.fill(BLACK, Rect((0,35),(480, 5)))

    #mode buttons
    locating8_button = create_button(screen, 'Locating 8.19Khz', WHITE, ORANGE, (20, 210), (140,40), buttonFont)
    tracking12_button = create_button(screen, 'Tracking 12.04Khz', WHITE, ORANGE, (167, 210), (140,40), buttonFont)
    tracking29_button = create_button(screen, 'Tracking 29.43Khz', WHITE, ORANGE, (167, 260), (140,40), buttonFont)

    #gain
    textsurface = buttonFont.render('Gain', False, BLACK)
    screen.blit(textsurface,(77,265))
    minus_gain_button = create_button(screen, '-', WHITE, ORANGE, (20, 260), (40,40), numberFont)
    plus_gain_button = create_button(screen, '+', WHITE, ORANGE, (120, 260), (40,40), numberFont)

    #calibration
    calibration_button = create_button(screen, 'Calibrate', WHITE, ORANGE, (314, 210), (140,40), buttonFont)
    textsurface = buttonFont.render('Distance', False, BLACK)
    screen.blit(textsurface,(359,265))
    minus_calibration_button = create_button(screen, '-', WHITE, ORANGE, (314, 260), (40,40), numberFont)
    plus_calibration_button = create_button(screen, '+', WHITE, ORANGE, (414, 260), (40,40), numberFont)

    pygame.display.update()

    increment = 0

    while True:

        rects = []

        if update_mode_request:
            print(current_mode.value)
            dpsk_array.clear()
            current_mode_rect = display_text(screen, current_mode.value, BLACK , BACKGROUND_COLOR, (300,10), 180, textFont)
            rects.append(current_mode_rect)
            if current_mode == Mode.TRACKING12:
                set_mode_pin(TRACKING12PIN)
            elif current_mode == Mode.TRACKING29:
                set_mode_pin(TRACKING28PIN)
            elif current_mode == Mode.LOCATING:
                set_mode_pin(LOCATINGPIN)

            update_mode_request = False

        if update_calibration_distance_request:
            calibration_string = '{}in'.format(calibration_distance)
            calibration_rect = pygame.Rect((357,280), (57,20))
            text_surface = textFont.render(calibration_string, False, BLACK)
            screen.fill(BACKGROUND_COLOR, calibration_rect)
            screen.blit(text_surface,(357,280))
            rects.append(calibration_rect)
            update_calibration_distance = False

        if update_calibration_value_request:
            if calibration_value == 1:
                calibration_string = 'Calibration Value = UNSET'
            else:
                calibration_string = 'Calibration Value = SET'
            text_surface = buttonFont.render(calibration_string, False, BLACK)
            calibration_value_rect = pygame.Rect((150,15), (140,20))
            screen.fill(BACKGROUND_COLOR, calibration_value_rect)
            screen.blit(text_surface,(150,15))
            rects.append(calibration_value_rect)
            update_calibration_distance = False

        if update_gain_request:
            text_surface = textFont.render(str(gain_value), False, BLACK)
            set_gain(gain_value)
            gain_rect = pygame.Rect((65,280), (50,20))
            screen.fill(BACKGROUND_COLOR, gain_rect)
            screen.blit(text_surface,(77,280))
            rects.append(gain_rect)
            update_calibration_distance = False
        
        depth_rect = display_text(screen, "{:.2f}ft".format(current_value), BLACK , BACKGROUND_COLOR, (20,90), 100, numberFont)
        message_rect = display_text(screen, message, BLACK , BACKGROUND_COLOR, (20,170), 200, textFont)
        value0_rect = display_text(screen, "{:.2f}V".format(to_voltage(value0)), BLACK , BACKGROUND_COLOR, (380,85), 100, numberFont)
        value1_rect = display_text(screen, "{:.2f}V".format(to_voltage(value1)), BLACK , BACKGROUND_COLOR, (380,125), 100, numberFont)
        ref_rect = display_text(screen, "{:.2f}V".format(to_voltage(value_ref)), BLACK , BACKGROUND_COLOR, (380,165), 100, numberFont)
        rects += [depth_rect, value0_rect, value1_rect, ref_rect, message_rect]

        pygame.display.update(rects)
            
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONUP:
                pos = pygame.mouse.get_pos()
                if locating8_button.collidepoint(pos):
                    switch_to_locating()
                elif tracking12_button.collidepoint(pos):
                    switch_to_tracking12() 
                elif tracking29_button.collidepoint(pos):
                    switch_to_tracking29()
                elif calibration_button.collidepoint(pos):
                    calibrate()
                elif minus_gain_button.collidepoint(pos):
                    minus_gain()
                elif plus_gain_button.collidepoint(pos):
                    plus_gain()
                elif minus_calibration_button.collidepoint(pos):
                    minus_calibration()
                elif plus_calibration_button.collidepoint(pos):
                    plus_calibration()     
            elif event.type == pygame.QUIT:
                pygame.display.quit()
                pygame.quit()  # Hangs here
                sys.exit()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.display.quit()
                    pygame.quit()  # Hangs here
                    sys.exit()          
        increment += 1
        clock.tick(10)

if __name__== '__main__':

    #GPIO setup
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    #Multiplexing
    GPIO.setup(LOCATINGPIN, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(TRACKING12PIN, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(TRACKING28PIN, GPIO.OUT, initial=GPIO.LOW)

    #Gain
    GPIO.setup(GAINCSPIN, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(GAINCLKPIN, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(GAINDATAPIN, GPIO.OUT, initial=GPIO.LOW)

    close_pipe()
    p = open_pipe(80,10,30)
    q = Queue()
    t1 = Thread(target=enqueue_output, args=(p,q))
    t1.daemon = True
    t1.start()

    t2 = Thread(target=process_queue, args=(q,))
    t2.daemon = True
    t2.start()

    t3 = Thread(target=start_app)
    t3.daemon = True
    t3.start()

    try:
        main()
    finally:
        GPIO.cleanup()

    