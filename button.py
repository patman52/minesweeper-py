"""
button.py

Button objects and data for minesweeper, helps determine if a button was pressed based on size, shape, and position

Author Paul Archer Tunis
"""

from math import sqrt
from settings import *
from typing import Optional

BUTTON_SHAPES = ['rect', 'cir']


class Button:
    def __init__(self, name:str, image_normal: 'pygame.Surface', image_pressed: Optional['pygame.Surface'] = None, 
                 image_game_over: Optional['pygame.Surface'] = None, shape: str = BUTTON_SHAPES[0],
                 display: str = DISPLAYS[0], pos: list[float] = [0.0, 0.0], center: tuple[bool] = (True, True),
                 text_to_display: Optional[str] = None, text_size: Optional[int] = None, font: Optional[str] = None,
                 text_color: tuple = (0, 0, 0)):
        self.name: str = name
        self.image_normal: 'pygame.image' = image_normal
        if image_pressed is None:
            self.image_pressed: 'pygame.image' = self.image_normal
        else:
            self.image_pressed = image_pressed
        if image_game_over is None:
            self.image_game_over: 'pygame.image' = self.image_normal
        else:
            self.image_game_over = image_game_over
        self.display: str = display
        self.size: tuple[float] =(self.image_normal.get_width(), self.image_normal.get_height())
        self.pos: list[float] = pos
        if center[0]:
            self.pos[0] -= self.size[0]/2
        if center[1]:
            self.pos[1] -= self.size[1]/2
        if shape not in BUTTON_SHAPES:
            raise ValueError(f'button shape specified must be {BUTTON_SHAPES}')
        self.shape: str = shape
        self.text_to_display: None | str = text_to_display
        self.text_size: None | int = text_size 
        self.font: None | str = font
        self.text_color: tuple = text_color
        self.pressed: bool = False
        
    def check_collide(self, point: tuple[float], flip: bool = False) -> bool:
        if self.shape == BUTTON_SHAPES[0]:
            if self._determine_point_in_rectangle(point):
                if flip:
                    self.pressed = not self.pressed
                else:
                    self.pressed = True
                return True
        elif self.shape == BUTTON_SHAPES[1]:
            if self._determine_point_in_circle(point):
                if flip:
                    self.pressed = not self.pressed
                else:
                    self.pressed = True
                return True
        return False

    def get_bounding_box(self) -> tuple[float, float, float, float]:
        return (self.pos[0], self.pos[1], self.size[0], self.size[1])

    def _determine_point_in_rectangle(self, point: tuple[float]) -> bool:
        return self.pos[0] < point[0] < self.pos[0] + self.size[0] and self.pos[1] < point[1] < self.pos[1] + self.size[1]

    def _determine_point_in_circle(self, point: tuple[float]) -> bool:
        """ 
        finding if a point is in a circle
        (x - center_x)² + (y - center_y)² < radius².
        """
        return sqrt((point[0] - (self.pos[0] + self.size[0]/2))**2 + (point[1] - (self.pos[1] + self.size[0]/2))**2) < self.size[0]/2

