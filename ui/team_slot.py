import pygame
from core.constants import *

class TeamSlot:
    WIDTH  = 120
    HEIGHT = 180

    def __init__(self, x, y, index):
        self.index = index
        self.rect  = pygame.Rect(x, y, self.WIDTH, self.HEIGHT)
        self.font  = pygame.font.SysFont("arial", 24)
        self.small = pygame.font.SysFont("arial", 18)

    def draw(self, screen, card=None, highlight=False, hidden=False):
        """
        highlight  – gold border (battle: this card is the active attacker)
        hidden     – card defeated, draw empty slot
        """
        if hidden or card is None:
            color = GRAY
            pygame.draw.rect(screen, color, self.rect, 3, border_radius=20)
            if not hidden:
                num = pygame.font.SysFont("arial", 42).render(
                    str(self.index + 1), True, GRAY
                )
                screen.blit(num, num.get_rect(center=self.rect.center))
            return

        border_color = GOLD if highlight else GRAY
        border_width = 8    if highlight else 3
        pygame.draw.rect(screen, border_color, self.rect, border_width, border_radius=20)

        name = self.font.render(card.name[:8], True, BLACK)
        atk  = self.font.render(str(card.attack), True, BLACK)
        hp   = self.font.render(str(max(card.health, 0)), True, RED)
        spd  = self.small.render(f"spd {card.speed}", True, BLUE)

        screen.blit(name, (self.rect.x + 8, self.rect.y + 10))
        screen.blit(atk,  (self.rect.x + 8, self.rect.bottom - 36))
        screen.blit(hp,   (self.rect.right - 40, self.rect.bottom - 36))
        screen.blit(spd,  (self.rect.x + 8, self.rect.bottom - 58))

        for i in range(card.level):
            pygame.draw.circle(
                screen, GOLD,
                (self.rect.x + 12 + i * 16, self.rect.y + self.HEIGHT - 70), 6
            )

        hint = self.small.render("RMB sell", True, GRAY)
        screen.blit(hint, (self.rect.x + 4, self.rect.y + self.HEIGHT // 2))
