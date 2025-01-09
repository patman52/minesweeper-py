"""
minesweeper.py

A version of the classic minesweeper built in pure Python using Pygame!

Author Paul Archer Tunis
"""

# standard libraries
import datetime
import time
import sys
from typing import Tuple, Optional

# external dependencies
import pygame
from pygame.locals import *

# custom scripts
from board import *
from button import Button, BUTTON_SHAPES
from settings import *

pygame.font.init()


class MineSweeper:
    def __init__(self):

        # set up screen and object sizes
        self.caption: str = "Minesweeper"
        self.fps: int = 24
        self.clock = pygame.time.Clock()
        self.user = User()

        width, height, mines = self._determine_screen_board_size()
        
        # set up the board
        self.board = Board(width=width, height=height, mines=mines)    
        self.board.setup()

        # current display (either the game or the settings windows)
        self.current_display: str = DISPLAYS[0]

        # set up variables to track time and current status
        self.start_time: float = 0.0
        self.current_game_time: float = 0.0
        self.game_started: bool = False
        self.paused: bool = True  # used to pause inbetween games when we win or loose
        
        # ties buttons to images, positions, etc.
        self.button_mapping: dict[str: Button] = {}
        self.return_pressed: bool = False
        self.reset_pressed: bool = True
        
        # load graphic resources
        self.tile_unchecked = None
        self.tile_checked = None
        self.tile_flagged = None
        self.tile_question = None
        self.tile_mine_checked = None
        self.mine = None
        self.segment_display = None

        # create screen
        self.screen = pygame.display.set_mode((self.user.tile_size*width, self.user.tile_size*height+HEADER_HEIGHT))
        self.screen.fill(SCREEN_FILL)
        self.settings_submenu_width = None
        self.settings_submenu_height = None
        self.slider_width = None
        self.slider_pos_x = None
        self.width_slider_y = None
        self.height_slider_y = None
        self.mine_slider_y = None

        # create buttons and load image resources
        self._map_buttons()
        self._load_resources()

        pygame.display.flip()

    def main(self):
        self.setup_window()

        while True: # main game loop
            self.event_loop()
            self.update_display()

    def event_loop(self):
        if not self.board.user_won and self.board.valid and not self.paused:
            self.current_game_time = time.time() - self.start_time

        for event in pygame.event.get():
            # quit the game
            if event.type == QUIT:
                self.terminate_game()

            # events for the main game board
            if self.current_display == DISPLAYS[0]:
                self.game_event(event)

            elif self.current_display == DISPLAYS[1]:
                self.settings_event(event)

    def game_event(self, event):
        # save the game if we loose
        if not self.board.valid and not self.paused:
            self.paused = True
            self.user.save_game(self.user.current_game,datetime.datetime.today().strftime('%M-%D-%Y'), self.current_game_time, False)

        # save the game if we win
        if self.board.user_won and not self.paused:
            self.paused = True
            self.user.save_game(self.user.current_game,datetime.datetime.today().strftime('%M-%D-%Y'), self.current_game_time, True)
        
        # get the current position of the mouse
        x, y = pygame.mouse.get_pos()

        # flag the tile
        if event.type == MOUSEBUTTONDOWN and event.button == MOUSE_RIGHT and y > HEADER_HEIGHT:
            row, col = self._find_clicked_tile((x, y)) # what tile is the mouse in?
            self.board.tile_action(action=TILE_ACTIONS[3], row=row, col=col)
            return

        # when we click down on the tile, and hold it, it will be 'pressed'
        if pygame.mouse.get_pressed()[0]:
            if y > HEADER_HEIGHT:
                row, col = self._find_clicked_tile((x, y)) # what tile is the mouse in?
                self.board.tile_action(action=TILE_ACTIONS[0], row=row, col=col)
            else:
                # check if it's in the circle for the new game button
                if self.button_mapping['new_game'].check_collide((x, y)):
                    self.start_time = time.time()
                    self.board.setup()
                    self.paused = False
                # check if it's in the circle for the settings / stat screen
                elif self.button_mapping['open_settings'].check_collide((x, y)):
                    print('changing to the settings / stats screen')
                    self.user.get_calc_stats()
                    self._determine_settings_positions()
                    self.current_display = DISPLAYS[1]
                
        # when we release the button we will click any tile we are hovering over
        elif event.type == MOUSEBUTTONUP and self.board.tile_pressed:
            if y > HEADER_HEIGHT:
                row, col = self._find_clicked_tile((x, y)) # what tile is the mouse in?
                self.board.tile_action(action=TILE_ACTIONS[2], row=row, col=col)

                # if the game hasn't started yet (typically since we've just loaded the program), start it now
                if self.paused:
                    self.start_time = time.time()
                    self.paused = False
            else:
                self.board.tile_action(TILE_ACTIONS[1])
                self.user._load_game_data()

        self.button_mapping['new_game'].pressed = self.board.tile_pressed

    def settings_event(self, event):
        # get the current position of the mouse
        x, y = pygame.mouse.get_pos()

        # check if we pressed either the return or reset stat button
        if pygame.mouse.get_pressed()[0]:
            if self.button_mapping['return'].check_collide((x, y)):
                self.button_mapping['return'].pressed = True
                return
            if self.button_mapping['reset_stats'].check_collide((x, y)):
                self.button_mapping['reset_stats'].pressed = True
                return

            if self.button_mapping['width_slider'].check_collide((x, y)) and not self.button_mapping['width_slider'].pressed:
                self.button_mapping['width_slider'].pressed = True
                return

            if self.button_mapping['height_slider'].check_collide((x, y)) and not self.button_mapping['height_slider'].pressed:
                self.button_mapping['height_slider'].pressed = True
                return
            
            if self.button_mapping['mine_slider'].check_collide((x, y)) and not self.button_mapping['mine_slider'].pressed:
                self.button_mapping['mine_slider'].pressed = True
                return

            if self.button_mapping['width_slider'].pressed:
                self._slider_position_to_board_stats(x, 'width_slider')

            if self.button_mapping['height_slider'].pressed:
                self._slider_position_to_board_stats(x, 'height_slider')

            if self.button_mapping['mine_slider'].pressed:
                self._slider_position_to_board_stats(x, 'mine_slider')

        elif event.type == MOUSEBUTTONUP:
            if self.button_mapping['return'].check_collide((x, y)) and self.button_mapping['return'].pressed:
                print('returning to game screen')
                self.button_mapping['return'].pressed = False
                self.current_display = DISPLAYS[0]
            if self.button_mapping['reset_stats'].check_collide((x, y)) and self.button_mapping['reset_stats'].pressed:
                self.button_mapping['reset_stats'].pressed = False
                print('reseting all game stats')
                # self.user.reset_stats()
        else:
            self.button_mapping['return'].pressed = False
            self.button_mapping['reset_stats'].pressed = False
            self.button_mapping['width_slider'].pressed = False
            self.button_mapping['height_slider'].pressed = False
            self.button_mapping['mine_slider'].pressed = False 

    def setup_window(self):
        pygame.init()
        pygame.display.set_caption(self.caption)

    def update_display(self):
        self.draw_layout()
        self.draw_stats()
        self.draw_buttons()
        self.draw_counters()
        self.draw_tiles()   
        self.draw_mines()    
        if self.board.user_won:
            self.draw_text('YOU WON!!!', text_pos=(self.screen.get_width()/2, self.screen.get_height()/2), text_size=60)
        pygame.display.update()
        self.clock.tick(self.fps)

    def draw_buttons(self):
        for button_name, button in self.button_mapping.items():
            if button.display != self.current_display:
                continue

            if not self.board.valid:
                image = button.image_game_over
            elif button.pressed:
                image = button.image_pressed
            else:
                image = button.image_normal
            self.screen.blit(image, button.pos)

            if button.text_to_display is not None:
                self.draw_text(button.text_to_display, text_size=button.text_size, bounding_box=button.get_bounding_box())

    def draw_counters(self):
        # don't draw counters for settings menu
        if self.current_display == DISPLAYS[1]:
            return
        
        # first draw the counter with the remaining mines
        mines_remaining = str(len(self.board.tiles_with_mines) - self.board.get_flagged_mine_count()).zfill(3)
        mine_count_pos_x = self.screen.get_width()/2-self.user.tile_size-COUNTER_WIDTH
        mines_rect = pygame.Rect(mine_count_pos_x, HEADER_HEIGHT*0.1, COUNTER_WIDTH, COUNTER_HEIGHT)
        remaining_mines_bg = pygame.draw.rect(self.screen, (0, 0, 0), mines_rect)
        time_count_pos_x = self.screen.get_width()/2+self.user.tile_size
        time_rect = pygame.Rect(time_count_pos_x, HEADER_HEIGHT*0.1, COUNTER_WIDTH, COUNTER_HEIGHT)
        time_bg = pygame.draw.rect(self.screen, (0, 0, 0), time_rect)
        # pygame.display.flip()

        for digit_index, digit in enumerate(mines_remaining):
            segs_to_display = SEGMENTS_TO_DISPLAY[int(digit)]
            # segs_to_display = [True, True, True, True]
            for seg_index, seg in enumerate(segs_to_display):
                if not seg:
                    continue
                base_x = mine_count_pos_x + (COUNTER_WIDTH - TOTAL_DIGIT_WIDTH*3 - DIGIT_GAP*2)/2 + digit_index*(TOTAL_DIGIT_WIDTH+DIGIT_GAP)
                base_y = (HEADER_HEIGHT - TOTAL_DIGIT_HEIGHT)/2

                seg_x, seg_y, rotate = SEGMENT_POSITION_SIZE[seg_index]

                if rotate:
                    image = self.segment_display_rot
                else:
                    image = self.segment_display
                
                self.screen.blit(image, (seg_x+base_x, seg_y+base_y))

        if self.start_time is None:
            current_game_time_str = '000'
        else:
            current_game_time_str = str(round(self.current_game_time)).zfill(3)

        for digit_index, digit in enumerate(current_game_time_str):
            segs_to_display = SEGMENTS_TO_DISPLAY[int(digit)]
            # segs_to_display = [True, True, True, True]
            for seg_index, seg in enumerate(segs_to_display):
                if not seg:
                    continue
                base_x = time_count_pos_x + (COUNTER_WIDTH - TOTAL_DIGIT_WIDTH*3 - DIGIT_GAP*2)/2 + digit_index*(TOTAL_DIGIT_WIDTH+DIGIT_GAP)
                base_y = (HEADER_HEIGHT - TOTAL_DIGIT_HEIGHT)/2

                seg_x, seg_y, rotate = SEGMENT_POSITION_SIZE[seg_index]

                if rotate:
                    image = self.segment_display_rot
                else:
                    image = self.segment_display
                
                self.screen.blit(image, (seg_x+base_x, seg_y+base_y))

    def draw_tiles(self): 
        # don't draw tiles for settings menu
        if self.current_display == DISPLAYS[1]:
            return

        for tile in self.board.tiles:
            # first, determine what resource to display based on the tile status
            if tile.status == TILE_STATES[0]:
                if tile.pressed:
                    resource = pygame.transform.flip(self.tile_unchecked, True, True)
                else:
                    resource = self.tile_unchecked
                self.screen.blit(resource, (tile.col*self.user.tile_size, tile.row*self.user.tile_size + HEADER_HEIGHT))
            elif tile.status == TILE_STATES[1]:
                if tile.mine:
                    self.screen.blit(self.tile_mine_checked, (tile.col*self.user.tile_size, tile.row*self.user.tile_size + HEADER_HEIGHT))
                else:
                    self.screen.blit(self.tile_checked, (tile.col*self.user.tile_size, tile.row*self.user.tile_size + HEADER_HEIGHT))
                if tile.adjacent_mines > 0:
                    text_x = tile.col*self.user.tile_size + self.user.tile_size/2
                    text_y = tile.row*self.user.tile_size + self.user.tile_size/2 + HEADER_HEIGHT
                    self.draw_text(str(tile.adjacent_mines), text_size=int(self.user.tile_size*0.8), text_pos=(text_x, text_y), 
                                   font='Times New Roman', text_color=NUM_TEXT_COLOUR[tile.adjacent_mines])

            elif tile.status == TILE_STATES[2]:
                self.screen.blit(self.tile_flagged, (tile.col*self.user.tile_size, tile.row*self.user.tile_size + HEADER_HEIGHT))
            elif tile.status == TILE_STATES[3]:
                self.screen.blit(self.tile_question, (tile.col*self.user.tile_size, tile.row*self.user.tile_size + HEADER_HEIGHT))

    def draw_mines(self):
        if self.current_display == DISPLAYS[1]:
            return
        if self.board.valid:
            return
        for tile in self.board.tiles:
            if tile.mine:
                mine_x = tile.col*self.user.tile_size + (self.user.tile_size - self.mine.get_width())/2
                mine_y = tile.row*self.user.tile_size + (self.user.tile_size - self.mine.get_height())/2 + HEADER_HEIGHT
                self.screen.blit(self.mine, (mine_x, mine_y))
                continue
            
            # draw and X on any tiles that were flagged as mines and not actually mines
            if tile.status == TILE_STATES[2] and not tile.mine:
                text_x = tile.col*self.user.tile_size + self.user.tile_size/2
                text_y = tile.row*self.user.tile_size + self.user.tile_size/2 + HEADER_HEIGHT

                self.draw_text('X', text_size=int(self.user.tile_size*0.8), text_pos=(text_x, text_y), font='Arial')

    def draw_layout(self):
        # draw the return to game button
        self.screen.fill(SCREEN_FILL)
        if self.current_display == DISPLAYS[1]:
            # draw settings sub-menu
            settings_menu_rect = pygame.Rect(SETTINGS_INSET, SETTINGS_INSET, self.settings_submenu_width, self.settings_submenu_height)
            pygame.draw.rect(self.screen, SETTING_FILL, settings_menu_rect)

            # width slider bar
            self.draw_text('WIDTH', bounding_box=(self.slider_pos_x, self.width_slider_y-55, self.slider_width, 40))
            width_slider_rect = pygame.Rect(self.slider_pos_x, self.width_slider_y, self.slider_width, SLIDER_HEIGHT)
            pygame.draw.rect(self.screen, (0, 0, 0), width_slider_rect)

            # height slider bar
            self.draw_text('HEIGHT', bounding_box=(self.slider_pos_x, self.height_slider_y-55, self.slider_width, 40))
            height_slider_rect = pygame.Rect(self.slider_pos_x, self.height_slider_y, self.slider_width, SLIDER_HEIGHT)
            pygame.draw.rect(self.screen, (0, 0, 0), height_slider_rect)

            # mine slider bar
            self.draw_text('MINES', bounding_box=(self.slider_pos_x, self.mine_slider_y-55, self.slider_width, 40))
            mine_slider_rect = pygame.Rect(self.slider_pos_x, self.mine_slider_y, self.slider_width, SLIDER_HEIGHT)
            pygame.draw.rect(self.screen, (0, 0, 0), mine_slider_rect)

            # draw stats sub-menu
            stat_menu_rect = pygame.Rect((SETTINGS_INSET+self.screen.get_width())/2, SETTINGS_INSET, self.settings_submenu_width, self.settings_submenu_height)
            pygame.draw.rect(self.screen, SETTING_FILL, stat_menu_rect)

    def draw_stats(self):
        if self.current_display == DISPLAYS[0]:
            return
        pos_x = self.screen.get_width()/2 + SETTINGS_INSET*3
        pos_y = 60
        new_line_spacing = 25

        for i, (game_type, data) in enumerate(self.user.game_history.items()):           
            self.draw_text(game_type, text_pos=(pos_x, pos_y), text_size=15, center=False)
            pos_y += new_line_spacing
            for stat_name, val in data.items():
                if type(val) == list:
                    continue
                self.draw_text(f'{stat_name}: {round(val, 3)}', text_pos=(pos_x, pos_y), text_size=15, center=False)
                pos_y += new_line_spacing


    def _determine_screen_board_size(self):
        # get the size of the users screen
        width = self.user.board_sizes[self.user.current_game]['width']
        height = self.user.board_sizes[self.user.current_game]['height']
        mines = self.user.board_sizes[self.user.current_game]['mines']

        if self.user.tile_size * width > SCREEN_SIZE[0] * MAX_SCREEN_RATIO:
            self.user.tile_size = SCREEN_SIZE[0] * MAX_SCREEN_RATIO / width

        if self.user.tile_size * height > SCREEN_SIZE[1] * MAX_SCREEN_RATIO:
            self.user.tile_size = SCREEN_SIZE[1] * MAX_SCREEN_RATIO / height

        return width, height, mines

    def _determine_settings_positions(self):
        self.settings_submenu_width = self.screen.get_width()/2-SETTINGS_INSET*1.5
        self.settings_submenu_height = self.screen.get_height()-SETTINGS_INSET*2
        self.slider_width = self.settings_submenu_width*0.65
        self.slider_pos_x = SETTINGS_INSET + (self.settings_submenu_width - self.slider_width)/2
        self.width_slider_y = self.settings_submenu_height*0.2
        self.height_slider_y = self.settings_submenu_height*0.4
        self.mine_slider_y = self.settings_submenu_height*0.6
        self._determine_slider_icon_positions()
        
    def _determine_slider_icon_positions(self):
        self.button_mapping['width_slider'].pos = [self.slider_pos_x+self.slider_width * (self.board.width-MIN_WIDTH)/(MAX_WIDTH-MIN_WIDTH)-SLIDER_ICON_WIDTH/2, self.width_slider_y-(SLIDER_ICON_WIDTH-SLIDER_HEIGHT)/2]
        self.button_mapping['height_slider'].pos = [self.slider_pos_x+self.slider_width * (self.board.height-MIN_HEIGHT)/(MAX_HEIGHT-MIN_HEIGHT)-SLIDER_ICON_WIDTH/2, self.height_slider_y-(SLIDER_ICON_WIDTH-SLIDER_HEIGHT)/2]
        self.button_mapping['mine_slider'].pos = [self.slider_pos_x+self.slider_width * (self.board.mine_count-self.board.width*self.board.height*MIN_MINE_RATIO)/(self.board.width*self.board.height*MAX_MINE_RATIO-self.board.width*self.board.height*MIN_MINE_RATIO)-SLIDER_ICON_WIDTH/2, self.mine_slider_y-(SLIDER_ICON_WIDTH-SLIDER_HEIGHT)/2]

    def _slider_position_to_board_stats(self, x: float, slider: str):
        
        if x <= self.slider_pos_x:
            ratio = 0.0
        elif x >= self.slider_pos_x + self.slider_width:
            ratio = 1.0
        else:
            ratio = (x - self.slider_pos_x) / self.slider_width
        print(f'x = {x}, slider pos = {self.slider_pos_x}, width = {self.slider_width}, ratio = {ratio}')
        print(f'width = {self.board.width}')

        if slider == 'width_slider':
            self.board.width = int((MAX_WIDTH-MIN_WIDTH)*ratio + MIN_WIDTH)
            self.button_mapping['width_slider'].text_to_display = self.board.width
        elif slider == 'height_slider':
            self.board.height = int((MAX_HEIGHT-MIN_HEIGHT)*ratio + MIN_HEIGHT)
            self.button_mapping['height_slider'].text_to_display = self.board.height
        elif slider == 'mine_slider':
            self.board.mine_count = int(self.board.width*self.board.height*(MAX_MINE_RATIO-MIN_MINE_RATIO)*ratio + self.board.width*self.board.height*MIN_MINE_RATIO) 
            self.button_mapping['mine_slider'].text_to_display = self.board.mine_count
        else:
            raise ValueError(f'slider {slider} specified does not exist!')
        
        print(f'width now = {self.board.width}')

        self._determine_slider_icon_positions()

    def _map_buttons(self):
        """
        We have four buttons and three sliders we need to track.
        On the game screen/display:
            New Game Button
            Open Settings
        On the settings screen/display:
            Return to Game
            Reset stats
            three 'sliders' for the width, height, and mine count
        """

        self.button_mapping['new_game'] = Button(
            name='new_game', 
            image_normal=self._scale_resource(pygame.image.load('resources/new_game.png')), 
            image_pressed=self._scale_resource(pygame.image.load('resources/tile_pressed.png')), 
            image_game_over=self._scale_resource(pygame.image.load('resources/game_over.png')),
            pos=[self.screen.get_width()/2, HEADER_HEIGHT/2],
            shape=BUTTON_SHAPES[1]
            )
        
        self.button_mapping['open_settings'] = Button(
            name='open_settings',
            image_normal=self._scale_resource(pygame.image.load('resources/settings.png'), scaling=0.9),
            pos=[SETTINGS_BTN_PADX, HEADER_HEIGHT / 2],
            shape=BUTTON_SHAPES[1],
            center=(False, True)
        )

        self.button_mapping['return'] = Button(
            name='return',
            image_normal=self._scale_resource(pygame.image.load('resources/settings btn unpressed.png'), target_width=CHANGE_SETTINGS_WIDTH),
            image_pressed=self._scale_resource(pygame.image.load('resources/settings btn pressed.png'), target_width=CHANGE_SETTINGS_WIDTH),
            display=DISPLAYS[1],
            pos=[self.screen.get_width()/4, self.screen.get_height()-SETTINGS_INSET*5],
            text_to_display='Return to Menu',
            text_size=30,
        )

        self.button_mapping['reset_stats'] = Button(
            name='reset_stats',
            image_normal=self._scale_resource(pygame.image.load('resources/settings btn unpressed.png'), target_width=CHANGE_SETTINGS_WIDTH),
            image_pressed=self._scale_resource(pygame.image.load('resources/settings btn pressed.png'), target_width=CHANGE_SETTINGS_WIDTH),
            display=DISPLAYS[1],
            pos=[self.screen.get_width()*0.75, self.screen.get_height()-SETTINGS_INSET*5],
            text_to_display='Reset Stats',
            text_size=30
        )

        self.button_mapping['width_slider'] = Button(
            name='width_slider',
            image_normal=self._scale_resource(pygame.image.load('resources/slider.png'), target_width=SLIDER_ICON_WIDTH),
            display=DISPLAYS[1],
            text_to_display=self.board.width,
            text_size=int(SLIDER_ICON_WIDTH*0.8)
        )

        self.button_mapping['height_slider'] = Button(
            name='width_slider',
            image_normal=self._scale_resource(pygame.image.load('resources/slider.png'), target_width=SLIDER_ICON_WIDTH),
            display=DISPLAYS[1],
            text_to_display=self.board.height,
            text_size=int(SLIDER_ICON_WIDTH*0.8)
        )

        self.button_mapping['mine_slider'] = Button(
            name='width_slider',
            image_normal=self._scale_resource(pygame.image.load('resources/slider.png'), target_width=SLIDER_ICON_WIDTH),
            display=DISPLAYS[1],
            text_to_display=self.board.mine_count,
            text_size=int(SLIDER_ICON_WIDTH*0.8)
        )

    def _load_resources(self):
        self.tile_unchecked = self._scale_resource(pygame.image.load('resources/tile_unchecked.png'))
        self.tile_checked = self._scale_resource(pygame.image.load('resources/tile_checked.png'))
        self.tile_flagged = self._scale_resource(pygame.image.load('resources/tile_flagged.png'))
        self.tile_question = self._scale_resource(pygame.image.load('resources/tile_question.png'))
        self.tile_mine_checked = self._scale_resource(pygame.image.load('resources/tile_mine_checked.png'))
        self.mine = self._scale_resource(pygame.image.load('resources/mine.png'), scaling=0.8)
        self.segment_display = self._scale_resource(pygame.image.load('resources/segment_display.png'), target_width=SEGMENT_WIDTH)
        self.segment_display_rot = pygame.transform.rotate(self.segment_display, 90.0)

    def _scale_resource(self, image: pygame.image, scaling: float = 1.0, target_width: None | float = None):
        width = image.get_width()
        height = image.get_height()
        if target_width is None:
            ratio = self.user.tile_size / width
        else:
            ratio = target_width / width
        image = pygame.transform.scale(image, (width*ratio*scaling, height*ratio*scaling))
        return image

    def _find_tile_by_row_col(self, row: int, col: int) -> Tuple[float, float]:
        """
        Determines the pixel coordinates of a tile given a row and col
        """
        return (col * self.user.tile_size + self.user.tile_size, row * self.user.tile_size + self.user.tile_size)

    def _find_clicked_tile(self, mouse_pos: tuple) -> Tuple[int, int]:
        """
        finds the row and col of the tile click
        """
        return (int((mouse_pos[1] - HEADER_HEIGHT) // self.user.tile_size), int(mouse_pos[0] // self.user.tile_size))

    def draw_text(self, message: str, bounding_box: Optional[tuple[float]] = None, inset: float = 0.0,
                  text_size: Optional[int] = None, text_pos: Optional[tuple] = None, font: str = 'Calibri', 
                  text_color: tuple = (0, 0, 0), center: bool = True):
        """
        Draws message to the screen. 
        param: bounding box: (x, y, w, h) -> draw text within a bounding box, will prioritize this over any specifed size or position
        param: inset: desire percent inset from the bounding box border, cannout exceed 25%
        """

        message = str(message)

        if bounding_box is None and text_size is None and text_pos is None:
            raise ValueError(f'bounding box, or text size and pos must be specified')

        if inset > 0.25:
            raise ValueError(f'text inset of bounding box cannot exceed 25% of objects height or width')
        
        if bounding_box is not None: 
            if text_size is None:              
                text_size = int(bounding_box[3]*(1-inset))
            while True:
                font_obj = pygame.font.SysFont(font, text_size)
                text_surface_obj = font_obj.render(str(message), True, text_color)
                if text_surface_obj.get_width() > bounding_box[2]*(1-inset):
                    # get new width
                    ratio = text_surface_obj.get_width() / (bounding_box[2]*(1-inset))
                    text_size = int(text_size/ratio)
                    continue
                break
            
            x = bounding_box[0] + (bounding_box[2] - text_surface_obj.get_width())/2
            y = bounding_box[1] + (bounding_box[3] - text_surface_obj.get_height())/2

        else:
            font_obj = pygame.font.SysFont(font, text_size)
            text_surface_obj = font_obj.render(str(message), True, text_color)
            
            if center:
                text_width = text_surface_obj.get_width()
                text_height = text_surface_obj.get_height()
                x = text_pos[0] - text_width/2
                y = text_pos[1] - text_height/2
            else:
                x, y = text_pos

        self.screen.blit(text_surface_obj, (x, y))
	
    def terminate_game(self):
        """Quits the program and ends the game."""
        pygame.quit()
        sys.exit


if __name__ == "__main__":
    minesweeper = MineSweeper()
    minesweeper.main()
