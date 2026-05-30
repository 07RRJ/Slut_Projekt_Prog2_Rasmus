import pygame
from core.constants import *

class CardView:
    WIDTH  = 120
    HEIGHT = 180

    def __init__(self, card, x, y, selected=False, greyed=False):
        self.card     = card
        self.rect     = pygame.Rect(x, y, self.WIDTH, self.HEIGHT)
        self.selected = selected
        self.greyed   = greyed
        self.font     = pygame.font.SysFont("arial", 22)
        self.small    = pygame.font.SysFont("arial", 18)

    def draw(self, screen):
        if self.greyed:
            # Bought-out card: dim overlay
            pygame.draw.rect(screen, (180, 180, 180), self.rect, border_radius=20)
            pygame.draw.rect(screen, GRAY, self.rect, 3, border_radius=20)
            sold = self.font.render("SOLD", True, GRAY)
            screen.blit(sold, sold.get_rect(center=self.rect.center))
            return

        border_color = GOLD if self.selected else GRAY
        border_width = 6   if self.selected else 3
        pygame.draw.rect(screen, border_color, self.rect, border_width, border_radius=20)

        name  = self.font.render(self.card.name[:8], True, DARK_GRAY)
        atk   = self.font.render(str(self.card.attack), True, BLACK)
        hp    = self.font.render(str(self.card.health), True, RED)
        spd   = self.small.render(f"spd {self.card.speed}", True, BLUE)

        screen.blit(name, (self.rect.x + 8,           self.rect.y + 10))
        screen.blit(atk,  (self.rect.x + 8,           self.rect.bottom - 36))
        screen.blit(hp,   (self.rect.right - 40,       self.rect.bottom - 36))
        screen.blit(spd,  (self.rect.x + 8,           self.rect.bottom - 58))
