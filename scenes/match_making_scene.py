import pygame
import time
from scenes.base_scene import BaseScene
from logic.controllers.game_controller import GameController
from ui.team_slot import TeamSlot
from ui.stat_box import StatBox
from core.constants import *

class MatchMakingScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        self.ctrl = GameController(game)
        self.state = game.state
        self.font = game.assets.get_font("body")
        self.title = game.assets.get_font("title")
        self.status = "Searching for opponent…"
        self.dots = 0
        self.last_poll = 0
        self.POLL_EVERY = 2 # seconds

        match = self.ctrl.find_match()
        if match["phase"] in ("previewing", "shopping", "battling"):
            self.go_to_preview()

    def go_to_preview(self):
        self.ctrl.load_enemy_team()
        self.game.scene_manager.switch_scene(PreviewScene(self.game))

    def update(self):
        now = time.time()
        if now - self.last_poll > self.POLL_EVERY:
            self.last_poll = now
            match = self.ctrl.poll_match()
            if match and match["phase"] != "waiting":
                self.go_to_preview()
            self.dots = (self.dots + 1) % 4

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: # cancel search
                from scenes.menu_scene import MenuScene
                self.game.scene_manager.switch_scene(MenuScene(self.game))

    def draw(self, screen):
        screen.fill(BACKGROUND_COLOR)

        searching = self.title.render("Searching" + "." * self.dots, True, BLACK)
        screen.blit(searching, searching.get_rect(center=(MIDDLE_WIDTH, MIDDLE_HEIGHT)))
        leave = self.font.render("Press ESC to cancel", True, GRAY)
        screen.blit(leave, leave.get_rect(center=(MIDDLE_WIDTH, MIDDLE_HEIGHT + 100)))

class PreviewScene(BaseScene):
    PREVIEW_SECONDS = 10

    def __init__(self, game):
        super().__init__(game)
        self.ctrl = GameController(game)
        self.font = game.assets.get_font("body")
        self.title = game.assets.get_font("title")
        self.stat_box = StatBox(game.state)

        self.my_slots  = [TeamSlot(my_slot_x(i),  my_slot_y(),  i) for i in range(5)]
        self.opp_slots = [TeamSlot(opp_slot_x(i), opp_slot_y(), i) for i in range(5)]

        # Use server-side match timestamp as shared clock so both clients
        # count down from the same origin — this prevents timer desync where
        # P2 (who joins slightly later) gets less preview time than P1.
        self._server_start: float = time.time()  # fallback: local clock
        match = game.state.match
        if match:
            # preview_started_at is set by the DB when P2 joins; prefer it
            # over created_at (which is P1's match creation time).
            ts = match.get("preview_started_at") or match.get("created_at")
            if ts:
                try:
                    from datetime import datetime, timezone
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    self._server_start = dt.timestamp()
                except Exception:
                    pass

    def _elapsed(self) -> float:
        return time.time() - self._server_start

    def update(self):
        if self._elapsed() >= self.PREVIEW_SECONDS:
            from scenes.shop_scene import ShopScene
            # Grant gold for this shopping round. This is the correct place:
            # preview->shop starts a new round. Both clients compute the same
            # value from the DB so the last-writer-wins race is harmless.
            player = self.game.db.get_player(self.game.state.user_id)
            if player:
                new_gold = min(player.get("gold", 0) + 10, 100)
                self.game.db.update_player(self.game.state.user_id, {"gold": new_gold})
                self.game.state.gold = new_gold
            # Reset shop_ready so both players can signal ready again this round.
            # Player1 owns this write to avoid a write race.
            match = self.game.state.match
            if match and match.get("player1_id") == self.game.state.user_id:
                try:
                    self.game.db.client.table("game_manager").update({
                        "shop_ready": 0,
                        "phase": "shopping",
                    }).eq("id", match["id"]).execute()
                except Exception:
                    pass
            # Clear match — shop.ready() must always go to matchmaking.
            self.game.state.match = None
            self.ctrl.refresh_shop()
            self.game.scene_manager.switch_scene(ShopScene(self.game))

    def handle_events(self, events):
        pass

    def draw(self, screen):
        screen.fill(BACKGROUND_COLOR)

        for slot in self.opp_slots:
            card = self.game.state.enemy_team[slot.index]
            slot.draw(screen, card)

        vs = self.title.render("VS", True, GOLD)
        screen.blit(vs, vs.get_rect(center=(MIDDLE_WIDTH, MIDDLE_HEIGHT)))

        for slot in self.my_slots:
            card = self.game.state.team[slot.index]
            slot.draw(screen, card)

        remaining = max(0, self.PREVIEW_SECONDS - int(self._elapsed()))
        timer = self.font.render(f"Shop opens in {remaining}", True, DARK_GRAY)
        screen.blit(timer, timer.get_rect(center=(MIDDLE_WIDTH, BASE_HEIGHT - 60)))

        self.stat_box.draw(screen)