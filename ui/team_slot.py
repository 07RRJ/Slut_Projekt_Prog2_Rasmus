import pygame
from core.constants import *

class TeamSlot:
    WIDTH  = 120
    HEIGHT = 180

    def __init__(self, x, y, index):
        self.index = index
        self.rect  = pygame.Rect(x, y, self.WIDTH, self.HEIGHT)
        self.font  = pygame.font.SysFont("arial", 28)
        self.small = pygame.font.SysFont("arial", 20)

    def draw(self, screen, card=None):
        pygame.draw.rect(screen, GRAY, self.rect, 3, border_radius=20)

        if card:
            # Card name
            name = self.font.render(card.name[:8], True, BLACK)
            screen.blit(name, (self.rect.x + 8, self.rect.y + 10))

            # Attack (bottom-left)
            atk = self.font.render(str(card.attack), True, BLACK)
            screen.blit(atk, (self.rect.x + 8, self.rect.bottom - 36))

            # Health (bottom-right, red)
            hp = self.font.render(str(card.health), True, RED)
            screen.blit(hp, (self.rect.right - 36, self.rect.bottom - 36))

            # Level dots
            for i in range(card.level):
                pygame.draw.circle(screen, GOLD,
                    (self.rect.x + 12 + i * 16, self.rect.y + self.HEIGHT - 50), 6)

            # Sell hint (right-click)
            hint = self.small.render("RMB sell", True, GRAY)
            screen.blit(hint, (self.rect.x + 4, self.rect.y + self.HEIGHT // 2))
        else:
            # Empty slot — just show slot number
            num = pygame.font.SysFont("arial", 42).render(str(self.index + 1), True, GRAY)
            screen.blit(num, num.get_rect(center=self.rect.center))
