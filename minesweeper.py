
import pygame, sys
from pygame.locals import *

pygame.font.init()
from board import Board


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


class MineSweeper:
    def __init__(self) -> None:
        self.board = Board(width=25, height=10, mines=50)
        self.graphics = Graphics(width=25, height=10)
        self.turn = BLUE
        self.selected_piece = None # a board location. 
        self.hop = False
        self.selected_legal_moves = []
        
        # set up the board
        self.board.setup()


    def setup(self):
        """Draws the window and board at the beginning of the game"""
        self.graphics.setup_window()

    def event_loop(self):
        """
        The event loop. This is where events are triggered 
        (like a mouse click) and then effect the game state.
        """
        self.mouse_pos = self.graphics.board_coords(pygame.mouse.get_pos()) # what square is the mouse in?
        if self.selected_piece != None:
            self.selected_legal_moves = self.board.legal_moves(self.selected_piece, self.hop)

        for event in pygame.event.get():

            if event.type == QUIT:
                self.terminate_game()

            if event.type == MOUSEBUTTONDOWN:
                if self.hop == False:
                    print(self.mouse_pos)
                    # if self.board.location(self.mouse_pos).occupant != None and self.board.location(self.mouse_pos).occupant.color == self.turn:
                    #     self.selected_piece = self.mouse_pos

                    # elif self.selected_piece != None and self.mouse_pos in self.board.legal_moves(self.selected_piece):

                    #     self.board.move_piece(self.selected_piece, self.mouse_pos)
                    
                    #     if self.mouse_pos not in self.board.adjacent(self.selected_piece):
                    #         self.board.remove_piece(((self.selected_piece[0] + self.mouse_pos[0]) >> 1, (self.selected_piece[1] + self.mouse_pos[1]) >> 1))
                        
                    #         self.hop = True
                    #         self.selected_piece = self.mouse_pos

                    #     else:
                    #         self.end_turn()

                if self.hop == True:					
                    if self.selected_piece != None and self.mouse_pos in self.board.legal_moves(self.selected_piece, self.hop):
                        self.board.move_piece(self.selected_piece, self.mouse_pos)
                        self.board.remove_piece(((self.selected_piece[0] + self.mouse_pos[0]) >> 1, (self.selected_piece[1] + self.mouse_pos[1]) >> 1))

                    if self.board.legal_moves(self.mouse_pos, self.hop) == []:
                            self.end_turn()

                    else:
                        self.selected_piece = self.mouse_pos


    def update(self):
        """Calls on the graphics class to update the game display."""
        self.graphics.update_display(self.board, self.selected_legal_moves, self.selected_piece)

    def terminate_game(self):
        """Quits the program and ends the game."""
        pygame.quit()
        sys.exit

    def main(self):
        """"This executes the game and controls its flow."""
        self.setup()

        while True: # main game loop
            self.event_loop()
            self.update()

    def end_turn(self):
        """
        End the turn. Switches the current player. 
        end_turn() also checks for and game and resets a lot of class attributes.
        """
        if self.turn == BLUE:
            self.turn = RED
        else:
            self.turn = BLUE

        self.selected_piece = None
        self.selected_legal_moves = []
        self.hop = False

        if self.check_for_endgame():
            if self.turn == BLUE:
                self.graphics.draw_message("RED WINS!")
            else:
                self.graphics.draw_message("BLUE WINS!")

    def check_for_endgame(self):
        """
        Checks to see if a player has run out of moves or pieces. If so, then return True. Else return False.
        """
        for x in range(8):
            for y in range(8):
                if self.board.location((x,y)).color == BLACK and self.board.location((x,y)).occupant != None and self.board.location((x,y)).occupant.color == self.turn:
                    if self.board.legal_moves((x,y)) != []:
                        return False

        return True


class Graphics:
    def __init__(self, width, height):
        self.caption = "Minesweeper"

        # set up screen and object sizes
        self.fps = 60
        self.clock = pygame.time.Clock()

        self.window_size = 1200
        self.width = width
        self.height = height
        self.tile_size = self.window_size / width

        # load graphic resources
        self.tile_unchecked = None
        self.tile_checked = None
        self.mine = None

        self._load_resources()

        self.screen = pygame.display.set_mode((self.window_size, self.window_size*height/width))
        self.screen.fill((200, 200, 200))
        pygame.display.flip()
        # self.background = pygame.image.load('resources/board.png')

        self.message = False

    def setup_window(self):
        """
        This initializes the window and sets the caption at the top.
        """
        pygame.init()
        pygame.display.set_caption(self.caption)

    def update_display(self, board, legal_moves, selected_piece):
        """
        This updates the current display.
        """
        # self.screen.blit(self.background, (0,0))
        
        self.highlight_squares(legal_moves, selected_piece)
        self.draw_tiles()
        # self.draw_board_pieces(board)

        # if self.message:
        #     self.screen.blit(self.text_surface_obj, self.text_rect_obj)

        pygame.display.update()
        self.clock.tick(self.fps)

    def draw_tiles(self):
        """
        Takes a board object and draws all of its squares to the display
        """


        for x in range(self.width):
            for y in range(self.height):
                # pygame.draw.rect(self.screen, board[x][y].color, (x * self.square_size, y * self.square_size, self.square_size, self.square_size), )
                self.screen.blit(self.tile_unchecked, (x*self.tile_size, y*self.tile_size))

    def _load_resources(self):
        # load graphic resources
        self.tile_unchecked = self._scale_resource(pygame.image.load('resources/tile_unchecked.png'))
        self.tile_checked = self._scale_resource(pygame.image.load('resources/tile_checked.png'))
        self.mine = self._scale_resource(pygame.image.load('resources/mine.png'))

    def _scale_resource(self, image: pygame.image):
        width = image.get_width()
        height = image.get_height()
        ratio = self.tile_size / width
        image = pygame.transform.scale(image, (width*ratio, height*ratio))
        return image

    def pixel_coords(self, board_coords):
        """
        Takes in a tuple of board coordinates (x,y) 
        and returns the pixel coordinates of the center of the square at that location.
        """
        return (board_coords[0] * self.tile_size + self.tile_size, board_coords[1] * self.tile_size + self.tile_size)

    def board_coords(self, pixel):
        """
        Does the reverse of pixel_coords(). Takes in a tuple of of pixel coordinates and returns what square they are in.
        """
        return (pixel[0] // self.tile_size, pixel[1] // self.tile_size)

    def highlight_squares(self, squares, origin):
        """
        Squares is a list of board coordinates. 
        highlight_squares highlights them.
        """
        for square in squares:
            pygame.draw.rect(self.screen, HIGH, (square[0] * self.square_size, square[1] * self.square_size, self.square_size, self.square_size))	

        if origin != None:
            pygame.draw.rect(self.screen, HIGH, (origin[0] * self.square_size, origin[1] * self.square_size, self.square_size, self.square_size))

    def draw_message(self, message):
        """
        Draws message to the screen. 
        """
        self.message = True
        self.font_obj = pygame.font.Font('freesansbold.ttf', 44)
        self.text_surface_obj = self.font_obj.render(message, True, HIGH, BLACK)
        self.text_rect_obj = self.text_surface_obj.get_rect()
        self.text_rect_obj.center = (self.window_size >> 1, self.window_size >> 1)	


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
