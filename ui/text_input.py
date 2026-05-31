import pygame
from core.constants import *

class TextInput:
    def __init__(self, rect, placeholder="", password=False, font=None):
        self.rect = pygame.Rect(rect)
        self.placeholder = placeholder
        self.password = password
        self.font = font or pygame.font.SysFont("arial", 28)
        self.text = ""
        self.active = False
        self.disabled = False

    def handle_event(self, event):
        if self.disabled:
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key not in (pygame.K_RETURN, pygame.K_TAB):
                self.text += event.unicode

    def draw(self, screen):
        if self.disabled:
            pygame.draw.rect(screen, (180, 180, 180), self.rect, border_radius=8)
            pygame.draw.rect(screen, GRAY, self.rect, 2, border_radius=8)
            display = ("*" * len(self.text)) if self.password else self.text.upper()
            surf = self.font.render(display if display else self.placeholder, True, GRAY)
            screen.blit(surf, (self.rect.x + 10, self.rect.y + 8))
            return
        color = BLUE if self.active else GRAY
        pygame.draw.rect(screen, color, self.rect, 2, border_radius=8)
        display = ("*" * len(self.text)) if self.password else self.text.upper()
        surf = self.font.render(display if display else self.placeholder, True, BLACK if display else GRAY)
        screen.blit(surf, (self.rect.x + 10, self.rect.y + 8))
