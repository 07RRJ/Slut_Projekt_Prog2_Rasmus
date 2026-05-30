import pygame
from core.constants import *

class CardView:
    WIDTH = 120
    HEIGHT = 180

    def __init__(self, card, x, y, selected=False):
        self.card = card
        self.rect = pygame.Rect(x, y, self.WIDTH, self.HEIGHT)
        self.selected = selected
        self.font = pygame.font.SysFont("arial", 24)

    def draw(self, screen):
        border_color = GOLD if self.selected else GRAY
        border_width = 4 if self.selected else 3
        pygame.draw.rect(screen, border_color, self.rect, border_width, border_radius=20)

        name = self.font.render(self.card.name[:8], True, DARK_GRAY)
        atk = self.font.render(str(self.card.attack), True, BLACK)
        hp = self.font.render(str(self.card.health), True, RED)

        screen.blit(name, (self.rect.x + 8, self.rect.y + 10))
        screen.blit(atk, (self.rect.x + 8, self.rect.bottom - 36))
        screen.blit(hp, (self.rect.right - 36, self.rect.bottom - 36))
