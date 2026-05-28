import pygame

class Button:
    def __init__(self, rect, text, callback):
        self.rect = pygame.Rect(rect)

        self.text = text
        self.callback = callback

        self.font = pygame.font.SysFont("arial", 28)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.callback()

    def draw(self, screen):
        pygame.draw.rect(screen, (0, 0, 0), self.rect, 4, border_radius=18)

        text_surface = self.font.render(self.text, True, (0, 0, 0))

        text_rect = text_surface.get_rect(center=self.rect.center)

        screen.blit(text_surface, text_rect)