import pygame

BASE_WIDTH, BASE_HEIGHT = 1920, 1080
screen = pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
clock = pygame.time.Clock()

def LoadingScreen():
    for i in range(100):
        clock.tick(10)
        screen.fill((10, 10, 10))
        pygame.display.flip()