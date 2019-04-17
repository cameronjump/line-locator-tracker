import pygame
from pygame.locals import *
import os
import sys
from enum import Enum

'''os.putenv('SDL_FBDEV', '/dev/fb1')
os.putenv('SDL_VIDEODRIVER', 'fbcon')
os.putenv('SDL_MOUSEDRV', 'TSLIB')
os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')'''

#frequencies 
#Locating 8.19
#Tracking 12.04
#Tracking 29.43
class Mode(Enum):
        LOCATING = ' Locating 8.19Khz'
        TRACKING12 = 'Tracking 12.04Khz'
        TRACKING29 = 'Tracking 29.43Khz'

def display_text(screen, text, fontColor, backgroundColor, location, font): #returns rect
    text_surface = font.render(text, False, fontColor)
    text_rect = text_surface.get_rect(topleft = location)
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

def main():

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
    buttonFont = pygame.font.SysFont('default', 14)
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
    tracking12_button = create_button(screen, 'Tracking 12.04Khz', WHITE, ORANGE, (177, 210), (140,40), buttonFont)
    tracking29_button = create_button(screen, 'Tracking 29.43Khz', WHITE, ORANGE, (177, 260), (140,40), buttonFont)

    #gain
    textsurface = buttonFont.render('Gain', False, BLACK)
    screen.blit(textsurface,(77,265))
    minus_gain_button = create_button(screen, '-', WHITE, ORANGE, (20, 260), (40,40), numberFont)
    plus_gain_button = create_button(screen, '+', WHITE, ORANGE, (120, 260), (40,40), numberFont)

    #calibration
    calibration_button = create_button(screen, 'Calibrate', WHITE, ORANGE, (334, 210), (140,40), buttonFont)
    textsurface = buttonFont.render('Distance', False, BLACK)
    screen.blit(textsurface,(383,265))
    minus_calibration_button = create_button(screen, '-', WHITE, ORANGE, (334, 260), (40,40), numberFont)
    plus_calibration_button = create_button(screen, '+', WHITE, ORANGE, (434, 260), (40,40), numberFont)

    pygame.display.update()

    increment = 0

    while True:

        rects = []

        if update_mode_request:
            print(current_mode.value)
            current_mode_rect = display_text(screen, current_mode.value, BLACK , BACKGROUND_COLOR, (300,10), textFont)
            rects.append(current_mode_rect)
            update_mode_request = False

        if update_calibration_distance_request:
            calibration_string = '{}in'.format(calibration_distance)
            calibration_rect = display_text(screen, calibration_string, BLACK , BACKGROUND_COLOR, (377,280), textFont)
            rects.append(calibration_rect)
            update_calibration_distance = False

        if update_calibration_value_request:
            if calibration_value == 1:
                calibration_string = 'Calibration Value = UNSET'
            else:
                calibration_string = 'Calibration Value = {}'.format(calibration_value)
            calibration_value_rect = display_text(screen, calibration_string, BLACK , BACKGROUND_COLOR, (150,15), buttonFont)
            rects.append(calibration_value_rect)
            update_calibration_distance = False

        if update_gain_request:
            gain_rect = display_text(screen, str(gain_value), BLACK , BACKGROUND_COLOR, (77,280), textFont)
            rects.append(gain_rect)
            update_calibration_distance = False



        
        depth_rect = display_text(screen, str(increment), BLACK , BACKGROUND_COLOR, (20,90), numberFont)
        value0_rect = display_text(screen, str(increment), BLACK , BACKGROUND_COLOR, (380,85), numberFont)
        value1_rect = display_text(screen, str(increment), BLACK , BACKGROUND_COLOR, (380,125), numberFont)
        ref_rect = display_text(screen, str(increment), BLACK , BACKGROUND_COLOR, (380,165), numberFont)
        rects += [depth_rect, value0_rect, value1_rect, ref_rect]

        pygame.display.update(rects)
            
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONUP:
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
                    print('Calibration')
                elif minus_gain_button.collidepoint(pos):
                    print('Decrease Gain')
                elif plus_gain_button.collidepoint(pos):
                    print('Increase Gain')   
                elif minus_calibration_button.collidepoint(pos):
                    calibration_distance -= 1
                    update_calibration_distance = True
                elif plus_calibration_button.collidepoint(pos):
                    calibration_distance += 1
                    update_calibration_distance = True        
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

main()
        