import pygame
from core.constants import *

class StatBox:
    def __init__(self, state):
        self.state = state

        self.rect = pygame.Rect(WIDTH_WITH_MARGIN - 500, HEIGHT_WITH_MARGIN - 200, 500, 200)

        self.font = pygame.font.SysFont("arial", 32)

    def draw(self, screen):
        pygame.draw.rect(screen, (140, 140, 140), self.rect, 4, border_radius=30)

        username = self.font.render(self.state.username, True, BLACK)
        turn = self.font.render(f"turn: {self.state.turn}", True, BLACK)
        hp = self.font.render(f"health: {self.state.health}", True, (140, 0, 0))
        gold = self.font.render(f"gold: {self.state.gold}", True, GOLD)

        screen.blit(username, (self.rect.x + PADDING, self.rect.y + PADDING))
        screen.blit(turn, (self.rect.right - turn.get_width() - PADDING, self.rect.y + PADDING))
        screen.blit(hp, (self.rect.x + PADDING, self.rect.bottom - hp.get_height() - PADDING))
        screen.blit(gold, (self.rect.right - gold.get_width() - PADDING, self.rect.bottom - gold.get_height() - PADDING))