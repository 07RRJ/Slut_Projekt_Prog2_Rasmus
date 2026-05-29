import pygame
import time
from scenes.base_scene               import BaseScene
from logic.controllers.game_controller import GameController
from ui.button                       import Button
from ui.team_slot                    import TeamSlot
from ui.stat_box                     import StatBox
from core.constants                  import *

class MatchMakingScene(BaseScene):
    """
    Phase flow:
      1. Immediately call FindOrCreateMatch
      2a. If match is 'waiting'   → poll until opponent joins → go to preview
      2b. If match is 'previewing' → already matched → go straight to preview
    """

    def __init__(self, game):
        super().__init__(game)
        self.ctrl   = GameController(game)
        self.state  = game.state
        self.font   = game.assets.get_font("body")
        self.title  = game.assets.get_font("title")
        self.status = "Searching for opponent…"
        self.dots   = 0
        self.last_poll  = 0
        self.POLL_EVERY = 2   # seconds

        # Kick off matchmaking immediately
        match = self.ctrl.find_match()
        if match["phase"] in ("previewing", "shopping", "battling"):
            self._go_to_preview()

    def _go_to_preview(self):
        self.ctrl.load_enemy_team()
        self.game.scene_manager.switch_scene(
            PreviewScene(self.game)
        )

    def update(self):
        now = time.time()
        if now - self.last_poll > self.POLL_EVERY:
            self.last_poll = now
            match = self.ctrl.poll_match()
            if match and match["phase"] != "waiting":
                self._go_to_preview()
            self.dots = (self.dots + 1) % 4

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                # Cancel search
                from scenes.menu_scene import MenuScene
                self.game.scene_manager.switch_scene(MenuScene(self.game))

    def draw(self, screen):
        screen.fill(BACKGROUND_COLOR)
        msg = self.title.render(
            "Searching" + "." * self.dots, True, BLACK
        )
        screen.blit(msg, msg.get_rect(center=(BASE_WIDTH // 2, BASE_HEIGHT // 2)))
        hint = self.font.render("Press ESC to cancel", True, GRAY)
        screen.blit(hint, hint.get_rect(center=(BASE_WIDTH // 2, BASE_HEIGHT // 2 + 100)))

class PreviewScene(BaseScene):
    """
    Show opponent's deck (read-only) before the shop phase.
    Both players see this simultaneously; a countdown then opens the shop.
    """
    PREVIEW_SECONDS = 10

    def __init__(self, game):
        super().__init__(game)
        self.ctrl      = GameController(game)
        self.font      = game.assets.get_font("body")
        self.title     = game.assets.get_font("title")
        self.start     = time.time()
        self.stat_box  = StatBox(game.state)

        # Build slot renderers for both teams
        self.my_slots  = [TeamSlot(50  + i * 150, 560, i) for i in range(5)]
        self.opp_slots = [TeamSlot(900 - i * 150, 100, i) for i in range(5)]

    def update(self):
        if time.time() - self.start >= self.PREVIEW_SECONDS:
            from scenes.shop_scene import ShopScene
            self.ctrl.refresh_shop()
            self.game.scene_manager.switch_scene(ShopScene(self.game))

    def handle_events(self, events):
        pass

    def draw(self, screen):
        screen.fill(BACKGROUND_COLOR)

        # ── Opponent row (mirrored — slot 1 on right) ─────────
        for slot in self.opp_slots:
            card = self.game.state.enemy_team[slot.index]
            slot.draw(screen, card)

        # ── VS label ──────────────────────────────────────────
        vs = self.title.render("VS", True, GOLD)
        screen.blit(vs, vs.get_rect(center=(BASE_WIDTH // 2, BASE_HEIGHT // 2)))

        # ── My row ────────────────────────────────────────────
        for slot in self.my_slots:
            card = self.game.state.team[slot.index]
            slot.draw(screen, card)

        # ── Countdown ─────────────────────────────────────────
        remaining = max(0, self.PREVIEW_SECONDS - int(time.time() - self.start))
        timer = self.font.render(
            f"Shop opens in {remaining}s…", True, DARK_GRAY
        )
        screen.blit(timer, timer.get_rect(center=(BASE_WIDTH // 2, BASE_HEIGHT - 60)))

        self.stat_box.draw(screen)
