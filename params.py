
import ctypes
import json
import os

MOUSE_LEFT = 1
MOUSE_RIGHT = 3

SCREEN_SIZE = ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1)

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

SAVE_DATA_FILE = r'user data.json'

DEFAULTS = {
    'screen_fill': [200, 200, 200],
    'tile_size': 40,
    'max_screen_ratio': 0.7,
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
        }
    },
    'user_stats': {
        'easy': {
            'wins': 0,
            'losses': 0,
            'fastest_game': 0.0
        },
        'medium': {
            'wins': 0,
            'losses': 0,
            'fastest_game': 0.0
        },
        'hard': {
            'wins': 0,
            'losses': 0,
            'fastest_game': 0.0
        },
        'custom': {
            'wins': 0,
            'losses': 0,
            'fastest_game': 0.0
        }
    }
}


class User:
    def __init__(self):
        self.user_stats: dict = {}
        self.tile_size: int = 0
        self.screen_fill: tuple = {}
        self.max_screen_ratio: float = 0.0
        self.board_sizes: dict = {}
        self.current_game: str = ''

        # initialize user data
        self._load_save_data()

    def _load_save_data(self):          
        if not os.path.isfile(SAVE_DATA_FILE):
            with open(SAVE_DATA_FILE, 'w') as f:
                f.write(json.dumps(DEFAULTS))
            os.system("attrib +h {SAVE_DATA_FILE)")
        
        with open(SAVE_DATA_FILE, 'r') as f:
            data = json.load(f)

        self._assign_user_params(data)

    def _assign_user_params(self, data):
        self.user_stats = data['user_stats']
        self.screen_fill = tuple(data['screen_fill'])
        self.tile_size = int(data['tile_size'])
        self.max_screen_ratio = float(data['max_screen_ratio'])
        self.board_sizes = data['board_sizes']
        self.current_game = data['last_game_played']
