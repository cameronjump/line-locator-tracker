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

def get_index_and_max(values):
    return max(range(len(values)), key=values.__getitem__) , max(values)

def inPhase(basetime, timestamp, lowbound, highbound, mod):
    check  = (timestamp-basetime)%mod
    if check > highbound or check < lowbound:
        return 0 #phase 0
    else:
        return 1 #phase 1

def phase_array_to_dpsk_string(phase_array):
    dpskstring = ''
    for i in range(0, len(phase_array)):
        if i< len(phase_array)-1:
            if (phase_array[i] != phase_array[i+1]):
                dpskstring += '1'
            else:
                dpskstring += '0'
    return dpskstring

def retrieve_message(dpskstring, startindex):
    if len(dpskstring)-52 < startindex:
        return False
    bits = dpskstring[startindex:startindex+53]
    message = ''
    for i in range(0,13):
        byte = bits[(i*4):(i*4)+4]
        hexed = hex(int(byte,2))
        formatted = hexed[2]
        message += formatted
    #add the last bit
    message += hex(int(str(bits[52])+'000',2))[2]
    return bits, message
