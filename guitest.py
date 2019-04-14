import pygame
from pygame.locals import *
import os
import sys

os.putenv('SDL_FBDEV', '/dev/fb1')

def display_text(screen, text, fontColor, backgroundColor, location, font): #returns rect
    voltage_surface = font.render(text, False, fontColor)
    voltage_rect = voltage_surface.get_rect(topleft = location)
    screen.fill(backgroundColor, voltage_rect)
    screen.blit(voltage_surface,voltage_rect.topleft)
    return voltage_rect

def gui():
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
    screen.blit(textsurface,(260,80))
    textsurface = textFont.render('Value 0', False, BLACK)
    screen.blit(textsurface,(260,120))
    textsurface = textFont.render('Value 1', False, BLACK)
    screen.blit(textsurface,(260,160))
    textsurface = textFont.render('Reference', False, BLACK)
    screen.blit(textsurface,(260,200))
    screen.fill(BLACK, Rect((0,35),(480, 5)))

    pygame.display.update()

    increment = 0

    while True:
        
        depth_rect = display_text(screen, str(increment), BLACK , BACKGROUND_COLOR, (20,120), numberFont)
        value0_rect = display_text(screen, str(increment), BLACK , BACKGROUND_COLOR, (380,115), numberFont)
        value1_rect = display_text(screen, str(increment), BLACK , BACKGROUND_COLOR, (380,155), numberFont)
        ref_rect = display_text(screen, str(increment), BLACK , BACKGROUND_COLOR, (380,195), numberFont)
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
        increment += 1
        clock.tick(10)

gui()
        