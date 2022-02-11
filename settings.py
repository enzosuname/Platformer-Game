import pygame as pg
# from sprites import SpriteSheet

# Constants
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (242, 235, 31)
GREEN = (31, 242, 137)
RED = (255, 0, 0)
SKY = (9, 175, 236)

FPS = 60

WIN_WIDTH = 825
WIN_HEIGHT = 825
TILE_SIZE = 75

# A

width = 20
height = 27
player_x = 5
player_y = 69
player_x_pad = 12
player_y_pad = 0

LAYOUT = [
    '0,0,0,0,0,0,0,0,0,0,0',
    '0,0,0,0,0,0,0,0,0,0,0',
    '0,0,0,0,0,0,0,0,0,0,0',
    '0,0,0,0,0,0,0,0,0,0,0',
    '0,0,0,0,0,0,0,0,0,0,0',
    '4,5,r,0,0,0,0,0,0,0,0',
    '-,-,m,0,0,0,0,0,0,0,0',
    '-,-,m,0,0,0,0,0,p,0,0',
    '-,-,m,0,0,0,0,l,5,5,6',
    '1,2,2,R,0,A,0,n,-,-,-',
    '-,-,-,M,0,I,0,n,-,-,-',
]
