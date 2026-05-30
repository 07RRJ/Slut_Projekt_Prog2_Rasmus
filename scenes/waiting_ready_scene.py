"""
WaitingReadyScene — both players land here after clicking Ready.

Flow:
  1. Player arrives here after push_deck_state() + player_ready() already fired.
  2. Poll every 2s for phase == 'battling' (both players ready) or 'done'.
  3. Once phase == 'battling', show a 5s "Battle starting in N..." countdown.
     This buffer ensures both players' deck pushes have fully committed before
     BattleScene reads the enemy team.
  4. After 5s, go to BattleScene.

P2 disconnect handling:
  - If P1 hasn't heartbeated for > P1_GONE_THRESHOLD seconds, P2 starts a
    grace countdown and claims a default win when it expires.
  - P2 override: if stuck in 'previewing' phase (P1 left mid-preview from a
    previous round), force-advance to 'battling'.
"""

import time
from scenes.base_scene import BaseScene
from logic.controllers.game_controller import GameController
from core.constants import *

P1_GONE_THRESHOLD  = 120   # seconds before P1 considered disconnected
P2_GRACE_SECONDS   = 30    # P2 countdown before default win
BATTLE_COUNTDOWN   = 5     # seconds buffer after both ready before battle loads


class WaitingReadyScene(BaseScene):
    POLL_EVERY = 2

    def __init__(self, game):
        super().__init__(game)
        self.ctrl      = GameController(game)
        self.font      = game.assets.get_font("body")
        self.title     = game.assets.get_font("title")
        self.last_poll = 0
        self.dots      = 0

        # Battle countdown state (starts when both are ready)
        self.battle_countdown_start: float | None = None

        # P1-gone tracking
        self.p1_gone_since: float | None = None
        self.default_win_claimed = False

    # ── Helpers ──────────────────────────────────────────────

    def _am_player2(self) -> bool:
        match = self.game.state.match
        return bool(match and match.get("player2_id") == self.game.state.user_id)

    def _go_to_battle(self):
        from scenes.battle_scene import BattleScene
        self.game.scene_manager.switch_scene(BattleScene(self.game))

    def _start_battle_countdown(self):
        if self.battle_countdown_start is None:
            self.battle_countdown_start = time.time()

    def _battle_countdown_left(self) -> int:
        if self.battle_countdown_start is None:
            return BATTLE_COUNTDOWN
        return max(0, int(BATTLE_COUNTDOWN - (time.time() - self.battle_countdown_start)))

    def _check_p1_gone(self) -> None:
        if not self._am_player2():
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

    # ── Scene interface ───────────────────────────────────────

    def update(self):
        now = time.time()

        # If battle countdown is running, just tick it down
        if self.battle_countdown_start is not None:
            if self._battle_countdown_left() == 0:
                self._go_to_battle()
            return

        if now - self.last_poll > self.POLL_EVERY:
            self.last_poll = now
            self.dots = (self.dots + 1) % 4

            match = self.ctrl.poll_match()
            if match:
                phase = match.get("phase", "")

                if phase == "battling":
                    self._start_battle_countdown()
                    return

                # P2 override: stuck in 'previewing' means P1 left during a
                # previous preview window — force-advance so P2 isn't locked out
                if phase == "previewing" and self._am_player2():
                    self.game.db.force_phase(match["id"], "battling")
                    self.game.state.match = self.game.db.get_match(match["id"])
                    self._start_battle_countdown()
                    return

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

        # Battle countdown takes over the display once both are ready
        if self.battle_countdown_start is not None:
            n = self._battle_countdown_left()
            msg = self.title.render(f"Battle starting in {n}…", True, GOLD)
            screen.blit(msg, msg.get_rect(center=(MIDDLE_WIDTH, MIDDLE_HEIGHT)))
            sub = self.font.render("Both players ready — syncing decks", True, GRAY)
            screen.blit(sub, sub.get_rect(center=(MIDDLE_WIDTH, MIDDLE_HEIGHT + 80)))
            return

        msg = self.title.render("Waiting for opponent" + "." * self.dots, True, BLACK)
        screen.blit(msg, msg.get_rect(center=(MIDDLE_WIDTH, MIDDLE_HEIGHT)))

        left = self._grace_seconds_left()
        if left is not None:
            warn = self.font.render(
                f"Opponent has left — claiming win in {left}s…", True, RED
            )
            screen.blit(warn, warn.get_rect(center=(MIDDLE_WIDTH, MIDDLE_HEIGHT + 80)))
        elif self._am_player2():
            hint = self.font.render(
                "Waiting for Player 1 to finish shopping…", True, GRAY
            )
            screen.blit(hint, hint.get_rect(center=(MIDDLE_WIDTH, MIDDLE_HEIGHT + 80)))
