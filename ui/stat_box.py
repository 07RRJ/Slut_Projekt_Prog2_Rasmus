import pygame
from core.constants import *

class StatBox:
    def __init__(self, state):
        self.state = state

        self.rect = pygame.Rect(BASE_WIDTH - 330, BASE_HEIGHT - 150, 300, 120)

        self.font = pygame.font.SysFont("arial", 32)

    def draw(self, screen):
        pygame.draw.rect(screen, (140, 140, 140), self.rect, 4, border_radius=30)

        username = self.font.render(self.state.username, True, BLACK)

        turn = self.font.render(f"turn: {self.state.turn}", True, BLACK)

        hp = self.font.render(f"health: {self.state.health}", True, (140, 0, 0))

        gold = self.font.render(f"gold: {self.state.gold}", True, GOLD)

        screen.blit(username, (970, 590))
        screen.blit(turn, (1120, 590))
        screen.blit(hp, (970, 640))
        screen.blit(gold, (1170, 640))