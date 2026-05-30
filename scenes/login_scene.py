import pygame
import bcrypt
from scenes.base_scene import BaseScene
from ui.button import Button
from core.constants import *

class TextInput:
    def __init__(self, rect, placeholder="", password=False, font=None):
        self.rect = pygame.Rect(rect)
        self.placeholder = placeholder
        self.password = password
        self.font = font or pygame.font.SysFont("arial", 28)
        self.text = ""
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key not in (pygame.K_RETURN, pygame.K_TAB):
                self.text += event.unicode

    def draw(self, screen):
        color = BLUE if self.active else GRAY
        pygame.draw.rect(screen, color, self.rect, 2, border_radius=8)
        display = ("*" * len(self.text)) if self.password else self.text.upper()
        if display:
            surf = self.font.render(display, True, BLACK)
        else:
            surf = self.font.render(self.placeholder, True, GRAY)
        screen.blit(surf, (self.rect.x + 10, self.rect.y + 8))

class LoginScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        self.font = game.assets.get_font("body")
        self.title = game.assets.get_font("title")
        self.error = ""

        self.username_input = TextInput((MIDDLE_WIDTH - 200, 380, 400, 50), "Username", font=self.font)
        self.password_input = TextInput((MIDDLE_WIDTH - 200, 460, 400, 50), "Password", password=True, font=self.font)

        self.login_btn = Button((MIDDLE_WIDTH - 200, 550, 190, 60), "LOGIN", self.do_login)
        self.back_btn = Button((MIDDLE_WIDTH + 10, 550, 190, 60), "BACK", self.back)

    def do_login(self):
        username = self.username_input.text.strip()
        password = self.password_input.text.encode()
        if not username or not password:
            self.error = "Please fill in both fields"
            return

        user = self.game.db.login(username)
        if not user:
            self.error = "User not found"
            return
        if not bcrypt.checkpw(password, user["password_hash"].encode()):
            self.error = "Wrong password"
            return

        session = {"user_id": user["id"], "username": user["username"]}
        from auth.session import save_session
        save_session(user["id"], user["username"])
        self.game.session = session
        self.game.state.user_id = user["id"]
        self.game.state.username = user["username"]

        from scenes.menu_scene import MenuScene
        self.game.scene_manager.switch_scene(MenuScene(self.game))

    def back(self):
        from scenes.menu_scene import MenuScene
        self.game.scene_manager.switch_scene(MenuScene(self.game))

    def handle_events(self, events):
        for event in events:
            self.username_input.handle_event(event)
            self.password_input.handle_event(event)
            self.login_btn.handle_event(event)
            self.back_btn.handle_event(event)

    def draw(self, screen):
        screen.fill(BACKGROUND_COLOR)
        title = self.title.render("Login", True, BLACK)
        screen.blit(title, title.get_rect(center=(BASE_WIDTH // 2, 260)))

        self.username_input.draw(screen)
        self.password_input.draw(screen)
        self.login_btn.draw(screen)
        self.back_btn.draw(screen)

        if self.error:
            error = self.font.render(self.error, True, RED)
            screen.blit(error, error.get_rect(center=(BASE_WIDTH // 2, 640)))

class RegisterScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        self.font = game.assets.get_font("body")
        self.title = game.assets.get_font("title")
        self.error = ""

        self.username_input = TextInput((MIDDLE_WIDTH - 200, 380, 400, 50), "Choose username", font=self.font)
        self.password_input = TextInput((MIDDLE_WIDTH - 200, 460, 400, 50), "Choose password", password=True, font=self.font)

        self.register_btn = Button((MIDDLE_WIDTH - 200, 550, 190, 60), "REGISTER", self._do_register)
        self.back_btn = Button((MIDDLE_WIDTH + 10, 550, 190, 60), "BACK", self.back)

    def _do_register(self):
        username = self.username_input.text.strip()
        password = self.password_input.text.encode()
        if not username or not password:
            self.error = "Please fill in both fields"
            return
        if len(password) < 4: # security aint my highest priority but still(=
            self.error = "Password must be at least 4 characters"
            return

        hashed = bcrypt.hashpw(password, bcrypt.gensalt()).decode()
        user = self.game.db.Register(username, hashed)
        if not user:
            self.error = "Username already taken"
            return

        session = {"user_id": user["id"], "username": user["username"]}
        from auth.session import save_session
        save_session(user["id"], user["username"])
        self.game.session = session
        self.game.state.user_id = user["id"]
        self.game.state.username = user["username"]

        from scenes.menu_scene import MenuScene
        self.game.scene_manager.switch_scene(MenuScene(self.game))

    def back(self):
        from scenes.menu_scene import MenuScene
        self.game.scene_manager.switch_scene(MenuScene(self.game))

    def handle_events(self, events):
        for event in events:
            self.username_input.handle_event(event)
            self.password_input.handle_event(event)
            self.register_btn.handle_event(event)
            self.back_btn.handle_event(event)

    def draw(self, screen):
        screen.fill(BACKGROUND_COLOR)
        title = self.title.render("Register", True, BLACK)
        screen.blit(title, title.get_rect(center=(BASE_WIDTH // 2, 260)))

        self.username_input.draw(screen)
        self.password_input.draw(screen)
        self.register_btn.draw(screen)
        self.back_btn.draw(screen)

        if self.error:
            error = self.font.render(self.error, True, RED)
            screen.blit(error, error.get_rect(center=(BASE_WIDTH // 2, 640)))