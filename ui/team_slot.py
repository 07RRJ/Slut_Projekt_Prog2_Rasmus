import pygame

class TeamSlot:
    WIDTH = 120
    HEIGHT = 180

    def __init__(self, x, y, index):
        self.index = index

        self.rect = pygame.Rect(x, y, self.WIDTH, self.HEIGHT)

        self.font = pygame.font.SysFont("arial", 42)

    def draw(self, screen):
        pygame.draw.rect(screen, (140, 140, 140), self.rect, 4, border_radius=20)

        text = self.font.render(str(self.index + 1), True, (140, 140, 140))

        text_rect = text.get_rect(center=self.rect.center)

        screen.blit(text, text_rect)