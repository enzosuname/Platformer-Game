# This class handles sprite sheets
# https://www.pygame.org/wiki/Spritesheet
# I've added some code to fail if the file wasn't found..
# Note: When calling images_at the rect is the format:
# (x, y, x + offset, y + offset)

from settings import *

import pygame


class SpriteSheet:

    def __init__(self, filename):
        """Load the sheet."""
        try:
            self.sheet = pygame.image.load(filename).convert()
        except pygame.error as e:
            print(f"Unable to load spritesheet image: {filename}")
            raise SystemExit(e)

    def image_at(self, rectangle, colorkey=None):
        """Load a specific image from a specific rectangle."""
        """rectangle is a tuple with (x, y, x+offset, y+offset)"""
        rect = pygame.Rect(rectangle)
        image = pygame.Surface(rect.size).convert()
        image.blit(self.sheet, (0, 0), rect)
        if colorkey is not None:
            if colorkey is -1:
                colorkey = image.get_at((0, 0))
            image.set_colorkey(colorkey, pygame.RLEACCEL)
        return image

    def images_at(self, rects, colorkey=None):
        """Load a whole bunch of images and return them as a list."""
        return [self.image_at(rect, colorkey) for rect in rects]

    def load_strip(self, rect, image_count, colorkey=None):
        """Load a whole strip of images, and return them as a list."""
        tups = [(rect[0] + rect[2] * x, rect[1], rect[2], rect[3])
                for x in range(image_count)]
        return self.images_at(tups, colorkey)

    def load_grid_images(self, num_rows, num_cols, x_margin=0, x_padding=0,
                         y_margin=0, y_padding=0, width=None, height=None, colorkey=None):
        """Load a grid of images.
        x_margin is the space between the top of the sheet and top of the first
        row. x_padding is space between rows. Assumes symmetrical padding on
        left and right.  Same reasoning for y. Calls self.images_at() to get a
        list of images.
        """

        sheet_rect = self.sheet.get_rect()
        sheet_width, sheet_height = sheet_rect.size

        # To calculate the size of each sprite, subtract the two margins,
        #   and the padding between each row, then divide by num_cols.
        # Same reasoning for y.

        if width and height:
            x_sprite_size = width
            y_sprite_size = height
        else:
            x_sprite_size = (sheet_width - 2 * x_margin
                             - (num_cols - 1) * x_padding) / num_cols
            y_sprite_size = (sheet_height - 2 * y_margin
                             - (num_rows - 1) * y_padding) / num_rows

        sprite_rects = []
        for row_num in range(num_rows):
            for col_num in range(num_cols):
                # Position of sprite rect is margin + one sprite size
                #   and one padding size for each row. Same for y.
                x = x_margin + col_num * (x_sprite_size + x_padding)
                y = y_margin + row_num * (y_sprite_size + y_padding)
                sprite_rect = (x, y, x_sprite_size, y_sprite_size)
                sprite_rects.append(sprite_rect)

        return self.images_at(sprite_rects, colorkey)

class Player(pygame.sprite.Sprite):

    def __init__(self, image_path, tilelist, level):
        pygame.sprite.Sprite.__init__(self)

        self.run_rt_list = image_path
        self.run_lft_list = [pg.transform.flip(characters, True, False) for characters in image_path]
        self.image = self.run_rt_list[0]
        self.rect = self.image.get_rect()
        self.rect.x = self.rect.width + 250
        self.rect.y = WIN_HEIGHT - 300  # - 75*2 - 26
        self.next = level

        self.tile_list = tilelist

        self.prev_update = pygame.time.get_ticks()
        self.frame = 0
        self.framerate = 100

        self.prev_update_jump = pygame.time.get_ticks()
        self.time = 1000

        self.change_x = 0
        self.jumping = False
        self.falling = False
        self.change_y = 1
        self.counter = 0
        self.change_counter = 0

    def update(self):
        self.rect.x += self.change_x
        self.rect.y += self.change_y

        if not self.jumping:
            self.change_y = 3.5
            self.falling = True

        now = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RIGHT]:
            if self.rect.x <= WIN_WIDTH:
                self.change_x = 2

                if now - self.prev_update > self.framerate:
                    self.prev_update = now
                    self.frame += 1
                    self.image = self.run_rt_list[self.frame]
                if self.frame == 4:
                    self.frame = 0


        elif keys[pygame.K_LEFT]:
            if self.rect.x >= 0:
                self.change_x = -2

                if now - self.prev_update > self.framerate:
                    self.prev_update = now
                    self.frame += 1
                    self.image = self.run_lft_list[self.frame]
                if self.frame == 4:
                    self.frame = 0

        else:
            self.change_x = 0

        for tile in self.tile_list:
            # see if any tile rect collides with player rect in horiz direction, notice the addition of dx to rect.x
            if tile[1].colliderect(self.rect.x + self.change_x,
                                   self.rect.y,
                                   self.rect.width,
                                   self.rect.height):
                self.change_x = 0

            # see if any tile rect collides with player rect in vert direction, notice the addition of dy to rect.y
            if tile[1].colliderect(self.rect.x,
                                   self.rect.y + self.change_y,
                                   self.rect.width,
                                   self.rect.height):

                # collision b/w bottom of platform and top of player
                if self.change_y < 0:
                    # allow the player to move up closer and closer to platform
                    self.change_y = tile[1].bottom - self.rect.top

                # collision b/w top of platform and bottom of player
                elif self.change_y > 0:
                    # allow the player to move down closer and closer to platform
                    self.change_y = tile[1].top - self.rect.bottom
                    self.change_y = 0
                    self.jumping = False
                    self.falling = False

        if keys[pygame.K_SPACE] and not self.jumping and not self.falling:
            self.jumping = True
            if self.next != 2:
                JUMP_SOUND.play()
            self.change_y = -3
            self.change_counter = 1.5

        self.counter += self.change_counter
        if self.counter > 50:
            self.jumping = False
            self.change_y = 1
            self.counter = 0
            self.change_counter = 0

class Enemy(pygame.sprite.Sprite):
    def __init__(self, image_path, tile_list):
        pygame.sprite.Sprite.__init__(self)

        self.run_rt_list = image_path
        self.run_lft_list = [pg.transform.flip(characters, True, False) for characters in image_path]
        self.image = self.run_rt_list[0]
        self.rect = self.image.get_rect()
        self.rect.x = self.rect.width + 250
        self.rect.y = WIN_HEIGHT - 300  # - 75*2 - 26

        self.tile_list = tile_list

        self.prev_update = pygame.time.get_ticks()
        self.frame = 0
        self.framerate = 100

        self.change_x = 0
        self.change_y = 1
        self.falling = True
        self.jumping = False

    def update(self):
        self.rect.x += self.change_x
        self.rect.y += self.change_y

        if not self.jumping:
            self.change_y = 3.5
            self.falling = True

        now = pygame.time.get_ticks()

        self.change_x = -.5
        if now - self.prev_update > self.framerate:
            self.prev_update = now
            self.frame += 1
            self.image = self.run_lft_list[self.frame]
        if self.frame == 3:
            self.frame = 0

        if self.rect.x <= 0 or self.rect.x >= WIN_WIDTH:
            self.change_x = 0

        for tile in self.tile_list:
            # see if any tile rect collides with player rect in horiz direction, notice the addition of dx to rect.x
            if tile[1].colliderect(self.rect.x + self.change_x,
                                   self.rect.y,
                                   self.rect.width,
                                   self.rect.height):
                self.change_x = 0

            # see if any tile rect collides with player rect in vert direction, notice the addition of dy to rect.y
            if tile[1].colliderect(self.rect.x,
                                   self.rect.y + self.change_y,
                                   self.rect.width,
                                   self.rect.height):

                # collision b/w bottom of platform and top of player
                if self.change_y < 0:
                    # allow the player to move up closer and closer to platform
                    self.change_y = tile[1].bottom - self.rect.top

                # collision b/w top of platform and bottom of player
                elif self.change_y > 0:
                    # allow the player to move down closer and closer to platform
                    self.change_y = tile[1].top - self.rect.bottom
                    self.change_y = 0
                    self.jumping = False
                    self.falling = False

        if self.rect.y > WIN_HEIGHT + 75 or self.rect.x < 0:
            self.kill()

class Layout:
    def __init__(self, level_layout, tile_size, level):
        self.tile_list = []
        self.back_list = []
        self.end_list = []
        self.player_group = pygame.sprite.Group()
        self.enemy_group = pygame.sprite.Group()
        self.change_x = 0
        self.player = None
        self.next = level

        characters = SpriteSheet("images/characters.png")
        run_rt_list = characters.load_grid_images(1, 23, player_x, player_x_pad, player_y, player_y_pad, width, height,
                                                  -1)
        run_enemy_list = characters.load_grid_images(1, 23, player_x, player_x_pad, 101, player_y_pad, width, height,
                                                  -1)

        tile_sheet = SpriteSheet("images/sheet.png")
        rock_green1 = tile_sheet.image_at((112, 0, 16, 16), (255, 255, 255))
        rock_green1 = pg.transform.scale(rock_green1, (tile_size, tile_size))
        rock_green2 = tile_sheet.image_at((112 + 16, 0, 16, 16), (255, 255, 255))
        rock_green2 = pg.transform.scale(rock_green2, (tile_size, tile_size))
        rock_green3 = tile_sheet.image_at((112 + 16 * 2, 0, 16, 16), (255, 255, 255))
        rock_green3 = pg.transform.scale(rock_green3, (tile_size, tile_size))
        rock_green_left = tile_sheet.image_at((112 + 16, 16, 16, 16), (255, 255, 255))
        rock_green_left = pg.transform.scale(rock_green_left, (tile_size, tile_size))
        rock_green_right = tile_sheet.image_at((112 + 16 * 2, 16, 16, 16), (255, 255, 255))
        rock_green_right = pg.transform.scale(rock_green_right, (tile_size, tile_size))
        grey_rock_green1 = tile_sheet.image_at((112, 16 * 2, 16, 16), (255, 255, 255))
        grey_rock_green1 = pg.transform.scale(grey_rock_green1, (tile_size, tile_size))
        grey_rock_green2 = tile_sheet.image_at((112 + 16, 16 * 2, 16, 16), (255, 255, 255))
        grey_rock_green2 = pg.transform.scale(grey_rock_green2, (tile_size, tile_size))
        grey_rock_green3 = tile_sheet.image_at((112 + 16 * 2, 16 * 2, 16, 16), (255, 255, 255))
        grey_rock_green3 = pg.transform.scale(grey_rock_green3, (tile_size, tile_size))
        grey_rock_green_left = tile_sheet.image_at((112 + 16, 16 * 3, 16, 16), (255, 255, 255))
        grey_rock_green_left = pg.transform.scale(grey_rock_green_left, (tile_size, tile_size))
        grey_rock_green_right = tile_sheet.image_at((112 + 16 * 2, 16 * 3, 16, 16), (255, 255, 255))
        grey_rock_green_right = pg.transform.scale(grey_rock_green_right, (tile_size, tile_size))
        rocky = tile_sheet.image_at((112, 16, 16, 16), (255, 255, 255))
        rocky = pg.transform.scale(rocky, (tile_size, tile_size))
        grey_rocky = tile_sheet.image_at((112, 16 * 3, 16, 16), (255, 255, 255))
        grey_rocky = pg.transform.scale(grey_rocky, (tile_size, tile_size))
        rock_lwall = tile_sheet.image_at((112 + 16 * 3, 16, 16, 16), (255, 255, 255))
        rock_lwall = pg.transform.scale(rock_lwall, (tile_size, tile_size))
        rock_rwall = tile_sheet.image_at((112 + 16 * 5, 16, 16, 16), (255, 255, 255))
        rock_rwall = pg.transform.scale(rock_rwall, (tile_size, tile_size))
        rock_left = tile_sheet.image_at((112 + 16 * 3, 0, 16, 16), (255, 255, 255))
        rock_left = pg.transform.scale(rock_left, (tile_size, tile_size))
        rock_right = tile_sheet.image_at((112 + 16 * 5, 0, 16, 16), (255, 255, 255))
        rock_right = pg.transform.scale(rock_right, (tile_size, tile_size))
        rock_floor = tile_sheet.image_at((112 + 16 * 4, 0, 16, 16), (255, 255, 255))
        rock_floor = pg.transform.scale(rock_floor, (tile_size, tile_size))
        grey_rock_lwall = tile_sheet.image_at((112 + 16 * 3, 16 * 3, 16, 16), (255, 255, 255))
        grey_rock_lwall = pg.transform.scale(grey_rock_lwall, (tile_size, tile_size))
        grey_rock_rwall = tile_sheet.image_at((112 + 16 * 5, 16 * 3, 16, 16), (255, 255, 255))
        grey_rock_rwall = pg.transform.scale(grey_rock_rwall, (tile_size, tile_size))
        grey_rock_left = tile_sheet.image_at((112 + 16 * 3, 16 * 2, 16, 16), (255, 255, 255))
        grey_rock_left = pg.transform.scale(grey_rock_left, (tile_size, tile_size))
        grey_rock_right = tile_sheet.image_at((112 + 16 * 5, 16 * 2, 16, 16), (255, 255, 255))
        grey_rock_right = pg.transform.scale(grey_rock_right, (tile_size, tile_size))
        grey_rock_floor = tile_sheet.image_at((112 + 16 * 4, 16 * 2, 16, 16), (255, 255, 255))
        grey_rock_floor = pg.transform.scale(grey_rock_floor, (tile_size, tile_size))
        inside = tile_sheet.image_at((112 + 16 * 4, 16, 16, 16), (255, 255, 255))
        inside = pg.transform.scale(inside, (tile_size, tile_size))
        rock_pillar_top = tile_sheet.image_at((112 + 16 * 6, 0, 16, 16), (255, 255, 255))
        rock_pillar_top = pg.transform.scale(rock_pillar_top, (tile_size, tile_size))
        rock_pillar = tile_sheet.image_at((112 + 16 * 6, 16, 16, 16), (255, 255, 255))
        rock_pillar = pg.transform.scale(rock_pillar, (tile_size, tile_size))
        grey_rock_pillar_top = tile_sheet.image_at((112 + 16 * 6, 16 * 2, 16, 16), (255, 255, 255))
        grey_rock_pillar_top = pg.transform.scale(grey_rock_pillar_top, (tile_size, tile_size))
        grey_rock_pillar = tile_sheet.image_at((112 + 16 * 6, 16 * 3, 16, 16), (255, 255, 255))
        grey_rock_pillar = pg.transform.scale(grey_rock_pillar, (tile_size, tile_size))
        grass_ltop = tile_sheet.image_at((112 + 16 * 4, 16 * 4, 16, 16), (255, 255, 255))
        grass_ltop = pg.transform.scale(grass_ltop, (tile_size, tile_size))
        grass_l = tile_sheet.image_at((112 + 16 * 4, 16 * 5, 16, 16), (255, 255, 255))
        grass_l = pg.transform.scale(grass_l, (tile_size, tile_size))
        grass_lbot = tile_sheet.image_at((112 + 16 * 4, 16 * 6, 16, 16), (255, 255, 255))
        grass_lbot = pg.transform.scale(grass_lbot, (tile_size, tile_size))
        grass_top = tile_sheet.image_at((112 + 16 * 5, 16 * 4, 16, 16), (255, 255, 255))
        grass_top = pg.transform.scale(grass_top, (tile_size, tile_size))
        grass_mid = tile_sheet.image_at((112 + 16 * 5, 16 * 5, 16, 16), (255, 255, 255))
        grass_mid = pg.transform.scale(grass_mid, (tile_size, tile_size))
        grass_bot = tile_sheet.image_at((112 + 16 * 5, 16 * 6, 16, 16), (255, 255, 255))
        grass_bot = pg.transform.scale(grass_bot, (tile_size, tile_size))
        grass_rtop = tile_sheet.image_at((112 + 16 * 4, 16 * 4, 16, 16), (255, 255, 255))
        grass_rtop = pg.transform.scale(grass_rtop, (tile_size, tile_size))
        grass_r = tile_sheet.image_at((112 + 16 * 4, 16 * 5, 16, 16), (255, 255, 255))
        grass_r = pg.transform.scale(grass_r, (tile_size, tile_size))
        grass_rbot = tile_sheet.image_at((112 + 16 * 4, 16 * 6, 16, 16), (255, 255, 255))
        grass_rbot = pg.transform.scale(grass_rbot, (tile_size, tile_size))

        for i, row in enumerate(level_layout):
            for j, col in enumerate(row):
                x_val = j * tile_size // 2
                y_val = i * tile_size

                if col == "1":
                    img_rect = rock_green1.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (rock_green1, img_rect)
                    self.tile_list.append(tile)
                if col == "2":
                    img_rect = rock_green2.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (rock_green2, img_rect)
                    self.tile_list.append(tile)
                if col == "3":
                    img_rect = rock_green3.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (rock_green3, img_rect)
                    self.tile_list.append(tile)
                if col == "L":
                    img_rect = rock_green_left.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (rock_green_left, img_rect)
                    self.tile_list.append(tile)
                if col == "R":
                    img_rect = rock_green_right.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (rock_green_right, img_rect)
                    self.tile_list.append(tile)
                if col == "4":
                    img_rect = grey_rock_green1.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (grey_rock_green1, img_rect)
                    self.tile_list.append(tile)
                if col == "5":
                    img_rect = grey_rock_green2.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (grey_rock_green2, img_rect)
                    self.tile_list.append(tile)
                if col == "6":
                    img_rect = grey_rock_green3.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (grey_rock_green3, img_rect)
                    self.tile_list.append(tile)
                if col == "l":
                    img_rect = grey_rock_green_left.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (grey_rock_green_left, img_rect)
                    self.tile_list.append(tile)
                if col == "r":
                    img_rect = grey_rock_green_right.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (grey_rock_green_right, img_rect)
                    self.tile_list.append(tile)
                if col == "U":
                    img_rect = rocky.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (rocky, img_rect)
                    self.tile_list.append(tile)
                if col == "u":
                    img_rect = grey_rocky.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (grey_rocky, img_rect)
                    self.tile_list.append(tile)
                if col == "N":
                    img_rect = rock_lwall.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (rock_lwall, img_rect)
                    self.tile_list.append(tile)
                if col == "M":
                    img_rect = rock_rwall.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (rock_rwall, img_rect)
                    self.tile_list.append(tile)
                if col == "A":
                    img_rect = rock_left.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (rock_left, img_rect)
                    self.tile_list.append(tile)
                if col == "D":
                    img_rect = rock_right.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (rock_right, img_rect)
                    self.tile_list.append(tile)
                if col == "n":
                    img_rect = grey_rock_lwall.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (grey_rock_lwall, img_rect)
                    self.back_list.append(tile)
                if col == "m":
                    img_rect = grey_rock_rwall.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (grey_rock_rwall, img_rect)
                    self.back_list.append(tile)
                if col == "a":
                    img_rect = grey_rock_left.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (grey_rock_left, img_rect)
                    self.tile_list.append(tile)
                if col == "d":
                    img_rect = grey_rock_right.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (grey_rock_right, img_rect)
                    self.tile_list.append(tile)
                if col == "F":
                    img_rect = rock_floor.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (rock_floor, img_rect)
                    self.tile_list.append(tile)
                if col == "f":
                    img_rect = rock_floor.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (grey_rock_floor, img_rect)
                    self.tile_list.append(tile)
                if col == "-":
                    img_rect = inside.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (inside, img_rect)
                    self.back_list.append(tile)
                if col == "A":
                    img_rect = inside.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (rock_pillar_top, img_rect)
                    self.tile_list.append(tile)
                if col == "I":
                    img_rect = inside.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (rock_pillar, img_rect)
                    self.tile_list.append(tile)
                if col == "a":
                    img_rect = inside.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (grey_rock_pillar_top, img_rect)
                    self.tile_list.append(tile)
                if col == "i":
                    img_rect = inside.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (grey_rock_pillar, img_rect)
                    self.tile_list.append(tile)
                if col == "7":
                    img_rect = inside.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (grass_ltop, img_rect)
                    self.back_list.append(tile)
                    self.end_list.append(tile)
                if col == "y":
                    img_rect = inside.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (grass_l, img_rect)
                    self.back_list.append(tile)
                    self.end_list.append(tile)
                if col == "j":
                    img_rect = inside.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (grass_lbot, img_rect)
                    self.back_list.append(tile)
                    self.end_list.append(tile)
                if col == "8":
                    img_rect = inside.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (grass_top, img_rect)
                    self.back_list.append(tile)
                    self.end_list.append(tile)
                if col == "=":
                    img_rect = inside.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (grass_mid, img_rect)
                    self.back_list.append(tile)
                    self.end_list.append(tile)
                if col == "k":
                    img_rect = inside.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (grass_bot, img_rect)
                    self.back_list.append(tile)
                    self.end_list.append(tile)
                if col == "9":
                    img_rect = inside.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (grass_rtop, img_rect)
                    self.back_list.append(tile)
                    self.end_list.append(tile)
                if col == "o":
                    img_rect = inside.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (grass_r, img_rect)
                    self.back_list.append(tile)
                    self.end_list.append(tile)
                if col == ";":
                    img_rect = inside.get_rect()
                    img_rect.x = x_val
                    img_rect.y = y_val
                    tile = (grass_r, img_rect)
                    self.back_list.append(tile)
                    self.end_list.append(tile)
                if col == "p":
                    player = Player(run_rt_list, self.tile_list, self.next)
                    player.rect.x = x_val
                    player.rect.y = y_val
                    self.player_group.add(player)
                if col == "x":
                    enemy = Enemy(run_enemy_list, self.tile_list)
                    enemy.rect.x = x_val
                    enemy.rect.y = y_val
                    self.enemy_group.add(enemy)
                elif col == "0":
                    pass

    def draw(self, display):
        for tile in self.tile_list:
            display.blit(tile[0], tile[1])
        for tile in self.back_list:
            display.blit(tile[0], tile[1])

        self.player_group.draw(display)
        self.enemy_group.draw(display)

    def update(self):
        self.player_group.update()
        self.enemy_group.update()
        self.camera()

    def camera(self):
        self.player = self.player_group.sprites()[0]
        keys = pygame.key.get_pressed()
        for tile in self.tile_list:
            if tile[1].colliderect(self.player.rect.x + self.player.change_x,
                                   self.player.rect.y,
                                   self.player.rect.width,
                                   self.player.rect.height):
                self.change_x = 0

        if self.player.rect.x > 200 and self.player.rect.x < WIN_WIDTH - 200:
            self.change_x = 0

        if self.player.rect.x >= WIN_WIDTH - 200:
            if self.player.change_x > 0:
                self.player.change_x = 0
                self.change_x = -2
        if self.player.rect.x <= 200:
            if self.player.change_x < 0:
                self.player.change_x = 0
                self.change_x = 2
        if not keys[pygame.K_LEFT] and not keys[pygame.K_RIGHT]:
            self.change_x = 0

        for tile in self.tile_list:
            if tile[1].colliderect(self.player.rect.x + self.player.change_x,
                                   self.player.rect.y,
                                   self.player.rect.width,
                                   self.player.rect.height):
                self.change_x = 0

        for tile in self.tile_list:
            tile[1].x += self.change_x
        for tile in self.back_list:
            tile[1].x += self.change_x
        for enemy in self.enemy_group:
            enemy.rect.x += self.change_x

    def Kill_Player(self):
        if pygame.sprite.groupcollide(self.player_group, self.enemy_group, False, True):
            return False
        if self.player.rect.y > WIN_HEIGHT + 75:
            return False

    def Next_Level(self):
        for tile in self.end_list:
            if tile[1].colliderect(self.player.rect.x + self.player.change_x,
                                   self.player.rect.y,
                                   self.player.rect.width,
                                   self.player.rect.height):
                LEVEL_SOUND.play()
                return False

    def Cont(self):
        characters = SpriteSheet("images/characters.png")
        run_enemy_list = characters.load_grid_images(1, 23, player_x, player_x_pad, 101, player_y_pad, width, height,
                                                     -1)
        if len(self.enemy_group) < 4:
            enemy = Enemy(run_enemy_list, self.tile_list)
            enemy.rect.x = 800
            enemy.rect.y = 720
            self.enemy_group.add(enemy)

