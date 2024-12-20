
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

        # check that the number of mines does not exceed the total tiles
        if self.mine_count / (self.width * self.height) > MAX_MINE_SHARE:
            raise ValueError(f'mines cannot exceed {MAX_MINE_SHARE*100}% of total board tiles!\n'
                             f'Current mines: {self.mine_count}, total tiles: {self.width*self.height}')

    def setup(self) -> None:
        """
        Start a new game board
        """
        self.clear_board()
        self._create_tiles()
        self._assign_mines()
        self._map_neighbors()

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
    
    def click_tile(self, **kwargs) -> bool | None:
        """
        click a tile, keyword parameters can be:
            tile_id -> the index of the tile in the tiles list
            row -> the row of the tile indexed to 0
            col -> the col of the tile indexed to 0
        """

        if 'tile_id' in kwargs:
            tile_id = int(kwargs['tile_id'])
        elif 'row' in kwargs and 'col' in kwargs:
            row = int(kwargs['row'])
            col = int(kwargs['col'])
            tile_id = self.get_tile_id_by_row_and_col(row, col)

            if tile_id is None:
                print('No matching row or coloumn on game board!')
                return None            
        else:
            raise ValueError('You must specify either a tile id, or a row and col pair')

        # if the tile is flagged on question mark, or already checked then clicking does nothing
        if self.tiles[tile_id].status != TILE_STATES[0]:
            return None
        
        # else we change the status to checked
        self.tiles[tile_id].status = TILE_STATES[1]
        
        # if its a mine, then game over
        if self.tiles[tile_id].mine:
            print('YOU CLICKED A MINE!')
            return True
        
        # if the tile has zero adjacent mines, we need to clear out all neighboring zero adjancent mine tiles
        if self.tiles[tile_id].adjacent_mines == 0:
            self._find_zero_adjacent_neighboring_tiles(tile_id)
        
        self._check_validity()

        return False

    def flag_tile(self, tile_id: int) -> None:
        """
        param: tile_id - index of tile in self.tiles list we are flagging
        """
        # flip to flagged
        if self.tiles[tile_id].status == TILE_STATES[0]:
            self.tiles[tile_id].status = TILE_STATES[2]
            return
        
        # flip to question mark
        if self.tiles[tile_id].status == TILE_STATES[2]:
            self.tiles[tile_id].status = TILE_STATES[3]
            return
        
        # flip back to unchecked
        if self.tiles[tile_id].status == TILE_STATES[3]:
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

            print(f'created tile {tile_id}, row = {row_count}, col = {col_count}')

    def _assign_mines(self) -> None:
        self.tiles_with_mines = random.sample(range(0, len(self.tiles)-1), self.mine_count)
        for tile in self.tiles:
            if tile.id in self.tiles_with_mines:
                tile.mine = True
            

    def _map_neighbors(self) -> None:
        """ 
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

    def _find_zero_adjacent_neighboring_tiles(self, tile_id: int) -> None:
        """
        Recursive function to clear out section of tiles with no adjacent mines
        param: tile_id - the index of the tile in the self.tiles list we are checking for neighbors
        """

        # get a list of all neighboring tiles
        neighbor_tiles = self.neighbors[tile_id]

        # loop through tiles and if they have zero adjacent tiles and are not checked, change the status to checked
        for neighbor_tile_id in neighbor_tiles:
            # skip mines
            if self.tiles[neighbor_tile_id].mine:
                continue
            # skip tiles with adjancent mines
            if self.tiles[neighbor_tile_id].adjacent_mines > 0:
                continue
            # skip ones that have already been checked
            if self.tiles[neighbor_tile_id].status == TILE_STATES[1]:
                continue

            # if we find one that doesn't get filtered out based on the criteria above, change the status to checked and then check
            # its adjacent tiles
            self.tiles[neighbor_tile_id].status = TILE_STATES[1]
            self._find_zero_adjacent_neighboring_tiles(neighbor_tile_id)

                
    def _check_validity(self):
        """
        Checks that we have not clicked a mine!
        """
        for tile in self.tiles:
            if tile.mine and tile.status == TILE_STATES[1]:
                self.valid = False


class Tile:
    id: int = 0                     # id of tile as position in board tile set
    mine: bool = False              # is the tile a mine
    status: str = TILE_STATES[0]    # state of the tile
    adjacent_mines: int = 0         # the number of adjacent mines
    row: int = 0                    # the row of the tile
    col: int = 0                    # the column of the tile
