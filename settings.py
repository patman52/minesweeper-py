
import ctypes
import datetime
import json
import os
import sqlite3

MOUSE_LEFT = 1
MOUSE_RIGHT = 3

SCREEN_SIZE = ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1)
SCREEN_FILL = (200, 200, 200)
MAX_SCREEN_RATION = 0.7

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
SAVE_DATA_FILE = r'game data.db'

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

SEVEN_SEGMENT_DISPLAY = {
    0: '1111110',
    1: '0110000',
    2: '1101101',
    3: '1111001',
    4: '0110011',
    5: '1011011',
    6: '1011111',
    7: '1110000',
    8: '1111111',
    9: '1111011'
}

GAME_TYPES = ['easy', 'medium', 'hard', 'custom']

# template to save previous game data
SAVE_GAME = {
    'type': '',
    'date_played': '',
    'play_time': 0.0,
    'won': False
}

# default user and board settings
DEFAULTS = {
    'tile_size': 40,
    'last_game_played': 'medium',
    'board_sizes': {
        'easy': {
            'width': 15,
            'height': 10,
            'mines': 20
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
    'game_history': [] # list of games and associated data
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
            game_type: {'play_times': [], 'total_games': 0, 'won': 0} for game_type in GAME_TYPES
        }

        # initialize user data
        self._load_save_data()

    def _load_save_data(self):          
        if not os.path.isfile(SAVE_DATA_FILE):
            self._create_database()
        #     with open(SAVE_DATA_FILE, 'w') as f:
        #         f.write(json.dumps(DEFAULTS))
        #     os.system("attrib +h {SAVE_DATA_FILE)")
        
        # with open(SAVE_DATA_FILE, 'r') as f:
        #     data = json.load(f)

        self._load_user_settings()

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
        self.tile_size = data[cols.index['Tile_Size']]
        self.board_sizes = json.loads(cols.index['Board_Sizes'])
        self.current_game = str(data[cols.index['Last_Game_Played']])
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
            self.game_history[type]['play_times'].append(float(game[cols.index['Play_Time']]))
            self.game_history[type]['total_games'] += 1
            self.game_history[type['won']] += int(game[cols.index['Won']])

    def save_game(self, type: str, date_played: str, play_time: float, win: bool):
        con = sqlite3.connect(SAVE_DATA_FILE)
        cur = con.cursor()
        sql = 'INSERT INTO GAME_DATA (Type, Date, Play_Time, Won) VALUES (?, ?, ?, ?)'
        cur.execute(sql, (type, date_played, play_time, int(win)))
        con.commit()
        con.close
