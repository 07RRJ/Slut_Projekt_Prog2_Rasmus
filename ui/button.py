import pygame

class Button:
    def __init__(self, rect, text, callback):
        self.rect     = pygame.Rect(rect)
        self.text     = text
        self.callback = callback
        self.font     = pygame.font.SysFont("arial", 28)
        self.hovered  = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.callback()

    def draw(self, screen):
        # Fill with a subtle highlight when hovered
        if self.hovered:
            pygame.draw.rect(screen, (220, 210, 170), self.rect, border_radius=18)  # warm gold tint
        border_color = (180, 140, 10) if self.hovered else (40, 40, 40)
        border_width = 4
        pygame.draw.rect(screen, border_color, self.rect, border_width, border_radius=18)

        text_color   = (140, 100, 0) if self.hovered else (40, 40, 40)
        text_surface = self.font.render(self.text, True, text_color)
        text_rect    = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
