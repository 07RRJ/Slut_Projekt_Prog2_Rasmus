import pygame, os, sys
from dataclasses import dataclass, field
from ui.assets import Assets, BASE_WIDTH, BASE_HEIGHT, screen

pygame.init()

assets = Assets()

@dataclass(slots=True)
class Button:
    BaseImg: pygame.Surface | None = None
    SelectedImg: pygame.Surface | None = None
    Text: str | None = None
    Rect: pygame.Rect | None = None
    Pos: tuple | None = None
    Font: pygame.font.Font | None = None
    Colour: tuple[int, int, int] | None = None

    baseImg: pygame.Surface | None = field(init=False, default=None)
    selectedImg: pygame.Surface | None = field(init=False, default=None)
    text: str | None = field(init=False, default=None)
    rect: pygame.Rect | None = field(init=False, default=None)
    pos: tuple | None = field(init=False, default=None)
    font: pygame.font.Font | None = field(init=False, default=None)
    colour: tuple[int, int, int] | None = field(init=False, default=None)
    label: pygame.Surface | None = field(init=False, default=None)
    labelRect: pygame.Rect | None = field(init=False, default=None)

    def __post_init__(self):
        self.baseImg = self.BaseImg
        self.selectedImg = self.SelectedImg

        if self.baseImg is not None and self.selectedImg is not None:
            self.pos = self.Pos if self.Pos is not None else (0, 0)
            self.rect = self.baseImg.get_rect(topleft=self.pos)
            return

        self.text = self.Text or ""
        self.rect = self.Rect
        self.font = self.Font
        self.colour = self.Colour if self.Colour is not None else (200, 200, 200)

        if self.font is None or self.rect is None:
            raise ValueError("Text buttons need Rect and Font")

        self.label = self.font.render(self.text, True, (255, 255, 255))
        self.labelRect = self.label.get_rect(center=self.rect.center)

    def draw(self, is_selected=False):
        if self.baseImg is not None:
            img = self.selectedImg if is_selected else self.baseImg
            screen.blit(img, self.rect)
            return

        if is_selected:
            highlight_rect = self.rect.inflate(12, 12)
            pygame.draw.rect(screen, (255, 200, 0), highlight_rect, border_radius=8)

        pygame.draw.rect(screen, self.colour, self.rect, border_radius=8)
        screen.blit(self.label, self.labelRect)

def Text(text):
    return assets.text_font.render(text, True, (25, 25, 25))

class Bar:
    def __init__(self, colour, x, y, width, height, text, reverse=False):
        self.colour: tuple = colour
        self.x: float = x
        self.y: float = y
        self.width: int = width
        self.height: int = height
        self.text: tuple = text
        self.reverse: bool = reverse
        self.black: tuple = (10, 10, 10)

    def draw(self):
        if self.text:
            value = getattr(self.text[0], self.text[1])
            value1 = getattr(self.text[0], self.text[2])
            if value > value1:
                rect = pygame.Rect(self.x, self.y, self.width, self.height)
            else:
                rect = pygame.Rect(self.x, self.y, self.width*value//value1, self.height)
            pygame.draw.rect(screen, self.colour, rect)
            
            if self.reverse:
                text = Assets.text_font.render(f"{round(100-value, 2)}/{round(value1, 2)}", True, (self.black))
            else:
                text = Assets.text_font.render(f"{round(value, 2)}/{round(value1, 2)}", True, (self.black))
            screen.blit(text, text.get_rect(center=(self.x+self.width//2, self.y+self.height//2)))
        else:
            rect = pygame.Rect(self.x, self.y, self.width, self.height)
            pygame.draw.rect(screen, self.colour, rect)