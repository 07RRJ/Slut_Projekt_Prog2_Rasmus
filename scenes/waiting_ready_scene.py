"""
WaitingReadyScene — waits for both players to signal shop-ready.

Stability rules implemented here:
  - Poll every 2 s for phase == 'battling'
  - If player1 hasn't sent a heartbeat for > P1_GONE_THRESHOLD seconds,
    start a visible countdown (P2_GRACE_SECONDS) for P2 to claim the win.
  - If that countdown expires, P2 wins by default (resolve_match called locally
    by P2 to unblock the game; a tiny race window exists but is acceptable).
  - P2 detection: match["player2_id"] == my user_id
"""

import time
from scenes.base_scene import BaseScene
from logic.controllers.game_controller import GameController
from core.constants import *

# How long (s) P1 must be silent before we consider them gone
P1_GONE_THRESHOLD  = 120   # 2 minutes

# Grace period (s) P2 gets to watch before claiming default win
P2_GRACE_SECONDS   = 30

class WaitingReadyScene(BaseScene):
    POLL_EVERY = 2  # seconds

    def __init__(self, game):
        super().__init__(game)
        self.ctrl      = GameController(game)
        self.font      = game.assets.get_font("body")
        self.title     = game.assets.get_font("title")
        self.last_poll = 0
        self.dots      = 0

        # P1-gone detection (only meaningful for P2)
        self.p1_gone_since: float | None = None   # time.time() when we first noticed
        self.default_win_claimed = False

    def _am_player2(self) -> bool:
        match = self.game.state.match
        return bool(match and match.get("player2_id") == self.game.state.user_id)

    def _p1_ready(self) -> bool:
        """shop_ready >= 1 means player1 already signalled."""
        match = self.game.state.match
        return bool(match and match.get("shop_ready", 0) >= 1)

    def _check_p1_gone(self) -> None:
        """
        For P2: poll how long since P1's last heartbeat.
        If > threshold, start the grace countdown.
        """
        if not self._am_player2():
            return
        if self._p1_ready():
            # P1 already ready — no need to check
            self.p1_gone_since = None
            return

        match = self.game.state.match
        if not match:
            return

        secs_silent = self.game.db.p1_last_seen(match["id"])
        if secs_silent is None:
            # Can't determine — be generous, don't trigger
            return

        if secs_silent > P1_GONE_THRESHOLD:
            if self.p1_gone_since is None:
                self.p1_gone_since = time.time()
        else:
            # P1 came back
            self.p1_gone_since = None

    def _grace_seconds_left(self) -> int | None:
        if self.p1_gone_since is None:
            return None
        elapsed = time.time() - self.p1_gone_since
        return max(0, int(P2_GRACE_SECONDS - elapsed))

    def _claim_default_win(self) -> None:
        if self.default_win_claimed:
            return
        self.default_win_claimed = True
        match = self.game.state.match
        if match:
            # Resolve match with P2 as winner
            self.game.db.resolve_match(match["id"], self.game.state.user_id)
            self.game.state.match = self.game.db.get_match(match["id"])
        # Proceed to battle scene — BattleScene will see the resolved match
        # and award the win correctly via run_battle()
        from scenes.battle_scene import BattleScene
        self.game.scene_manager.switch_scene(BattleScene(self.game))

    # ── Scene interface ──────────────────────────────────────

    def update(self):
        now = time.time()
        if now - self.last_poll > self.POLL_EVERY:
            self.last_poll = now
            self.dots = (self.dots + 1) % 4

            if self.ctrl.poll_both_ready():
                from scenes.battle_scene import BattleScene
                self.game.scene_manager.switch_scene(BattleScene(self.game))
                return

            # P2 disconnect-detection
            self._check_p1_gone()

        # Check if grace period expired → claim default win
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

        body = self.font

        # P1-gone warning (only shown to P2)
        left = self._grace_seconds_left()
        if left is not None:
            # Show red warning
            warn = body.render(
                f"Opponent has left the shop — claiming win in {left}s…",
                True, RED
            )
            screen.blit(warn, warn.get_rect(center=(MIDDLE_WIDTH, MIDDLE_HEIGHT + 80)))
        elif self._am_player2() and not self._p1_ready():
            # Show soft nudge
            hint = body.render(
                "Waiting for Player 1 to finish shopping…", True, GRAY
            )
            screen.blit(hint, hint.get_rect(center=(MIDDLE_WIDTH, MIDDLE_HEIGHT + 80)))
