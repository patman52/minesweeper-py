"""
button.py

Button objects and data for minesweeper, helps determine if a button was pressed based on size, shape, and position

Author Paul Archer Tunis
"""

from math import sqrt
from settings import *
from typing import Optional

class Button:
    def __init__(self, name:str, image_normal: 'pygame.image', image_pressed: Optional['pygame.image'] = None, 
                 image_secondary: Optional['pygame.image'] = None, shape: str = BUTTON_SHAPES[0],
                 display: str = DISPLAYS[0], pos: list[float] = [0.0, 0.0], center: tuple[bool] = (True, True),
                 text_to_display: None | str = None):
        self.name: str = name
        self.image_normal: 'pygame.image' = image_normal
        self.image_pressed: None | 'pygame.image'  = image_pressed
        self.image_secondary: None | 'pygame.image' = image_secondary
        self.display: str = display
        self.size: tuple[float] =(self.image_normal.get_width(), self.image_normal.get_height())
        self.pos: list[float] = pos
        if center[0]:
            self.pos[0] -= self.size[0]/2
        if center[1]:
            self.pos[1] -= self.size[1]/2
        self.shape: str = shape
        text_to_display: None | str = text_to_display
        
    def check_pressed(self, point: tuple[float]) -> bool:
        if self.shape == BUTTON_SHAPES[0]:
            return self._determine_point_in_rectangle(point)
        elif self.shape == BUTTON_SHAPES[1]:
            return self._determine_point_in_circle(point)
        else:
            raise ValueError(f'Button shape incorrectly defined, must be {BUTTON_SHAPES}')

    def get_bounding_box(self) -> tuple[float]:
        return (self.pos[0], self.pos[1], self.size[0], self.size[1])

    def _determine_point_in_rectangle(self, point: tuple[float]) -> bool:
        return self.pos[0] < point[0] < self.pos[0] + self.size[0] and self.pos[1] < point[1] < self.pos[1] + self.size[1]

    def _determine_point_in_circle(self, point: tuple[float]) -> bool:
        """ 
        finding if a point is in a circle
        (x - center_x)² + (y - center_y)² < radius².
        """
        return sqrt((point[0] - (self.pos[0] + self.size[0]/2))**2 + (point[1] - (self.pos[1] + self.size[0]/2))**2) < self.size[0]/2
