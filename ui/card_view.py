import pygame


class CardView:
    WIDTH = 120
    HEIGHT = 180

    def __init__(self, card, x, y):
        self.card = card
        self.rect = pygame.Rect(x, y, self.WIDTH, self.HEIGHT)
        self.font = pygame.font.SysFont("arial", 24)

    def draw(self, screen):
        pygame.draw.rect(screen, (140, 140, 140), self.rect, 4, border_radius=20)
        name = self.font.render(self.card.name, True, (100, 100, 100))
        atk = self.font.render(str(self.card.attack), True, (0, 0, 0))
        hp = self.font.render(str(self.card.health), True, (150, 0, 0))
        screen.blit(name, (self.rect.x + 20, self.rect.y + 20))
        screen.blit(atk, (self.rect.x + 20, self.rect.bottom - 40))
        screen.blit(hp, (self.rect.right - 40, self.rect.bottom - 40))