
import random

# used to find neighboring tile ids
SHIFT = {
    0: [-1, -1],
    1: [-1, 0],
    2: [-1, 1],
    3: [0, -1],
    4: [0, 1],
    5: [1, -1],
    6: [1, 0],
    7: [1, 1]
}

# used to assign controlled statuses to tiles as they are instantiated and clicked/flagged
TILE_STATES = [
    'unchecked',
    'checked',
    'flagged',
    'question'
]

TILE_ACTIONS = [
    'press',    # presses the tile but does not check if, possibly triggering a mind and end gam
    'release',  # releases the tile without checking it
    'click',    # changes tile status from unchecked to checked, if the tile is a mine, endgame
    'flag',     # also serves to place a question mark if the tile is already flagged
]

MAX_WIDTH = 40
MAX_TILES = 1600
MAX_MINE_SHARE = 0.8    # the maximum percent of mines per total tiles allowed


class Board:
    def __init__(self, width: int, height: int, mines: int) -> None:
        self.width: int = width                 # the width of the board in tiles
        self.height: int = height               # the height of the board in tiles
        self.mine_count: int = mines            # total count of mines
        self.tiles: list[int] = []              # a list of all tile objects
        self.tiles_with_mines: list = []        # the tile ids that have mines
        self.neighbors: dict[int: list] = {}    # maps tiles to their neighbors key = tile id / value = list of neighboring tiles
        self.valid = True                       # turns to false if a mine is clicked
        self.user_won = False                   # turns true when all mines have been correctly found!
        # check that the number of mines does not exceed the total tiles
        if self.mine_count / (self.width * self.height) > MAX_MINE_SHARE:
            raise ValueError(f'mines cannot exceed {MAX_MINE_SHARE*100}% of total board tiles!\n'
                             f'Current mines: {self.mine_count}, total tiles: {self.width*self.height}')
        self.tile_pressed = False
        self.current_pressed_tile: int = -1

    def setup(self) -> None:
        """
        Start a new game board
        """
        self.clear_board()
        self._create_tiles()
        self._assign_mines()
        self._map_neighbors()
        self.valid = True
        print("board set up!")

    def clear_board(self) -> None:
        """
        Clear the existing gameboard
        """
        self.tiles.clear()
        self.tiles_with_mines.clear()
        self.neighbors.clear()
    
    def reset_mines(self) -> None:
        for tile in self.tiles:
            tile.mine = False 
            tile.status = TILE_STATES[0]
            tile.adjacent_mines = 0
        self.neighbors.clear()
        self._assign_mines()
        self._map_neighbors()

    def get_tile_id_by_row_and_col(self, row: int, col: int) -> int | None:
        """
        Returns the id of the tile based on the input row and column
        param: row - the row of the tile indexed to 0
        param: col -> the col of the tile indexed to 0 

        """
        if 0 <= row < self.height and 0 <= col < self.width:
            return row*self.width + col
        
        return None
    
    def tile_action(self, action: str, **kwargs) -> None:
        """
        Control pressing, clicking, and flagging tiles and their associated status changes
        param: action - one of the elements in the TILE_ACTIONS list denoting what we are trying to do to the tile
        Keyword arguments can be:
            tile_id: int -> the index of the tile in the tiles list
            row: int -> the row of the tile indexed to 0
            col: int -> the col of the tile indexed to 0
        """

        if action not in TILE_ACTIONS:
            raise ValueError(f'{action} is not a valid action to perform against a tile')

        # get the tile_id we are performing the tile against        
        if 'tile_id' in kwargs and action != TILE_ACTIONS[1]:
            tile_id = int(kwargs['tile_id'])
        elif 'row' in kwargs and 'col' in kwargs and action != TILE_ACTIONS[1]:
            tile_id = self.get_tile_id_by_row_and_col(kwargs['row'], kwargs['col'])

            if tile_id is None:
                print('No matching row or coloumn on game board!')
                return           
        elif action == TILE_ACTIONS[1]:
            self._release_tiles()
            return
        else:
            raise ValueError('You must specify either a tile id, or a row and col pair')

        # if the tile is flagged on question mark, already checked, we won the game, or the board is not valid, then actions do nothing
        if self.tiles[tile_id].status != TILE_STATES[0] and action != TILE_ACTIONS[3] or not self.valid or self.user_won:
            return

        # pressing a tile
        if action == TILE_ACTIONS[0]:
            self._press_tile(tile_id)
            return

        # clicking a tile
        if action == TILE_ACTIONS[2]:
            self._click_tile(tile_id)
            return

        # flagging / question mark a tile
        if action == TILE_ACTIONS[3]:
            self._flag_tile(tile_id)
            return

    def _press_tile(self, tile_id) -> None:
        self._release_tiles()
        self.tiles[tile_id].pressed = True
        self.tile_pressed = True

    def _release_tiles(self) -> None:
        self.tile_pressed = False
        self.current_pressed_tile = -1
        for tile in self.tiles:
            tile.pressed = False

    def _click_tile(self, tile_id: int) -> None:
        self._release_tiles()
        
        self.tiles[tile_id].status = TILE_STATES[1]
        
        # if its a mine, then game over
        if self.tiles[tile_id].mine:
            print('YOU CLICKED A MINE!')
        
        # if the tile has zero adjacent mines, we need to clear out all neighboring zero adjancent mine tiles
        elif self.tiles[tile_id].adjacent_mines == 0:
            self._find_zero_adjacent_neighboring_tiles(tile_id)
        
        # now check if we have any checked mines for game over
        self._check_validity()

    def _flag_tile(self, tile_id: int) -> None:

        # flip to flagged
        if self.tiles[tile_id].status == TILE_STATES[0]:
            print('flipping to flagged')
            self.tiles[tile_id].status = TILE_STATES[2]
            return
        
        # flip to question mark
        if self.tiles[tile_id].status == TILE_STATES[2]:
            print('flipping to question mark')
            self.tiles[tile_id].status = TILE_STATES[3]
            return
        
        # flip back to unchecked
        if self.tiles[tile_id].status == TILE_STATES[3]:
            print('unflagging tile')
            self.tiles[tile_id].status = TILE_STATES[0]
            return

    def print_board(self) -> None:
        """
        Used for text based console version only, prints a mock up board on the console
        """
        game_str = ''
        col_count = 0
        for tile in self.tiles:
            if col_count >= self.width:
                col_count = 0
                game_str += '\n'
            if tile.mine and tile.status == TILE_STATES[1]:
                game_str += '[X]'
            else:
                if tile.adjacent_mines > 0 and tile.status == TILE_STATES[1]: 
                    game_str += f'[{tile.adjacent_mines}]'
                else:
                    if tile.status == TILE_STATES[1]:
                        game_str += '[ ]'
                    else:
                        game_str += '[-]'
            col_count += 1

        print(game_str)
    
    def _create_tiles(self) -> None:
        """
        Creates all tile objects on the board
        """
        mine_count_temp = 0  # used to check to make sure we made the correct number of mines
        total_tiles = self.width * self.height
        mine_percent = self.mine_count / total_tiles
        row_count = 0
        col_count = 0
        for tile_id in range(total_tiles):
            if col_count > self.width-1:
                col_count = 0
                row_count += 1
            
            new_tile = Tile()
            new_tile.id = tile_id
            new_tile.row = row_count
            new_tile.col = col_count
            self.tiles.append(new_tile)
            col_count += 1

    def _assign_mines(self) -> None:
        self.tiles_with_mines = random.sample(range(0, len(self.tiles)-1), self.mine_count)
        for tile in self.tiles:
            if tile.id in self.tiles_with_mines:
                tile.mine = True

    def _map_neighbors(self) -> None:
        """ `
        tiles can have up to 8 neighbors
            c-1  c  c+1
        r-1 [0] [1] [2]
        r   [3] [t] [4]
        r+1 [5] [6] [7]

        """
        for tile in self.tiles:
            row = tile.row
            col = tile.col

            if tile.mine:
                continue

            if tile.id not in self.neighbors:
                self.neighbors[tile.id] = []

            for i in range(8):
                row_check = row + SHIFT[i][0]         
                col_check = col + SHIFT[i][1]

                # make sure the iterator falls outside of the board
                if 0 <= row_check < self.height and 0 <= col_check < self.width:
                    # get the id of the tile
                    neighboring_tile = self.get_tile_id_by_row_and_col(row_check, col_check)

                    if neighboring_tile is None:
                        continue

                    self.neighbors[tile.id].append(neighboring_tile)

            tile.adjacent_mines = len([neighboring_tile for neighboring_tile in self.neighbors[tile.id] if neighboring_tile in self.tiles_with_mines])

    def _find_zero_adjacent_neighboring_tiles(self, tile_id: int, maximum_iters: int = 1e7) -> None:
        """
        Clears out sections of connected tiles with no adjacent mines
        """
        tiles_to_check = [tile_id]
        current_iter = 0
        while True:
            # break out of the loop if we have checked them all
            if len(tiles_to_check) == 0:
                break

            # run time catch to avoid an infinite loop
            current_iter += 1                   
            if current_iter >= maximum_iters:
                raise RuntimeWarning(f'Exceeded runtime iterations of {maximum_iters} during _find_zero_adjacent_neighboring tiles_mod')  

            temp_list = []
            for tile_id in tiles_to_check:
                for neighbor_tile_id in self.neighbors[tile_id]:

                    # skip mines
                    if self.tiles[neighbor_tile_id].mine:
                        continue

                    # skip ones that have already been checked
                    if self.tiles[neighbor_tile_id].status == TILE_STATES[1]:
                        continue
 
                    # otherwise, check the tile and if it also has zero adjacent mines, add it to the temp list
                    self.tiles[neighbor_tile_id].status = TILE_STATES[1]
                    if self.tiles[neighbor_tile_id].adjacent_mines == 0:
                        temp_list.append(neighbor_tile_id)
            
            # reset the tiles to check and loop around
            tiles_to_check = temp_list

    def _check_validity(self):
        """
        Checks that we have not clicked a mine!
        """
        for tile in self.tiles:
            if tile.mine and tile.status == TILE_STATES[1]:
                self.valid = False
                break

    def _check_win(self):
        for mine_tile in self.tiles_with_mines:
            # if any mine tiles are not flagged, then we still have not won
            if self.tiles[mine_tile].status != TILE_STATES[2]:
                return
            
        self.user_won = True
        print('you won the game!')
        # check every other tile
        for tile in self.tiles:
            if not tile.mine and tile.status == TILE_STATES[0]:
                tile.status = TILE_STATES[1]
    

class Tile:
    id: int = 0                     # id of tile as position in board tile set
    mine: bool = False              # is the tile a mine
    pressed: bool = False           # if the current tile is pressed by the mouse
    status: str = TILE_STATES[0]    # state of the tile
    adjacent_mines: int = 0         # the number of adjacent mines
    row: int = 0                    # the row of the tile
    col: int = 0                    # the column of the tile
