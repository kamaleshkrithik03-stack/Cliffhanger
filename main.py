import os
import pygame
import math
import random #these imports are in the back of my hand rn im so use to it
import sys

pygame.init()
WIDTH = 1000 # for now  i might chage to make it full screen
HEIGHT = 800 #not gonna do a config.py too lazy
screen = pygame.display.set_mode(WIDTH, HEIGHT)
pygame.display.set_caption("Cliffhanger is the name i could come up with")
clock = pygame.time.Clock()
FONT_BIG = pygame.font.SysFont("arial", 42, bold=True) #im sticking to arial(maybe times new roman) as im not experimenting with orbitron and all that shi
FONT_MED = pygame.font.SysFont("arial", 25, bold=True) #maybe idk ill see
FONT_SMALL = pygame.font.SysFont("arial", 18) #not bold

LEVELS = [
    {"level": 1, "time": 10, "gravity": 500, "max_safe_vy": 420}, # ok so basically what ive done here is my idea is that the char/sprite will be floating in air in a cliff and as levels goes up u can see the time(most hardest) decreases
    {"level": 2, "time": 8, "gravity": 650, "max_safe_vy": 380}, # copy pasted from last line 
    {"level": 3, "time": 5, "gravity": 750, "max_safe_vy": 340},
]
GROUND_Y = HEIGHT - 60
DROP_START_X = 340 #ugghh ofc i have to use pycase not snakecase its of i have to have caps lock on evry timr
DROP_START_Y = 150

def load_transparent_asset(filename, size, fallback_color):
    if os.path.exists(filename):
        img = pygame.image.load(filename).convert_alpha()
        return pygame.transform.smoothscale(img, size)
    

