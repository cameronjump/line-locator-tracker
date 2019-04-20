import pygame
from pygame.locals import *

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