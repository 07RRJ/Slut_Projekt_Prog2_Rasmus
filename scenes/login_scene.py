import pygame
import threading
import bcrypt
from scenes.base_scene import BaseScene
from ui.button import Button
from ui.text_input import TextInput
from core.constants import *

class AuthScene(BaseScene):
    def __init__(self, game, title_text):
        super().__init__(game)
        self.font = game.assets.get_font("body")
        self.title_font = game.assets.get_font("title")
        self.title_text = title_text
        self.error = ""
        self.loading = False

        self.username_input = TextInput((MIDDLE_WIDTH - 200, 380, 400, 50), "Username", font=self.font)
        self.password_input = TextInput((MIDDLE_WIDTH - 200, 460, 400, 50), "Password", password=True, font=self.font)

    def set_loading(self, state: bool):
        self.loading = state
        self.username_input.disabled = state
        self.password_input.disabled = state
        for btn in self.buttons():
            btn.disabled = state # handled below in draw

    def buttons(self):
        return []

    def back(self):
        from scenes.menu_scene import MenuScene
        self.game.scene_manager.switch_scene(MenuScene(self.game))

    def open_session(self, user): # get the session duh
        from auth.session import save_session
        from scenes.menu_scene import MenuScene
        save_session(user["id"], user["username"])
        self.game.session = {"user_id": user["id"], "username": user["username"]}
        self.game.state.user_id = user["id"]
        self.game.state.username = user["username"]
        self.game.db.cleanup_stale_data(user["id"])
        self.game.scene_manager.switch_scene(MenuScene(self.game))

    def handle_events(self, events): # event logic from pygame, like in all scenes
        for event in events:
            self.username_input.handle_event(event)
            self.password_input.handle_event(event)
            if not self.loading:
                for btn in self._buttons():
                    btn.handle_event(event)

    def draw(self, screen):
        screen.fill(BACKGROUND_COLOR)
        title = self.title_font.render(self.title_text, True, BLACK)
        screen.blit(title, title.get_rect(center=(MIDDLE_WIDTH, 260)))

        self.username_input.draw(screen)
        self.password_input.draw(screen)

        for btn in self.buttons():
            if self.loading:
                draw_disabled_button(screen, btn) # visual "this isnt active thingy so you dont spam it"
            else:
                btn.draw(screen)

        if self.loading:
            dots = int(pygame.time.get_ticks() / 400) % 4
            msg = self.font.render("Please wait" + "." * dots, True, GRAY)
            screen.blit(msg, msg.get_rect(center=(MIDDLE_WIDTH, 640)))
        elif self.error:
            err = self.font.render(self.error, True, RED)
            screen.blit(err, err.get_rect(center=(MIDDLE_WIDTH, 640)))

def draw_disabled_button(screen, btn):
    pygame.draw.rect(screen, (180, 180, 180), btn.rect, border_radius=18)
    pygame.draw.rect(screen, GRAY, btn.rect, 4, border_radius=18)
    font = pygame.font.SysFont("arial", 28)
    surf = font.render(btn.text, True, GRAY)
    screen.blit(surf, surf.get_rect(center=btn.rect.center))

class LoginScene(AuthScene):
    def __init__(self, game):
        super().__init__(game, "Login")
        self.login_btn = Button((MIDDLE_WIDTH - 200, 550, 190, 60), "LOGIN", self.do_login)
        self.back_btn = Button((MIDDLE_WIDTH + 10, 550, 190, 60), "BACK", self.back)

    def buttons(self):
        return [self.login_btn, self.back_btn]

    def do_login(self):
        username = self.username_input.text.strip()
        password = self.password_input.text.encode()
        if not username or not password:
            self.error = "Fill in both fields"
            return
        self.set_loading(True)
        self.error = ""

        def work():
            user = self.game.db.login(username)
            if not user:
                self.error = "User not found"
                self.set_loading(False)
                return
            if not bcrypt.checkpw(password, user["password_hash"].encode()):
                self.error = "Wrong password"
                self.set_loading(False)
                return
            self._pending_session = user

        self._pending_session = None
        threading.Thread(target=work, daemon=True).start()

    def update(self):
        if self.loading and hasattr(self, "_pending_session") and self._pending_session is not None:
            user = self._pending_session
            self._pending_session = None
            self._set_loading(False)
            self._open_session(user)

class RegisterScene(AuthScene):
    def __init__(self, game):
        super().__init__(game, "Register")
        self.register_btn = Button((MIDDLE_WIDTH - 200, 550, 190, 60), "REGISTER", self.do_register)
        self.back_btn = Button((MIDDLE_WIDTH + 10, 550, 190, 60), "BACK", self.back)

    def buttons(self):
        return [self.register_btn, self.back_btn]

    def do_register(self):
        username = self.username_input.text.strip()
        password = self.password_input.text.encode()
        if not username or not password:
            self.error = "Fill in both fields"
            return
        if len(password) < 4:
            self.error = "Password must be at least 4 characters" # some base security for users
            return
        self._set_loading(True)
        self.error = ""

        def work():
            hashed = bcrypt.hashpw(password, bcrypt.gensalt()).decode()
            user = self.game.db.register(username, hashed)
            if not user:
                self.error = "Username already taken"
                self._set_loading(False)
                return
            self._pending_session = user

        self._pending_session = None
        threading.Thread(target=work, daemon=True).start()

    def update(self):
        if self.loading and hasattr(self, "_pending_session") and self._pending_session is not None:
            user = self._pending_session
            self._pending_session = None
            self._set_loading(False)
            self._open_session(user)
