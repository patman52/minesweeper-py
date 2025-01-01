"""
minesweeper.py

A version of the classic minesweeper built in pure Python using Pygame!

Author P Tunis 12/2024
"""

# standard libraries
import datetime
import time
from math import sqrt
from typing import Tuple


# external dependencies
import pygame, sys
from pygame.locals import *

# custom scripts
from board import Board, TILE_STATES, TILE_ACTIONS
# from settings import User, NUM_TEXT_COLOUR, SCREEN_SIZE, MOUSE_RIGHT, HEADER_HEIGHT, SCREEN_FILL, MAX_SCREEN_RATIO, SEGMENTS_TO_DISPLAY, SEGMENT_POSITION_SIZE, SEGMENT_WIDTH, COUNTER_WIDTH, COUNTER_HEIGHT, TOTAL_DIGIT_HEIGHT, DIGIT_GAP
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

        # set up variables to track time and current status
        self.start_time: float | None = None
        self.end_time: float | None = None
        self.paused: bool = True  # used to pause inbetween games when we win or loose
        
        # load graphic resources
        self.tile_unchecked = None
        self.tile_checked = None
        self.tile_flagged = None
        self.tile_question = None
        self.mine = None
        self.new_game = None
        self.game_over = None
        self.segment_display = None
        self._load_resources()

        # create screen
        self.screen = pygame.display.set_mode((self.user.tile_size*width, self.user.tile_size*height+HEADER_HEIGHT))
        self.screen.fill(SCREEN_FILL)
        pygame.display.flip()
        
    def main(self):
        self.setup_window()

        while True: # main game loop
            self.event_loop()
            self.update_display()

    def event_loop(self):

        for event in pygame.event.get():
            # quit the game
            if event.type == QUIT:
                self.terminate_game()
            
            # save the game if we loose
            if not self.board.valid and not self.paused:
                self.paused = True
                if self.end_time is None:
                    self.end_time = time.time()-self.start_time
                self.user.save_game(self.user.current_game,datetime.datetime.today().strftime('%d-%m-%Y'), self.end_time, False)

            # save the game if we win
            if self.board.user_won and not self.paused:
                self.paused = True
                if self.end_time is None:
                    self.end_time = time.time()-self.start_time
                self.user.save_game(self.user.current_game,datetime.datetime.today().strftime('%d-%m-%Y'), self.end_time, False)
            
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
                    """
                    determine if the click is on the new game / game over button which isa circle
                    
                    finding if a point is in a circle
                    (x - center_x)² + (y - center_y)² < radius².
                    """
                    radius = self.new_game.get_width() / 2
                    center_x = self.user.tile_size * self.board.width / 2
                    center_y = HEADER_HEIGHT / 2

                    if sqrt((x - center_x)**2 + (y - center_y)**2) < radius:
                        self.start_time = time.time()
                        self.board.setup()
                        self.paused = False

            # when we release the button we will click any tile we are hovering over
            elif event.type == MOUSEBUTTONUP and self.board.tile_pressed:
                if y > HEADER_HEIGHT:
                    row, col = self._find_clicked_tile((x, y)) # what tile is the mouse in?
                    self.board.tile_action(action=TILE_ACTIONS[2], row=row, col=col)

                    # if the game hasn't started yet (typically since we've just loaded the program), start it now
                    if self.start_time is None:
                        self.start_time = time.time()
                        self.paused = False
                else:
                    self.board.tile_action(TILE_ACTIONS[1])

    def setup_window(self):
        pygame.init()
        pygame.display.set_caption(self.caption)

    def update_display(self):
        self.draw_buttons()
        self.draw_counters()
        self.draw_tiles()
        # check for end game
        if not self.board.valid:
            self.draw_mines()
            self.draw_message("GAME OVER!!")
        if self.board.user_won:
            self.draw_tiles()
            self.draw_message("YOU WON!!")
        pygame.display.update()
        self.clock.tick(self.fps)

    def draw_buttons(self):
        if not self.board.valid:
            button_width = self.new_game.get_width()
            button_height = self.new_game.get_height()
            self.screen.blit(self.game_over, (self.board.width*self.user.tile_size/2-button_width/2, (HEADER_HEIGHT-button_height)/2))
            return
        
        if self.board.tile_pressed:
            button_width = self.game_over.get_width()
            button_height = self.game_over.get_height()
            self.screen.blit(self.new_game_tile_pressed, (self.board.width*self.user.tile_size/2-button_width/2, (HEADER_HEIGHT-button_height)/2))
        else:
            button_width = self.game_over.get_width()
            button_height = self.game_over.get_height()
            self.screen.blit(self.new_game, (self.board.width*self.user.tile_size/2-button_width/2, (HEADER_HEIGHT-button_height)/2))

    def draw_counters(self):
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
            current_game_time = '000'
        elif self.board.user_won and self.end_time is not None:
            current_game_time = str(self.end_time).zfill(3)
        else:
            current_game_time = str(round(time.time() - self.start_time)).zfill(3)

        for digit_index, digit in enumerate(current_game_time):
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
        for tile in self.board.tiles:
            # first, determine what resource to display based on the tile status
            if tile.status == TILE_STATES[0]:
                if tile.pressed:
                    resource = pygame.transform.flip(self.tile_unchecked, True, True)
                else:
                    resource = self.tile_unchecked
                self.screen.blit(resource, (tile.col*self.user.tile_size, tile.row*self.user.tile_size + HEADER_HEIGHT))
            elif tile.status == TILE_STATES[1]:
                self.screen.blit(self.tile_checked, (tile.col*self.user.tile_size, tile.row*self.user.tile_size + HEADER_HEIGHT))
                if tile.adjacent_mines > 0:
                    mine_num = pygame.font.SysFont('Times New Roman', int(self.user.tile_size*0.8))
                    text_surface = mine_num.render(str(tile.adjacent_mines), False, NUM_TEXT_COLOUR[tile.adjacent_mines])
                    text_x = tile.col*self.user.tile_size + (self.user.tile_size - text_surface.get_width())/2
                    text_y = tile.row*self.user.tile_size + self.user.tile_size*0.05 + HEADER_HEIGHT
                    self.screen.blit(text_surface, (text_x, text_y))
            elif tile.status == TILE_STATES[2]:
                self.screen.blit(self.tile_flagged, (tile.col*self.user.tile_size, tile.row*self.user.tile_size + HEADER_HEIGHT))
            elif tile.status == TILE_STATES[3]:
                self.screen.blit(self.tile_question, (tile.col*self.user.tile_size, tile.row*self.user.tile_size + HEADER_HEIGHT))


    def draw_mines(self):
        for tile in self.board.tiles:
            if tile.mine:
                mine_x = tile.col*self.user.tile_size + (self.user.tile_size - self.mine.get_width())/2
                mine_y = tile.row*self.user.tile_size + (self.user.tile_size - self.mine.get_height())/2 + HEADER_HEIGHT
                self.screen.blit(self.mine, (mine_x, mine_y))

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

    def _load_resources(self):
        self.tile_unchecked = self._scale_resource(pygame.image.load('resources/tile_unchecked.png'))
        self.tile_checked = self._scale_resource(pygame.image.load('resources/tile_checked.png'))
        self.tile_flagged = self._scale_resource(pygame.image.load('resources/tile_flagged.png'))
        self.tile_question = self._scale_resource(pygame.image.load('resources/tile_question.png'))
        self.new_game = self._scale_resource(pygame.image.load('resources/new_game.png'))
        self.new_game_tile_pressed = self._scale_resource(pygame.image.load('resources/tile_pressed.png'))
        self.game_over = self._scale_resource(pygame.image.load('resources/game_over.png'))
        self.segment_display = self._scale_resource(pygame.image.load('resources/segment_display.png'), target_width=SEGMENT_WIDTH)
        self.segment_display_rot = pygame.transform.rotate(self.segment_display, 90.0)
        self.mine = self._scale_resource(pygame.image.load('resources/mine.png'), scaling=0.8)

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

    def draw_message(self, message: str, text_size: int = 44, text_color: tuple = (0, 0, 0)):
        """
        Draws message to the screen. 
        """
        font_obj = pygame.font.Font('freesansbold.ttf', text_size)
        text_surface_obj = font_obj.render(message, True, text_color)
        text_width = text_surface_obj.get_width()
        x = (self.screen.get_width()-text_width)/2
        y = (self.screen.get_height()-text_size)/2
        self.screen.blit(text_surface_obj, (x, y))

	
    def terminate_game(self):
        """Quits the program and ends the game."""
        pygame.quit()
        sys.exit


def text_version(width=25, height=10, mines=50):
    board = Board(width, height, mines)
    board.setup()
    board.print_board()

    while True:
        # response = input('Choose tile to click (enter EXIT to quit): ')
        row = input('Enter row: ')

        if not row.isdigit():
            print('please only enter integers')
            continue

        col = input('Enter col: ')
        
        if not row.isdigit():
            print('please only enter integers')
            continue

        if row.upper() == 'EXIT' or col.upper() == 'EXIT':
            break

        board.click_tile(row=row, col=col)

        board.print_board()

        if not board.valid:
            print("YOU HAVE CLICKED A MINE!")
            break


if __name__ == "__main__":
    minesweeper = MineSweeper()
    minesweeper.main()
