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

os.putenv('SDL_FBDEV', '/dev/fb1')
os.putenv('SDL_VIDEODRIVER', 'fbcon')
os.putenv('SDL_MOUSEDRV', 'TSLIB')
os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')

app = Flask(__name__)

past_values0 = []
past_values1 = []
past_values_ref = []

message = 'TEAM1FTW'
current_value = 0
value0 = 0
value1 = 0
value_ref = 0

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
    global current_value, value0, value1, value_ref, past_values0, past_values1

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
                adc, timestamp, value = sample.split(',',2)
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

        #print(string_format_voltages(voltages0))
        #print(string_format_voltages(voltages1))

        #index_max0 = index_of_max(values0)
        #index_max1 = index_of_max(values1)
        #index_max2 = index_of_max(values_ref)


        #print(str(voltages[index_max]) + 'V', str(timestamps[index_max]) + 'us')
        past_values0.append(sum(adjusted_values0)/len(adjusted_values0))
        past_values1.append(sum(adjusted_values1)/len(adjusted_values1))
        past_values_ref.append(reference_value)

        if(len(past_values0) > 10):
            del past_values0[0]
        if(len(past_values1) > 10):
            del past_values1[0]
        if(len(past_values_ref) > 10):
            del past_values_ref[0]

        value0 = sum(past_values0)/len(past_values0)
        value1 = sum(past_values1)/len(past_values1)
        value_ref = sum(past_values_ref)/len(past_values_ref)

        #print('0',past_values0)
        #print('1',past_values1)
        #print('2',past_values_ref)

        k = 3.78125 #in
        #s1 value 0, s2 value1, ref value3
        ratio = to_voltage(value0)/to_voltage(value1)
        #print('v0',value0)
        #print('v1',value1)
        d1 = k/ (ratio - 1)
        current_value = d1
    #elif line != '': 
    #    print(line)

def process_queue(queue):
     while True:
            try:
                line = queue.get_nowait()
            except Empty:
                continue
            else:
                process_line(line)

#frequencies 
#Locating 8.19
#Tracking 12.04
#Tracking 29.43
class Mode(Enum):
        LOCATING = ' Locating 8.19Khz'
        TRACKING12 = 'Tracking 12.04Khz'
        TRACKING29 = 'Tracking 29.43Khz'

def main():
    global current_value, value0, value1, value_ref, message

    #button update requests
    update_mode_request = True
    current_mode = Mode.LOCATING

    update_calibration_distance_request = True
    calibration_distance = 120 #distance in inches

    update_calibration_value_request = True
    calibration_value = 1

    update_gain_request = True
    gain_value = 10

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
            current_mode_rect = display_text(screen, current_mode.value, BLACK , BACKGROUND_COLOR, (300,10), 180, textFont)
            rects.append(current_mode_rect)
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
                calibration_string = 'Calibration Value = {}'.format(calibration_value)
            text_surface = buttonFont.render(calibration_string, False, BLACK)
            calibration_value_rect = pygame.Rect((150,15), (140,20))
            screen.fill(BACKGROUND_COLOR, calibration_value_rect)
            screen.blit(text_surface,(150,15))
            rects.append(calibration_value_rect)
            update_calibration_distance = False

        if update_gain_request:
            text_surface = textFont.render(str(gain_value), False, BLACK)
            gain_rect = pygame.Rect((77,280), (30,20))
            screen.fill(BACKGROUND_COLOR, gain_rect)
            screen.blit(text_surface,(77,280))
            rects.append(gain_rect)
            update_calibration_distance = False
        
        depth_rect = display_text(screen, "{:.2f}ft".format(current_value), BLACK , BACKGROUND_COLOR, (20,90), 100, numberFont)
        message_rect = display_text(screen, message, BLACK , BACKGROUND_COLOR, (20,170), 200, textFont)
        value0_rect = display_text(screen, "{:.2f}V".format(to_voltage(value0)), BLACK , BACKGROUND_COLOR, (380,85), 100, numberFont)
        value1_rect = display_text(screen, "{:.2f}V".format(to_voltage(value1)), BLACK , BACKGROUND_COLOR, (380,125), 100, numberFont)
        ref_rect = display_text(screen, "{:.2f}V".format(to_voltage(value_ref)), BLACK , BACKGROUND_COLOR, (380,165), 100, numberFont)
        rects += [depth_rect, value0_rect, value1_rect, ref_rect]

        pygame.display.update(rects)
            
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONUP:
                print('Click')
                pos = pygame.mouse.get_pos()
                if locating8_button.collidepoint(pos):
                    current_mode = Mode.LOCATING
                    update_mode_request = True
                elif tracking12_button.collidepoint(pos):
                    current_mode = Mode.TRACKING12
                    update_mode_request = True   
                elif tracking29_button.collidepoint(pos):
                    current_mode = Mode.TRACKING29
                    update_mode_request = True 
                elif calibration_button.collidepoint(pos):
                    calibration_value = calibration_distance
                    update_calibration_value_request
                elif minus_gain_button.collidepoint(pos):
                    if gain_value > 0:
                        gain_value -= 1
                        update_gain_request = True
                elif plus_gain_button.collidepoint(pos):
                    gain_value += 1
                    update_gain_request = True  
                elif minus_calibration_button.collidepoint(pos):
                    if calibration_distance > 0:
                        calibration_distance -= 1
                        update_calibration_distance_request = True
                elif plus_calibration_button.collidepoint(pos):
                    calibration_distance += 1
                    update_calibration_distance_request = True        
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
    close_pipe()
    p = open_pipe(80,10,30)
    q = Queue()
    t1 = Thread(target=enqueue_output, args=(p,q))
    t1.daemon = True
    t1.start()

    t2 = Thread(target=process_queue, args=(q,))
    t2.daemon = True
    t2.start()

    main()

    