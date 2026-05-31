import pygame
from core.constants import *

class CardView:
    WIDTH = CARD_W
    HEIGHT = CARD_H

    def __init__(self, card, x, y, selected=False, greyed=False):
        self.card = card
        self.rect = pygame.Rect(x, y, self.WIDTH, self.HEIGHT)
        self.selected = selected
        self.greyed = greyed
        self.font = pygame.font.SysFont("arial", 22)
        self.small = pygame.font.SysFont("arial", 18)

    def draw(self, screen):
        if self.greyed:
            pygame.draw.rect(screen, LIGHT_GRAY, self.rect, border_radius=20)
            pygame.draw.rect(screen, GRAY, self.rect, 3, border_radius=20)
            sold = self.font.render("SOLD", True, GRAY)
            screen.blit(sold, sold.get_rect(center=self.rect.center))
            return

        border_color = GOLD if self.selected else GRAY
        border_width = 6 if self.selected else 3
        pygame.draw.rect(screen, border_color, self.rect, border_width, border_radius=20)

        name = self.font.render(self.card.name[:8], True, DARK_GRAY)
        atk = self.font.render(str(self.card.attack), True, BLACK)
        hp = self.font.render(str(self.card.health), True, RED)
        spd = self.small.render(f"spd {self.card.speed}", True, BLUE)

        screen.blit(name, (self.rect.x + 8, self.rect.y + 10))
        screen.blit(atk, (self.rect.x + 8, self.rect.bottom - 36))
        screen.blit(hp, (self.rect.right - 40, self.rect.bottom - 36))
        screen.blit(spd, (self.rect.x + 8, self.rect.bottom - 58))

class StatUpVeiw:
    WIDTH = CARD_W
    HEIGHT = CARD_H

    def __init__(self, stat_up: tuple, x: int, y: int, selected: bool = False, greyed: bool = False):
        self.stat_up = stat_up
        self.rect = pygame.Rect(x, y, self.WIDTH, self.HEIGHT)
        self.selected = selected
        self.greyed = greyed
        self.font = pygame.font.SysFont("arial", 22)
        self.small = pygame.font.SysFont("arial", 18)

    def draw(self, screen):
        if self.greyed:
            pygame.draw.rect(screen, LIGHT_GRAY, self.rect, border_radius=20)
            pygame.draw.rect(screen, GRAY, self.rect, 3, border_radius=20)
            sold = self.font.render("SOLD", True, GRAY)
            screen.blit(sold, sold.get_rect(center=self.rect.center))
            return

        border_color = GOLD if self.selected else BLUE
        border_width = 6 if self.selected else 3
        pygame.draw.rect(screen, border_color, self.rect, border_width, border_radius=20)

        label = self.font.render(self.stat_up.label, True, BLACK)
        cost = self.font.render(f"{self.stat_up.cost}g", True, GOLD)
        screen.blit(label, label.get_rect(center=(self.rect.centerx, self.rect.centery - 16)))
        screen.blit(cost, cost.get_rect( center=(self.rect.centerx, self.rect.centery + 20)))

def my_slot_x(slot_index: int) -> int:
    return MARGIN + slot_index * (CARD_W + CARD_GAP)

def my_slot_y() -> int:
    return BASE_HEIGHT - CARD_H - MARGIN

def opp_slot_x(slot_index: int) -> int:
    return BASE_WIDTH - MARGIN - CARD_W - slot_index * (CARD_W + CARD_GAP)

def opp_slot_y() -> int:
    return MARGIN