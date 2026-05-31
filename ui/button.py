import pygame
from core.constants import *

class Button:
    def __init__(self, rect, text, callback):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.font = pygame.font.SysFont("arial", 28)
        self.hovered = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.callback()

    def draw(self, screen):
        if self.hovered:
            pygame.draw.rect(screen, LIGHT_GOLD, self.rect, border_radius=18)
        border_color = DARK_GOLD if self.hovered else LIGHT_BLACK
        border_width = 4
        pygame.draw.rect(screen, border_color, self.rect, border_width, border_radius=18)

        text_color = DIRTY_GOLD if self.hovered else LIGHT_BLACK
        text_surface = self.font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
