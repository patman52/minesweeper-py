"""
settings.py

Contains settings, defaults and constants for minesweeper.py, controls user data and saving game data to external sqlite database

Author Paul Archer Tunis

"""

import ctypes
import json
import os
import sqlite3
from statistics import mean
from typing import Optional

MOUSE_LEFT = 1
MOUSE_RIGHT = 3

SCREEN_SIZE = ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1)
SCREEN_FILL = (200, 200, 200)
SETTING_FILL = (255, 255, 255)
SETTINGS_INSET = 10
MAX_SCREEN_RATIO = 0.6
DISPLAYS = ['game', 'settings']

# the colors for numbers showing the number of adjacent mines
NUM_TEXT_COLOUR = {
    1: (0, 0, 0),  # black
    2: (0, 255, 0), # green
    3: (0, 0, 255), # blue
    4: (255, 0, 0), # red
    5: (190, 115, 105), # tan-ish
    6: (130, 115, 180), # light-ish blue
    7: (50, 50, 110), # purple-ish
    8: (150, 150, 150) # grey-ish
}

# path to save database
SAVE_DATA_FILE = 'game data.db'

# height of the header containing the new game buttons, counters, and settings button
HEADER_HEIGHT = 70
TILE_MIN = 20
TILE_MAX = 80

# used to turn on and off segments in the seven segment counters, key is the digit, and value is a seven character string with 0s and 1s
# 0 = off, 1 = on
"""
    _a__
   f|  |b
    |  |
    _g___
   e|  |c
    |  |
    ____
    d
"""

SEGMENTS_TO_DISPLAY = {
    # digit: list of whether the segment is on or off [a, b, c, d, e, f, g]
    0: [True, True, True, True, True, True, False],
    1: [False, True, True, False, False, False, False],
    2: [True, True, False, True, True, False, True],
    3: [True, True, True, True, False, False, True],
    4: [False, True, True, False, False, True, True],
    5: [True, False, True, True, False, True, True],
    6: [True, False, True, True, True, True, True],
    7: [True, True, True, False, False, False, False],
    8: [True, True, True, True, True, True, True],
    9: [True, True, True, True, False, True, True]
}

COUNTER_WIDTH = 100
COUNTER_HEIGHT = HEADER_HEIGHT*0.8
SEGMENT_WIDTH = COUNTER_WIDTH*0.2
SEGMENT_GAP = SEGMENT_WIDTH*0.15
DIGIT_GAP = 5
TOTAL_DIGIT_HEIGHT = SEGMENT_GAP*3 + SEGMENT_WIDTH*2
TOTAL_DIGIT_WIDTH = SEGMENT_GAP*2 + SEGMENT_WIDTH
SETTINGS_BTN_PADX = 20
SETTING_BTN_WIDTH = 220
SLIDER_ICON_WIDTH = 25
SLIDER_HEIGHT=10

SEGMENT_POSITION_SIZE = {
    # segement_index: [x, y, rotate (true or false)]
    0: [SEGMENT_GAP, 0, False],
    1: [SEGMENT_WIDTH + SEGMENT_GAP, SEGMENT_GAP, True],
    2: [SEGMENT_WIDTH + SEGMENT_GAP, SEGMENT_WIDTH + SEGMENT_GAP*2, True],
    3: [SEGMENT_GAP, (SEGMENT_WIDTH + SEGMENT_GAP)*2, False],
    4: [0, SEGMENT_WIDTH + SEGMENT_GAP*2, True],
    5: [0, SEGMENT_GAP, True],
    6: [SEGMENT_GAP, SEGMENT_WIDTH + SEGMENT_GAP, False]
}

GAME_TYPES = ['easy', 'medium', 'hard', 'custom']

# default user and board settings
DEFAULTS = {
    'tile_size': 40,
    'last_game_played': 'easy',
    'board_sizes': {
        'easy': {
            'width': 15,
            'height': 10,
            'mines': 10
        },
        'medium': {
            'width': 25,
            'height': 15,
            'mines': 50  
        },
        'hard': {
            'width': 40,
            'height': 25,
            'mines': 100             
        },
        'custom': {
            'width': 40,
            'height': 25,
            'mines': 100 
        }
    },
}


class User:
    def __init__(self):
        self.user_stats: dict = {}
        self.tile_size: int = 0
        self.screen_fill: tuple = {}
        self.max_screen_ratio: float = 0.0
        self.board_sizes: dict = {}
        self.current_game: str = ''
        self.game_history: dict = {
            game_type: {'play_times': [], 'total_games': 0, 'won': 0, 'ave_playtime': 0.0, 'ratio': 0.0} for game_type in GAME_TYPES
        }

        # initialize user data
        self._load_save_data()

    def _load_save_data(self):          
        if not os.path.isfile(SAVE_DATA_FILE):
            self._create_database()

        self._load_user_settings()
        self._load_game_data()

    def _create_database(self):
        con = sqlite3.connect(SAVE_DATA_FILE)
        cur = con.cursor()

        # Create settings table
        settings_table_sql = """ CREATE TABLE SETTINGS (
            id INTEGER PRIMARY KEY,
            Tile_Size  INTEGER NOT NULL,
            Board_Sizes  TEXT NOT NULL,
            Last_Game_Played TEXT NOT NULL
        ); """

        cur.execute(settings_table_sql)

        # insert the default settings
        default_settings_sql = """ INSERT INTO SETTINGS (Tile_Size, Board_Sizes , Last_Game_Played) VALUES (?, ?, ?)"""
        cur.execute(default_settings_sql, (DEFAULTS['tile_size'], json.dumps(DEFAULTS['board_sizes']), DEFAULTS['last_game_played']))

        # create game save data table
        game_save_data_sql = """ CREATE TABLE GAME_DATA (
            id INTEGER PRIMARY KEY,
            Type  TEXT NOT NULL,
            Date  TEXT NOT NULL,
            Play_Time REAL NOT NULL,
            Won INTEGER NOT NULL
        ); """

        cur.execute(game_save_data_sql)
        con.commit()
        con.close()

    def _load_user_settings(self):
        con = sqlite3.connect(SAVE_DATA_FILE)
        cur = con.cursor()
        sql = 'SELECT * FROM SETTINGS'
        output = cur.execute(sql)
        cols = [col[0] for col in output.description]
        data = output.fetchone()
        self.tile_size = data[cols.index('Tile_Size')]
        self.board_sizes = json.loads(data[cols.index('Board_Sizes')])
        self.current_game = str(data[cols.index('Last_Game_Played')])
        con.close()

    def _load_game_data(self):
        con = sqlite3.connect(SAVE_DATA_FILE)
        cur = con.cursor()

        game_data_sql = 'SELECT * FROM GAME_DATA'
        output = cur.execute(game_data_sql)
        cols = [col[0] for col in output.description]
        game_data = output.fetchall()

        for game in game_data:
            type = str(game[cols.index('Type')]) 
            if type not in GAME_TYPES:
                raise ValueError(f'game type {type} not supported, must be {GAME_TYPES}')
            self.game_history[type]['play_times'].append(float(game[cols.index('Play_Time')]))
            self.game_history[type]['total_games'] += 1
            self.game_history[type]['won'] += int(game[cols.index('Won')])

    def save_game(self, type: str, date_played: str, play_time: float, win: bool):
        self.game_history[type]['play_times'].append(play_time)
        self.game_history[type]['total_games'] += 1
        self.game_history[type]['won'] += int(win)
        self.get_calc_stats()
        con = sqlite3.connect(SAVE_DATA_FILE)
        cur = con.cursor()
        sql = 'INSERT INTO GAME_DATA (Type, Date, Play_Time, Won) VALUES (?, ?, ?, ?)'
        cur.execute(sql, (type, date_played, play_time, int(win)))
        con.commit()
        con.close

    def reset_stats(self):
        """
        Deletes all saved game data
        """
        self.game_history: dict = {
            game_type: {'play_times': [], 'total_games': 0, 'won': 0, 'ave_playtime': 0.0, 'ratio': 0.0} for game_type in GAME_TYPES
        }
        con = sqlite3.connect(SAVE_DATA_FILE)
        cur = con.cursor()
        cur.execute('DELETE FROM GAME_DATA')
        con.commit()
        con.close()

    def get_calc_stats(self):
        for type, game_data in self.game_history.items():
            game_data['ave_playtime'] = mean(game_data['play_times']) if len(game_data['play_times']) > 0 else 0.0
            game_data['ratio'] = game_data['won'] / game_data['total_games'] if game_data['total_games'] > 0 else 0.0

    def get_current_game_specs(self, game_type: Optional[str] = None):

        if game_type is None:
            game_type = self.current_game
        else:
            if game_type not in GAME_TYPES:
                raise ValueError(f'game_type {game_type} does not match available game types {GAME_TYPES}')
        
        width = self.board_sizes[game_type]['width']
        height = self.board_sizes[game_type]['height']
        mines = self.board_sizes[game_type]['mines']

        return width, height, mines

    def update_settings(self, width: int, height: int, mines: int) -> None:
        self.board_sizes['custom']['width'] = width
        self.board_sizes['custom']['height'] = height
        self.board_sizes['custom']['mines'] = mines
        con = sqlite3.connect(SAVE_DATA_FILE)
        cur = con.cursor()
        cur.execute('UPDATE SETTINGS SET Board_Sizes = ?, Last_Game_Played = ?', (json.dumps(self.board_sizes), 'custom'))
        con.commit()
        con.close()
