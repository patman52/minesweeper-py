
import pygame, sys
from pygame.locals import *
from typing import Tuple

pygame.font.init()


from board import Board, TILE_STATES


##COLORS##
#             R    G    B 
WHITE    = (255, 255, 255)
BLUE     = (  0,   0, 255)
RED      = (255,   0,   0)
BLACK    = (  0,   0,   0)
GOLD     = (255, 215,   0)
HIGH     = (160, 190, 255)

##DIRECTIONS##
NORTHWEST = "northwest"
NORTHEAST = "northeast"
SOUTHWEST = "southwest"
SOUTHEAST = "southeast"

WINDOW_SIZE = 1200
INITIAL_BOARD = {
    'width': 25,
    'height': 10,
    'mines': 50
}


class MineSweeper:
    def __init__(self) -> None:

        # set up screen and object sizes
        self.caption: str = "Minesweeper"
        self.fps: int = 60
        self.clock = pygame.time.Clock()
        self.window_size = WINDOW_SIZE
        
        # set up the board
        self.board = Board(width=INITIAL_BOARD['width'], 
                           height=INITIAL_BOARD['height'], 
                           mines=INITIAL_BOARD['mines']) 
        self.board.setup()
        self.tile_size = self.window_size / self.board.width
        
        # load graphic resources
        self.tile_unchecked = None
        self.tile_checked = None
        self.mine = None
        self._load_resources()

        # create screen
        self.screen = pygame.display.set_mode((self.window_size, self.window_size*self.board.height/self.board.width))
        self.screen.fill((200, 200, 200))
        pygame.display.flip()
        
    def main(self):
        self.setup_window()

        while True: # main game loop
            self.event_loop()
            self.update_display()

    def event_loop(self):

        for event in pygame.event.get():
            row, col = self._find_clicked_tile(pygame.mouse.get_pos()) # what tile is the mouse in?

            if event.type == QUIT:
                self.terminate_game()

            if event.type == MOUSEBUTTONDOWN:
                print(f'clicked row {row}, col {col}')
                self.board.click_tile(row=row, col=col)

    def setup_window(self):
        pygame.init()
        pygame.display.set_caption(self.caption)

    def update_display(self):
        self.draw_tiles()
        pygame.display.update()
        self.clock.tick(self.fps)

    def draw_tiles(self):
        
        for tile in self.board.tiles:
            # first, determine what resource to display based on the tile status
            if tile.status == TILE_STATES[0]:
                resource = self.tile_unchecked
            elif tile.status == TILE_STATES[1]:
                if tile.mine:
                    resource = self.mine
                else:
                    resource = self.tile_checked
            elif tile.status == TILE_STATES[2]:
                pass
            elif tile.status == TILE_STATES[3]:
                pass
            
            self.screen.blit(resource, (tile.col*self.tile_size, tile.row*self.tile_size))

        # for x in range(self.width):
        #     for y in range(self.height):
        #         # pygame.draw.rect(self.screen, board[x][y].color, (x * self.square_size, y * self.square_size, self.square_size, self.square_size), )
        #         self.screen.blit(self.tile_unchecked, (x*self.tile_size, y*self.tile_size))

    def _load_resources(self):
        self.tile_unchecked = self._scale_resource(pygame.image.load('resources/tile_unchecked.png'))
        self.tile_checked = self._scale_resource(pygame.image.load('resources/tile_checked.png'))
        self.mine = self._scale_resource(pygame.image.load('resources/mine.png'))

    def _scale_resource(self, image: pygame.image):
        width = image.get_width()
        height = image.get_height()
        ratio = self.tile_size / width
        image = pygame.transform.scale(image, (width*ratio, height*ratio))
        return image

    def _find_tile_by_row_col(self, row: int, col: int) -> Tuple[float, float]:
        """
        Determines the pixel coordinates of a tile given a row and col
        """
        return (col * self.tile_size + self.tile_size, row * self.tile_size + self.tile_size)

    def _find_clicked_tile(self, mouse_pos: tuple) -> Tuple[int, int]:
        """
        finds the row and col of the tile click
        """
        return (int(mouse_pos[1] // self.tile_size), int(mouse_pos[0] // self.tile_size))

    def draw_message(self, message):
        """
        Draws message to the screen. 
        """
        self.message = True
        self.font_obj = pygame.font.Font('freesansbold.ttf', 44)
        self.text_surface_obj = self.font_obj.render(message, True, HIGH, BLACK)
        self.text_rect_obj = self.text_surface_obj.get_rect()
        self.text_rect_obj.center = (self.window_size >> 1, self.window_size >> 1)
	
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

        result = board.click_tile(row=row, col=col)

        board.print_board()

        if not board.valid or result:
            print("YOU HAVE CLICKED A MINE!")
            break



if __name__ == "__main__":
    minesweeper = MineSweeper()
    minesweeper.main()
