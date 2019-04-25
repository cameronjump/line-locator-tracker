import sys
import time
import os
from enum import Enum

import pygame
from pygame.locals import *

import requests

os.putenv('SDL_FBDEV', '/dev/fb1')
os.putenv('SDL_VIDEODRIVER', 'fbcon')
os.putenv('SDL_MOUSEDRV', 'TSLIB')
os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')


message = 'TEAM1FTW'
current_value = 0
value0 = 0
value1 = 0
value_ref = 0
current_mode = ' Locating 8.19Khz'

url = 'http://10.0.0.1:5000'

calibration_distance = 120 #distance in inches
calibration_value = 1
gain_value = 1

def display_text(screen, text, fontColor, backgroundColor, location, width, font): #returns rect
    text_surface = font.render(text, False, fontColor)
    text_rect = pygame.Rect(location, (width, 25))
    screen.fill(backgroundColor, text_rect)
    screen.blit(text_surface,text_rect.topleft)
    return text_rect

def create_button(screen, text, fontColor, buttonColor, location, size, font):
    button_rect = pygame.Rect(location, size)
    text_surface = font.render(text, False, fontColor)
    text_rect = text_surface.get_rect(center = button_rect.center)
    screen.fill(buttonColor, button_rect)
    screen.blit(text_surface, text_rect)
    return button_rect    

def to_voltage(x):
    ADCRESOLUTION = 4095
    SYSTEMVOLTAGE = 5
    return (x/ADCRESOLUTION)*SYSTEMVOLTAGE

def main():
    global current_value, value0, value1, value_ref, message, current_mode, calibration_distance, calibration_value, gain_value, url

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

        current_mode_rect = display_text(screen, current_mode, BLACK , BACKGROUND_COLOR, (300,10), 180, textFont)
        rects.append(current_mode_rect)


        calibration_string = '{}in'.format(calibration_distance)
        calibration_rect = pygame.Rect((357,280), (57,20))
        text_surface = textFont.render(calibration_string, False, BLACK)
        screen.fill(BACKGROUND_COLOR, calibration_rect)
        screen.blit(text_surface,(357,280))
        rects.append(calibration_rect)

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

        text_surface = textFont.render(str(gain_value), False, BLACK)
        gain_rect = pygame.Rect((65,280), (50,20))
        screen.fill(BACKGROUND_COLOR, gain_rect)
        screen.blit(text_surface,(77,280))
        rects.append(gain_rect)
        
        depth_rect = display_text(screen, "{:.2f}ft".format(current_value), BLACK , BACKGROUND_COLOR, (20,90), 100, numberFont)
        message_rect = display_text(screen, message, BLACK , BACKGROUND_COLOR, (20,170), 200, textFont)
        value0_rect = display_text(screen, "{:.2f}V".format(to_voltage(value0)), BLACK , BACKGROUND_COLOR, (380,85), 100, numberFont)
        value1_rect = display_text(screen, "{:.2f}V".format(to_voltage(value1)), BLACK , BACKGROUND_COLOR, (380,125), 100, numberFont)
        ref_rect = display_text(screen, "{:.2f}V".format(to_voltage(value_ref)), BLACK , BACKGROUND_COLOR, (380,165), 100, numberFont)
        rects += [depth_rect, value0_rect, value1_rect, ref_rect, message_rect]

        pygame.display.update(rects)
            
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONUP:
                print('Click')
                pos = pygame.mouse.get_pos()
                if locating8_button.collidepoint(pos):
                    requests.post('{}/locating'.format(url))
                elif tracking12_button.collidepoint(pos):
                    requests.post('{}/tracking12'.format(url))
                elif tracking29_button.collidepoint(pos):
                    requests.post('{}/tracking29'.format(url))
                elif calibration_button.collidepoint(pos):
                    requests.post('{}/calibrate'.format(url))
                elif minus_gain_button.collidepoint(pos):
                    requests.post('{}/minusgain'.format(url))
                elif plus_gain_button.collidepoint(pos):
                    requests.post('{}/plusgain'.format(url))
                elif minus_calibration_button.collidepoint(pos):
                    requests.post('{}/minuscalibration'.format(url))
                elif plus_calibration_button.collidepoint(pos):
                    requests.post('{}/pluscalibration'.format(url))    
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
        try :
            r = requests.get('{}/api'.format(url))
            l = r.text
            values = l.split(',')
            current_mode = values[0]
            current_value = float(values[1])
            value0 = float(values[2])
            value1 = float(values[3])
            value_ref = float(values[4])
            message = values[5]
            gain_value = values[6]
            calibration_distance = values[7]
            calibration_value = values[8]

        except:
            print('Connection error')
        clock.tick(4)

if __name__== '__main__':

    try:
        main()
    finally:
        print('Goodnight')

    