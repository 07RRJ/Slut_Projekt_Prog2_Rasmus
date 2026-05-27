import pygame
from ui.assets import Assets, BASE_WIDTH, BASE_HEIGHT, screen

clock = pygame.time.Clock()

def LoadingScreen():
    # for i in range(100):
        # clock.tick(100)
    screen.blit(Assets.MAIN_MENU, (0, 0))
    pygame.display.flip()