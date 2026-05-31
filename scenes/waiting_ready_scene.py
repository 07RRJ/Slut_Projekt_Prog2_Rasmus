import time
from scenes.base_scene import BaseScene
from logic.controllers.game_controller import GameController
from core.constants import *

class WaitingReadyScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        self.ctrl = GameController(game)
        self.font = game.assets.get_font("body")
        self.title = game.assets.get_font("title")
        self.last_poll = 0
        self.dots = 0

        self.battle_countdown_start: float | None = None

        self.p1_gone_since: float | None = None
        self.controll_taken = False

    def am_player2(self) -> bool:
        match = self.game.state.match
        return bool(match and match.get("player2_id") == self.game.state.user_id)

    def go_to_battle(self):
        from scenes.battle_scene import BattleScene
        self.game.scene_manager.switch_scene(BattleScene(self.game))

    def start_battle_countdown(self):
        if self.battle_countdown_start is None:
            self.battle_countdown_start = time.time()

    def battle_countdown_left(self) -> int:
        if self.battle_countdown_start is None:
            return BATTLE_COUNTDOWN
        return max(0, int(BATTLE_COUNTDOWN - (time.time() - self.battle_countdown_start)))

    def check_p1_gone(self) -> None:
        if not self.am_player2():
            return
        match = self.game.state.match
        if not match:
            return
        seconds_silent = self.game.db.p1_last_seen(match["id"])
        if seconds_silent is None:
            return
        if seconds_silent > P1_GONE_THRESHOLD:
            if self.p1_gone_since is None:
                self.p1_gone_since = time.time()
        else:
            self.p1_gone_since = None

    def grace_seconds_left(self) -> int | None:
        if self.p1_gone_since is None:
            return None
        return max(0, int(P2_GRACE_SECONDS - (time.time() - self.p1_gone_since)))

    def p2_takes_controll(self) -> None:
        if self.controll_taken:
            return
        self.controll_taken = True
        match = self.game.state.match
        if match:
            self.game.db.resolve_match(match["id"], self.game.state.user_id)
            self.game.state.match = self.game.db.get_match(match["id"])
        self.go_to_battle()

    def update(self):
        now = time.time()

        if self.battle_countdown_start is not None:
            if self.battle_countdown_left() == 0:
                self.go_to_battle()
            return

        if now - self.last_poll > self.POLL_EVERY:
            self.last_poll = now
            self.dots = (self.dots + 1) % 4

            match = self.ctrl.poll_match()
            if match:
                phase = match.get("phase", "")

                if phase == "battling":
                    self.start_battle_countdown()
                    return

                if phase == "previewing" and self.am_player2():
                    self.game.db.force_phase(match["id"], "battling")
                    self.game.state.match = self.game.db.get_match(match["id"])
                    self.start_battle_countdown()
                    return

                if phase == "done":
                    self.go_to_battle()
                    return

            self.check_p1_gone()

        if self.am_player2() and not self.controll_taken:
            left = self.grace_seconds_left()
            if left is not None and left == 0:
                self.p2_takes_controll()

    def handle_events(self, events):
        pass

    def draw(self, screen):
        screen.fill(BACKGROUND_COLOR)

        if self.battle_countdown_start is not None:
            time_left = self.battle_countdown_left()
            msg = self.title.render(f"Battle starting in {time_left}…", True, GOLD)
            screen.blit(msg, msg.get_rect(center=(MIDDLE_WIDTH, MIDDLE_HEIGHT)))
            sub = self.font.render("Both players ready, syncing decks", True, GRAY)
            screen.blit(sub, sub.get_rect(center=(MIDDLE_WIDTH, MIDDLE_HEIGHT + 80)))
            return

        msg = self.title.render("Waiting for opponent" + "." * self.dots, True, BLACK)
        screen.blit(msg, msg.get_rect(center=(MIDDLE_WIDTH, MIDDLE_HEIGHT)))

        left = self.grace_seconds_left()
        if left is not None:
            info = self.font.render(f"Opponent has left, taking match controll in {left}s…", True, RED)
            screen.blit(info, info.get_rect(center=(MIDDLE_WIDTH, MIDDLE_HEIGHT + 80)))
        elif self.am_player2():
            info = self.font.render("Waiting for Player 1 to finish shopping…", True, GRAY)
            screen.blit(info, info.get_rect(center=(MIDDLE_WIDTH, MIDDLE_HEIGHT + 80)))