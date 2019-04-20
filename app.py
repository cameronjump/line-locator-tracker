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

os.putenv('SDL_FBDEV', '/dev/fb1')
os.putenv('SDL_VIDEODRIVER', 'fbcon')
os.putenv('SDL_MOUSEDRV', 'TSLIB')
os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')

app = Flask(__name__)

past_values0 = []
past_values1 = []
past_values2 = []

current_value = 0
value0 = 0
value1 = 0
value2 = 0

def enqueue_output(process, queue):
    while process.poll() is None:
        for line in iter(process.stdout.readline, ""):
            line = line.decode('UTF-8').replace('\n', '')
            queue.put(line)
    process.close()

def open_pipe(micros_between_readings, samples, sample_set_frequency):
    try:
        path = '/home/pi/underground-locator/read_adc_daemon'
        print(path)
        command = 'sudo {} {} {} {}'.format(path, micros_between_readings, samples, sample_set_frequency)
        print(command)

        process = Popen(command, stdout=PIPE, stderr=STDOUT, shell=True)
        return process
    except Exception as e:
        close_pipe()
        print(e)
        sys.exit(1)

def close_pipe():
    call('sudo killall read_adc_daemon', shell=True)

def read_adc_pipe(micros_between_readings, samples):
    process = open_pipe(micros_between_readings, samples)

    while process.poll() is None:
        for line in iter(process.stdout.readline, ""):
            line = line.decode('UTF-8').replace('\n', '')
            process_line(line)

def process_line(line):
    global current_value, value0, value1, value2, past_values0, past_values1, past_values2

    if line[0:2] == 'DS':
        timestamps0 = []
        values0 = []
        timestamps1 = []
        values1 = []
        timestamps2 = []
        values2 = []

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
                    values2.append(int(value))
            except:
                continue
        
        if len(values0)  == 0 or len(values1) == 0 or len(values2) == 0:
            return

        #delete first value
        del values0[0]
        del timestamps0[0]
        del values1[0]
        del timestamps1[0]
        del values2[0]
        del timestamps2[0]

        #adjusted_timestamps = adjust_timestamps(timestamps0)
        voltages0 = list_to_voltage(values0)
        voltages1 = list_to_voltage(values1)
        reference_value = sum(values2)/len(values2)

        adjusted_values0 = list(map(lambda x: x-reference_value, values0))
        adjusted_values1 = list(map(lambda x: x-reference_value, values1))
        adjusted_values0 = list(map(abs, adjusted_values0))
        adjusted_values1 = list(map(abs, adjusted_values1))

        #print(string_format_voltages(voltages0))
        #print(string_format_voltages(voltages1))

        #index_max0 = index_of_max(values0)
        #index_max1 = index_of_max(values1)
        #index_max2 = index_of_max(values2)


        #print(str(voltages[index_max]) + 'V', str(timestamps[index_max]) + 'us')
        past_values0.append(sum(adjusted_values0)/len(adjusted_values0))
        past_values1.append(sum(adjusted_values1)/len(adjusted_values1))
        past_values2.append(reference_value)

        if(len(past_values0) > 10):
            del past_values0[0]
        if(len(past_values1) > 10):
            del past_values1[0]
        if(len(past_values2) > 10):
            del past_values2[0]

        value0 = sum(past_values0)/len(past_values0)
        value1 = sum(past_values1)/len(past_values1)
        value2 = sum(past_values2)/len(past_values2)

        #print('0',past_values0)
        #print('1',past_values1)
        #print('2',past_values2)

        k = 3.78125 #in
        #s1 value 0, s2 value1, ref value3
        ratio = to_voltage(value0)/to_voltage(value1)
        #print('v0',value0)
        #print('v1',value1)
        d1 = k/ (ratio - 1)
        current_value = d1
    #elif line != '': 
    #    print(line)

def to_voltage(x):
    ADCRESOLUTION = 4095
    SYSTEMVOLTAGE = 5
    return (x/ADCRESOLUTION)*SYSTEMVOLTAGE

def list_to_voltage(values):
    return list(map(to_voltage, values))

def adjust_timestamps(timestamps):
    return list(map(lambda x: x-timestamps[0], timestamps))

def index_of_max(values):
    return max(range(len(values)), key=values.__getitem__)

def string_format_voltages(voltages):
    return ["%.3f" % voltage for voltage in voltages]

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
    global current_value, value0, value1, value2
    mode = 'Locating'
    value = ("%.3f" % float(current_value/12))
    unit = 'ft'
    extra = ''
    extra += 'Value 0    ' + str(int(value0)) +'    ' + ("%.3f" % to_voltage(value0))+'V\n'
    extra += 'Value 1    ' + str(int(value1)) +'    ' + ("%.3f" % to_voltage(value1))+'V\n'
    extra += 'Reference Value    ' + str(int(value2)) +'    ' + ("%.3f" % to_voltage(value2))+'V\n'    
    return jsonify(mode=mode, value=value, unit=unit, extra=extra)

def display_text(screen, text, fontColor, backgroundColor, location, font): #returns rect
    voltage_surface = font.render(text, False, fontColor)
    voltage_rect = voltage_surface.get_rect(topleft = location)
    screen.fill(backgroundColor, voltage_rect)
    screen.blit(voltage_surface,voltage_rect.topleft)
    return voltage_rect

def gui():
    global current_value, value0, value1, value2

    #colors
    BACKGROUND_COLOR = (255, 255, 255)
    BLACK = (0,0,0)
    ORANGE = (255, 61, 0)

    #setup font
    pygame.font.init()
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
    screen.blit(textsurface,(20,80))
    textsurface = textFont.render('Magnitudes', False, ORANGE)
    screen.blit(textsurface,(220,80))
    textsurface = textFont.render('Value 0', False, BLACK)
    screen.blit(textsurface,(220,120))
    textsurface = textFont.render('Value 1', False, BLACK)
    screen.blit(textsurface,(220,160))
    textsurface = textFont.render('Reference', False, BLACK)
    screen.blit(textsurface,(220,200))
    screen.fill(BLACK, Rect((0,35),(480, 5)))

    pygame.display.update()

    while True:
        
        depth_rect = display_text(screen, "{:.2f}ft".format(current_value), BLACK , BACKGROUND_COLOR, (20,120), numberFont)
        value0_rect = display_text(screen, "{:.2f}V".format(to_voltage(value0)) , BLACK , BACKGROUND_COLOR, (340,115), numberFont)
        value1_rect = display_text(screen, "{:.2f}V".format(to_voltage(value1)), BLACK , BACKGROUND_COLOR, (340,155), numberFont)
        ref_rect = display_text(screen, "{:.2f}V".format(to_voltage(value2)), BLACK , BACKGROUND_COLOR, (340,195), numberFont)
        rects = [depth_rect, value0_rect, value1_rect, ref_rect]

        pygame.display.update(rects)
            
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.display.quit()
                pygame.quit()  # Hangs here
                sys.exit()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.display.quit()
                    pygame.quit()  # Hangs here
                    sys.exit()          
        clock.tick(10)

def main():
    close_pipe()
    p = open_pipe(80,10,30)
    q = Queue()
    t1 = Thread(target=enqueue_output, args=(p,q))
    t1.daemon = True
    t1.start()

    t2 = Thread(target=process_queue, args=(q,))
    t2.daemon = True
    t2.start()


if __name__== '__main__':
    main()
    #app.run("0.0.0.0")

    gui()

    