"""
BattleScene — animated battle playback.

Uses BattleEngine's structured event log to drive per-step animation:
  1. Highlight the attacking card (gold border, 8px)
  2. Lerp a "projectile" rect from attacker → defender over SLIDE_TIME seconds
  3. On arrival: update defender HP on the displayed card copy
  4. If death event: mark that slot as hidden
  5. When all events done: show result banner, wait for click

All card state is kept in local display copies (self.a_cards / self.b_cards)
so the live GameState isn't mutated.
"""

import pygame, time, copy
from scenes.base_scene                 import BaseScene
from logic.controllers.game_controller import GameController
from logic.battle_engine               import BattleEvent
from ui.team_slot                      import TeamSlot
from ui.stat_box                       import StatBox
from core.constants                    import *

CARD_W, CARD_H = 120, 180
SLOT_GAP       = 20
SLIDE_TIME     = 0.35   # seconds for the projectile to travel
PAUSE_AFTER    = 0.25   # seconds to pause after each event before next

# ── Layout helpers ────────────────────────────────────────────────────────────
def _my_slot_rect(slot_index: int) -> pygame.Rect:
    x = MARGIN + slot_index * (CARD_W + SLOT_GAP)
    y = BASE_HEIGHT - CARD_H - MARGIN - 60
    return pygame.Rect(x, y, CARD_W, CARD_H)

def _opp_slot_rect(slot_index: int) -> pygame.Rect:
    # Opponent row: mirrored (slot 0 on right, slot 4 on left)
    x = BASE_WIDTH - MARGIN - CARD_W - slot_index * (CARD_W + SLOT_GAP)
    y = MARGIN + 60
    return pygame.Rect(x, y, CARD_W, CARD_H)

def _slot_rect(side: str, slot: int) -> pygame.Rect:
    return _my_slot_rect(slot) if side == "a" else _opp_slot_rect(slot)

def _slot_center(side: str, slot: int):
    r = _slot_rect(side, slot)
    return (r.centerx, r.centery)


class BattleScene(BaseScene):

    def __init__(self, game):
        super().__init__(game)
        self.ctrl     = GameController(game)
        self.font     = game.assets.get_font("body")
        self.title    = game.assets.get_font("title")
        self.stat_box = StatBox(game.state)

        # Load teams and run simulation (pure logic, no network during animation)
        self.ctrl.load_enemy_team()
        self.result = self.ctrl.run_battle()
        self.events = self.result["events"]

        # Local display copies so we can mutate HP/alive without touching state
        self.a_cards = [copy.copy(c) if c else None for c in game.state.team]
        self.b_cards = [copy.copy(c) if c else None for c in game.state.enemy_team]
        self.a_dead  = set()   # slot indices of defeated cards
        self.b_dead  = set()

        # Slot renderers (just for geometry; draw() calls them manually)
        self.my_slots  = [TeamSlot(*_my_slot_rect(i).topleft, i)  for i in range(5)]
        self.opp_slots = [TeamSlot(*_opp_slot_rect(i).topleft, i) for i in range(5)]

        # Animation state
        self.event_idx      = 0
        self.phase          = "pause"   # "sliding" | "pause" | "done"
        self.phase_start    = time.time()

        # Current event being animated
        self.cur_event: BattleEvent | None = None
        self.proj_start  = (0, 0)
        self.proj_end    = (0, 0)
        self.highlight_a_slot = -1
        self.highlight_b_slot = -1

        self.done = False
        self._advance()   # kick off first event immediately

    # ── Animation driver ─────────────────────────────────────

    def _advance(self):
        """Move to the next event in the log."""
        if self.event_idx >= len(self.events):
            self.phase = "done"
            self.done  = True
            self.highlight_a_slot = -1
            self.highlight_b_slot = -1
            return

        ev = self.events[self.event_idx]
        self.event_idx += 1
        self.cur_event = ev

        if ev.kind == "result":
            self.phase = "done"
            self.done  = True
            self.highlight_a_slot = -1
            self.highlight_b_slot = -1
            return

        if ev.kind == "death":
            # Immediately hide the card, then short pause
            if ev.defender_side == "a":
                self.a_dead.add(ev.defender_slot)
            else:
                self.b_dead.add(ev.defender_slot)
            self.highlight_a_slot = -1
            self.highlight_b_slot = -1
            self.phase       = "pause"
            self.phase_start = time.time()
            return

        if ev.kind == "strike":
            # Highlight attacker, start projectile
            if ev.attacker_side == "a":
                self.highlight_a_slot = ev.attacker_slot
                self.highlight_b_slot = -1
            else:
                self.highlight_b_slot = ev.attacker_slot
                self.highlight_a_slot = -1

            self.proj_start  = _slot_center(ev.attacker_side, ev.attacker_slot)
            self.proj_end    = _slot_center(ev.defender_side,  ev.defender_slot)
            self.phase       = "sliding"
            self.phase_start = time.time()

    def _finish_strike(self):
        """Called when the projectile reaches the target: apply HP update."""
        ev = self.cur_event
        if ev is None:
            return
        # Update the local display copy
        target_list = self.b_cards if ev.defender_side == "b" else self.a_cards
        c = target_list[ev.defender_slot]
        if c:
            c.health = ev.defender_hp
        self.highlight_a_slot = -1
        self.highlight_b_slot = -1
        self.phase       = "pause"
        self.phase_start = time.time()

    # ── Scene interface ──────────────────────────────────────

    def update(self):
        now     = time.time()
        elapsed = now - self.phase_start

        if self.phase == "sliding":
            if elapsed >= SLIDE_TIME:
                self._finish_strike()

        elif self.phase == "pause":
            if elapsed >= PAUSE_AFTER:
                self._advance()

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and self.done:
                from scenes.shop_scene import ShopScene
                from scenes.menu_scene import MenuScene
                player = self.game.db.get_player(self.game.state.user_id)
                if player:
                    self.game.scene_manager.switch_scene(ShopScene(self.game))
                else:
                    self.game.scene_manager.switch_scene(MenuScene(self.game))

    def draw(self, screen):
        screen.fill(BACKGROUND_COLOR)

        # ── Opponent row (top, mirrored) ──────────────────────
        for slot in self.opp_slots:
            card      = self.b_cards[slot.index]
            hidden    = slot.index in self.b_dead
            highlight = (slot.index == self.highlight_b_slot)
            slot.draw(screen, card, highlight=highlight, hidden=hidden)

        # ── My row (bottom) ───────────────────────────────────
        for slot in self.my_slots:
            card      = self.a_cards[slot.index]
            hidden    = slot.index in self.a_dead
            highlight = (slot.index == self.highlight_a_slot)
            slot.draw(screen, card, highlight=highlight, hidden=hidden)

        # ── VS label ─────────────────────────────────────────
        vs = self.title.render("VS", True, GOLD)
        screen.blit(vs, vs.get_rect(center=(MIDDLE_WIDTH, MIDDLE_HEIGHT)))

        # ── Projectile ────────────────────────────────────────
        if self.phase == "sliding" and self.cur_event:
            elapsed = time.time() - self.phase_start
            t       = min(elapsed / SLIDE_TIME, 1.0)
            px = int(self.proj_start[0] + (self.proj_end[0] - self.proj_start[0]) * t)
            py = int(self.proj_start[1] + (self.proj_end[1] - self.proj_start[1]) * t)
            pygame.draw.circle(screen, RED, (px, py), 10)

        # ── Current action text ───────────────────────────────
        if self.cur_event and not self.done:
            txt = self.font.render(self.cur_event.text, True, DARK_GRAY)
            screen.blit(txt, txt.get_rect(center=(MIDDLE_WIDTH, MIDDLE_HEIGHT + 60)))

        # ── Result banner ─────────────────────────────────────
        if self.done:
            w = self.result["winner"]
            if w == "a":
                banner, color = "YOU WIN!", GOLD
            elif w == "b":
                banner, color = "YOU LOSE",  RED
            else:
                banner, color = "DRAW",      GRAY
            surf = self.title.render(banner, True, color)
            screen.blit(surf, surf.get_rect(center=(MIDDLE_WIDTH, 50)))
            hint = self.font.render("Click anywhere to continue", True, GRAY)
            screen.blit(hint, hint.get_rect(center=(MIDDLE_WIDTH, BASE_HEIGHT - 50)))

        self.stat_box.draw(screen)
