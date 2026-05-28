import pygame, os, sys
from dataclasses import dataclass, field
from core.asset_manager import Assets, BASE_WIDTH, BASE_HEIGHT, screen

pygame.init()

assets = Assets()

def Text(text):
    return assets.text_font.render(text, True, (25, 25, 25))

class Bar:
    def __init__(self, colour, x, y, width, height, text, reverse=False):
        self.colour: tuple = colour
        self.x: float = x
        self.y: float = y
        self.width: int = width
        self.height: int = height
        self.text: tuple = text
        self.reverse: bool = reverse
        self.black: tuple = (10, 10, 10)

    def draw(self):
        if self.text:
            value = getattr(self.text[0], self.text[1])
            value1 = getattr(self.text[0], self.text[2])
            if value > value1:
                rect = pygame.Rect(self.x, self.y, self.width, self.height)
            else:
                rect = pygame.Rect(self.x, self.y, self.width*value//value1, self.height)
            pygame.draw.rect(screen, self.colour, rect)
            
            if self.reverse:
                text = Assets.text_font.render(f"{round(100-value, 2)}/{round(value1, 2)}", True, (self.black))
            else:
                text = Assets.text_font.render(f"{round(value, 2)}/{round(value1, 2)}", True, (self.black))
            screen.blit(text, text.get_rect(center=(self.x+self.width//2, self.y+self.height//2)))
        else:
            rect = pygame.Rect(self.x, self.y, self.width, self.height)
            pygame.draw.rect(screen, self.colour, rect)