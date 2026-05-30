"""
WaitingReadyScene — waits for both players to signal shop-ready.

Stability rules:
  - Poll every 2 s for phase == 'battling'
  - Also detect phase == 'done' (P1 already finished the battle while P2
    was stuck here) → go straight to BattleScene so P2 can finalise their side.
  - If player1 hasn't sent a heartbeat for > P1_GONE_THRESHOLD seconds,
    start a visible countdown (P2_GRACE_SECONDS) for P2 to claim the win.
  - After that countdown expires P2 wins by default.
  - P2 detection: match["player2_id"] == my user_id
"""

import time
from scenes.base_scene import BaseScene
from logic.controllers.game_controller import GameController
from core.constants import *

P1_GONE_THRESHOLD = 120   # seconds of silence before P1 is considered gone
P2_GRACE_SECONDS  = 30    # countdown P2 sees before claiming default win

class WaitingReadyScene(BaseScene):
    POLL_EVERY = 2  # seconds

    def __init__(self, game):
        super().__init__(game)
        self.ctrl      = GameController(game)
        self.font      = game.assets.get_font("body")
        self.title     = game.assets.get_font("title")
        self.last_poll = 0
        self.dots      = 0

        self.p1_gone_since: float | None = None
        self.default_win_claimed = False

    # ── Helpers ──────────────────────────────────────────────

    def _am_player2(self) -> bool:
        match = self.game.state.match
        return bool(match and match.get("player2_id") == self.game.state.user_id)

    def _p1_ready(self) -> bool:
        match = self.game.state.match
        return bool(match and match.get("shop_ready", 0) >= 1)

    def _go_to_battle(self):
        from scenes.battle_scene import BattleScene
        self.game.scene_manager.switch_scene(BattleScene(self.game))

    def _check_p1_gone(self) -> None:
        if not self._am_player2() or self._p1_ready():
            self.p1_gone_since = None
            return
        match = self.game.state.match
        if not match:
            return
        secs_silent = self.game.db.p1_last_seen(match["id"])
        if secs_silent is None:
            return
        if secs_silent > P1_GONE_THRESHOLD:
            if self.p1_gone_since is None:
                self.p1_gone_since = time.time()
        else:
            self.p1_gone_since = None

    def _grace_seconds_left(self) -> int | None:
        if self.p1_gone_since is None:
            return None
        return max(0, int(P2_GRACE_SECONDS - (time.time() - self.p1_gone_since)))

    def _claim_default_win(self) -> None:
        if self.default_win_claimed:
            return
        self.default_win_claimed = True
        match = self.game.state.match
        if match:
            self.game.db.resolve_match(match["id"], self.game.state.user_id)
            self.game.state.match = self.game.db.get_match(match["id"])
        self._go_to_battle()

    # ── Scene interface ──────────────────────────────────────

    def update(self):
        now = time.time()
        if now - self.last_poll > self.POLL_EVERY:
            self.last_poll = now
            self.dots = (self.dots + 1) % 4

            match = self.ctrl.poll_match()
            if match:
                phase = match.get("phase", "")
                if phase == "battling":
                    self._go_to_battle()
                    return
                # P1 resolved the match (wrote 'done') before P2 got to battle.
                # Go to BattleScene anyway — run_battle() will read the resolved
                # winner and handle health / turn progression correctly.
                if phase == "done":
                    self._go_to_battle()
                    return

            self._check_p1_gone()

        if self._am_player2() and not self.default_win_claimed:
            left = self._grace_seconds_left()
            if left is not None and left == 0:
                self._claim_default_win()

    def handle_events(self, events):
        pass

    def draw(self, screen):
        screen.fill(BACKGROUND_COLOR)

        msg = self.title.render("Waiting for opponent" + "." * self.dots, True, BLACK)
        screen.blit(msg, msg.get_rect(center=(MIDDLE_WIDTH, MIDDLE_HEIGHT)))

        left = self._grace_seconds_left()
        if left is not None:
            warn = self.font.render(
                f"Opponent has left — claiming win in {left}s…", True, RED
            )
            screen.blit(warn, warn.get_rect(center=(MIDDLE_WIDTH, MIDDLE_HEIGHT + 80)))
        elif self._am_player2() and not self._p1_ready():
            hint = self.font.render(
                "Waiting for Player 1 to finish shopping…", True, GRAY
            )
            screen.blit(hint, hint.get_rect(center=(MIDDLE_WIDTH, MIDDLE_HEIGHT + 80)))
