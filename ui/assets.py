import pygame
from logic.functions import ResourcePath

BASE_WIDTH, BASE_HEIGHT = 1920, 1080
screen = pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT), pygame.FULLSCREEN | pygame.SCALED)

MENU_PATH = "assets/img/menu/"
GAME_PATH = "assets/img/game/"
FONT_PATH = "assets/fonts/"

pygame.init()

class Assets:
    # COLOURS
    BLACK   = ((10, 10, 10), (50, 50, 50), (100, 100, 100), (150, 150, 150), (200, 200, 200), (250, 250, 250))
    RED     = ((100, 30, 30), (150, 50, 50), (200, 50, 50), (250, 75, 75))
    GREEN   = ((30, 100, 30), (30, 150, 30), (30, 200, 30), (50, 250, 50))
    BLUE    = ((30, 30, 100), (30, 30, 150), (30, 30, 200), (30, 30, 250), (173, 216, 230))
    YELLOW  = ((253, 253, 150), (255, 250, 50), (220, 220, 50), (250, 150, 0))

    # FONTS
    title_font_path = ResourcePath(FONT_PATH+"COPRGTB.TTF")
    text_font_path = ResourcePath(FONT_PATH+"corbelb.ttf")
    text_font_path1 = ResourcePath(FONT_PATH+"corbelb.ttf")

    title_font = pygame.font.Font(title_font_path, 64)
    text_font = pygame.font.Font(text_font_path, 24)
    text_font1 = pygame.font.Font(text_font_path1, 28)

    # IMGS
    MAIN_MENU = pygame.image.load(ResourcePath(MENU_PATH+"mainMenu.png")).convert_alpha()
    MAIN_MENU = pygame.transform.scale(MAIN_MENU, (BASE_WIDTH, BASE_HEIGHT))

    MENU = pygame.Rect(BASE_WIDTH//4, 0, BASE_WIDTH//2, BASE_HEIGHT)

    COMFIRM = pygame.Rect(BASE_WIDTH//4, BASE_HEIGHT//6, BASE_WIDTH//2, BASE_HEIGHT//3)

    # CARD_IMGS
    