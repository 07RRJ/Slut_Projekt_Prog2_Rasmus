"""
ShopScene — all card actions are LOCAL (no DB round-trips).
State is pushed to the DB at three moments only:
  1. Player clicks Ready
  2. 60s auto-ready fires
  3. 30s silent checkpoint (safety save in case of crash)
"""
import time
import pygame
from scenes.base_scene                 import BaseScene
from logic.controllers.game_controller import GameController
from logic.shop_logic                  import ShopLogic
from ui.button                         import Button
from ui.team_slot                      import TeamSlot
from ui.card_view                      import CardView
from ui.stat_box                       import StatBox
from core.constants                    import *

SHOP_TIME_LIMIT      = 60    # seconds before auto-ready fires
CHECKPOINT_TIME      = 30    # seconds — silent save halfway through
HEARTBEAT_INTERVAL   = 5     # seconds between heartbeat pings

SU_W, SU_H = CARD_W, CARD_H


class ShopScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        self.ctrl = GameController(game)

        # Shop offer always fetched fresh from DB (read-only, cheap)
        if not game.state.shop_cards:
            self.ctrl.refresh_shop()

        # Team is already in game.state.team from the previous battle/start_run.
        # We do NOT re-fetch from DB here — we trust the local state.

        # ── Layout ───────────────────────────────────────────
        self.team_slots = [
            TeamSlot(my_slot_x(i), my_slot_y(), i)
            for i in range(5)
        ]

        shop_y = MARGIN + 60
        self.shop_positions = [
            (MARGIN + i * (CARD_W + CARD_GAP), shop_y) for i in range(3)
        ]

        stat_start_x = BASE_WIDTH // 2 + MARGIN
        self.stat_positions = [
            (stat_start_x + i * (SU_W + CARD_GAP + 20), shop_y) for i in range(2)
        ]

        btn_y = my_slot_y() - 100
        self.reroll_btn = Button(
            (BASE_WIDTH - 420, btn_y, 180, 70), "reroll", self.reroll
        )
        self.ready_btn = Button(
            (BASE_WIDTH - 220, btn_y, 180, 70), "ready", self.ready
        )
        self.stat_box = StatBox(game.state)

        # ── Selection state ───────────────────────────────────
        self.selected_shop_idx     = None
        self.selected_stat_idx     = None
        self.selected_team_slot    = None   # for card swapping
        self.bought_shop_idx       = set()
        self.bought_stat_idx       = set()
        self.reroll_cost           = 1
        self.message               = ""
        self.selecting_stat_target = False

        # ── Timing ────────────────────────────────────────────
        self.shop_start        = time.time()
        self.auto_ready_fired  = False
        self.checkpoint_saved  = False      # True after 30s save fires
        self.last_heartbeat    = time.time()

    # ── Timing helpers ────────────────────────────────────────

    def _seconds_left(self) -> int:
        return max(0, int(SHOP_TIME_LIMIT - (time.time() - self.shop_start)))

    def _elapsed(self) -> float:
        return time.time() - self.shop_start

    def _maybe_heartbeat(self) -> None:
        now = time.time()
        if now - self.last_heartbeat >= HEARTBEAT_INTERVAL:
            self.last_heartbeat = now
            try:
                self.game.db.heartbeat(self.game.state.user_id)
            except Exception:
                pass

    # ── Button callbacks ─────────────────────────────────────

    def reroll(self):
        if self.ctrl.reroll_shop(self.reroll_cost):
            self.selected_shop_idx     = None
            self.selected_stat_idx     = None
            self.selected_team_slot    = None
            self.selecting_stat_target = False
            self.bought_shop_idx       = set()
            self.bought_stat_idx       = set()
            self.reroll_cost          += 1
            self.message = f"Rerolled! Next reroll costs {self.reroll_cost} gold"
        else:
            self.message = f"Not enough gold! (costs {self.reroll_cost})"

    def ready(self):
        self._clear_selection()
        self.auto_ready_fired = True
        if self.game.state.match is None:
            # First shop (no match yet) — push deck and go to matchmaking.
            self.ctrl.push_deck_state()
            from scenes.match_making_scene import MatchMakingScene
            self.game.scene_manager.switch_scene(MatchMakingScene(self.game))
        else:
            # Already paired — signal ready then wait for opponent.
            # Loop: matchmaking -> preview -> shop -> [ready] -> WaitingReady -> pvp
            self.ctrl.signal_shop_ready()
            from scenes.waiting_ready_scene import WaitingReadyScene
            self.game.scene_manager.switch_scene(WaitingReadyScene(self.game))

    def _clear_selection(self):
        self.selected_shop_idx     = None
        self.selected_stat_idx     = None
        self.selected_team_slot    = None
        self.selecting_stat_target = False

    # ── Shop actions (all local, no DB) ───────────────────────

    def buy(self, shop_idx, target_slot):
        if shop_idx in self.bought_shop_idx:
            self.message = "Already bought that card!"
            return
        card = self.game.state.shop_cards[shop_idx]
        if self.ctrl.buy_card(card, target_slot):
            self.bought_shop_idx.add(shop_idx)
            self.selected_shop_idx = None
            self.message = f"Bought {card.name}!"
        else:
            existing = self.game.state.team[target_slot]
            if existing is not None:
                self.message = "That slot is occupied! Sell first or pick another slot."
            else:
                self.message = "Not enough gold!"

    def sell(self, slot_idx):
        if self.ctrl.sell_card(slot_idx):
            self.message = "Sold for 1 gold"
        else:
            self.message = "No card in that slot"

    def apply_stat_up(self, slot_idx):
        if self.selected_stat_idx in self.bought_stat_idx:
            self.message = "Already used that stat-up!"
            self._clear_selection()
            return
        su = self.game.state.stat_ups[self.selected_stat_idx]
        if self.ctrl.apply_stat_up(su, slot_idx):
            self.bought_stat_idx.add(self.selected_stat_idx)
            self.message = f"Applied {su.label}!"
        else:
            self.message = "Can't apply: no card there or not enough gold"
        self._clear_selection()

    # ── Update ────────────────────────────────────────────────

    def update(self):
        self._maybe_heartbeat()
        elapsed = self._elapsed()

        # 30s checkpoint — silent background save
        if not self.checkpoint_saved and elapsed >= CHECKPOINT_TIME:
            self.checkpoint_saved = True
            try:
                self.ctrl.push_deck_state()
            except Exception:
                pass  # best-effort; don't crash the game

        # 60s auto-ready
        if not self.auto_ready_fired and self._seconds_left() == 0:
            self.auto_ready_fired = True
            self.message = "Time's up — auto-readying!"
            self.ready()

    # ── Event handling ────────────────────────────────────────

    def handle_events(self, events):
        for event in events:
            self.reroll_btn.handle_event(event)
            self.ready_btn.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos

                # ── Stat-up items ─────────────────────────────
                for i, (sx, sy) in enumerate(self.stat_positions):
                    r = pygame.Rect(sx, sy, SU_W, SU_H)
                    if r.collidepoint(mx, my):
                        if i in self.bought_stat_idx:
                            self.message = "Already used that stat-up! Reroll for more."
                        else:
                            self.selected_stat_idx     = i
                            self.selected_shop_idx     = None
                            self.selected_team_slot    = None
                            self.selecting_stat_target = True
                            su = self.game.state.stat_ups[i]
                            self.message = f"Selected {su.label} ({su.cost}g) — click a team slot"

                # ── New-card shop ─────────────────────────────
                for i, (sx, sy) in enumerate(self.shop_positions):
                    r = pygame.Rect(sx, sy, CARD_W, CARD_H)
                    if r.collidepoint(mx, my):
                        if i not in self.bought_shop_idx:
                            self.selected_shop_idx     = i
                            self.selected_stat_idx     = None
                            self.selected_team_slot    = None
                            self.selecting_stat_target = False
                            card = self.game.state.shop_cards[i]
                            self.message = f"Selected {card.name} — click a team slot to place"

                # ── Team slots ────────────────────────────────
                for slot in self.team_slots:
                    if slot.rect.collidepoint(mx, my):
                        if event.button == 3:
                            # Right-click always sells
                            self._clear_selection()
                            self.sell(slot.index)

                        elif self.selecting_stat_target and self.selected_stat_idx is not None:
                            self.apply_stat_up(slot.index)

                        elif self.selected_shop_idx is not None:
                            self.buy(self.selected_shop_idx, slot.index)

                        else:
                            # Team card swap
                            if self.selected_team_slot is None:
                                if self.game.state.team[slot.index] is not None:
                                    self.selected_team_slot = slot.index
                                    card = self.game.state.team[slot.index]
                                    self.message = f"Selected {card.name} — click another slot to swap"
                                else:
                                    self.message = "That slot is empty."
                            else:
                                if slot.index == self.selected_team_slot:
                                    self.selected_team_slot = None
                                    self.message = ""
                                else:
                                    if self.ctrl.swap_cards(self.selected_team_slot, slot.index):
                                        self.message = "Cards swapped!"
                                    else:
                                        self.message = "Nothing to swap."
                                    self.selected_team_slot = None

    # ── Drawing ───────────────────────────────────────────────

    def draw(self, screen):
        screen.fill(BACKGROUND_COLOR)

        body = self.game.assets.get_font("body")

        screen.blit(body.render("new cards:", True, GRAY),
                    (MARGIN, MARGIN + 28))
        screen.blit(body.render("stat up:", True, BLUE),
                    (BASE_WIDTH // 2 + MARGIN, MARGIN + 28))

        # New-card shop
        for i, card in enumerate(self.game.state.shop_cards):
            sx, sy = self.shop_positions[i]
            bought  = i in self.bought_shop_idx
            sel     = (i == self.selected_shop_idx) and not bought
            cv      = CardView(card, sx, sy, selected=sel, greyed=bought)
            cv.draw(screen)

        # Stat-up items
        for i, su in enumerate(self.game.state.stat_ups):
            sx, sy = self.stat_positions[i]
            used   = i in self.bought_stat_idx
            sel    = (i == self.selected_stat_idx) and not used
            _draw_stat_up(screen, su, sx, sy, sel, used, body)

        # Team slots — highlight selected-for-swap slot
        for slot in self.team_slots:
            swap_hl = (slot.index == self.selected_team_slot)
            slot.draw(screen, self.game.state.team[slot.index], highlight=swap_hl)

        # Buttons / HUD
        rc_label = body.render(f"reroll ({self.reroll_cost}g)", True, DARK_GRAY)
        screen.blit(rc_label, (self.reroll_btn.rect.x,
                               self.reroll_btn.rect.y - 28))
        self.reroll_btn.draw(screen)
        self.ready_btn.draw(screen)
        self.stat_box.draw(screen)

        # Timer
        secs        = self._seconds_left()
        timer_color = RED if secs <= 10 else DARK_GRAY
        timer_surf  = body.render(f"Shop closes in: {secs}s", True, timer_color)
        screen.blit(timer_surf, timer_surf.get_rect(topright=(BASE_WIDTH - MARGIN, MARGIN)))

        # 30s checkpoint indicator
        if self.checkpoint_saved:
            saved = body.render("✓ saved", True, GRAY)
            screen.blit(saved, saved.get_rect(topright=(BASE_WIDTH - MARGIN, MARGIN + 30)))

        if self.message:
            msg = body.render(self.message, True, DARK_GRAY)
            screen.blit(msg, msg.get_rect(
                center=(BASE_WIDTH // 2, my_slot_y() - 40)
            ))


def _draw_stat_up(screen, su, x, y, selected, used, font):
    rect = pygame.Rect(x, y, CARD_W, CARD_H)
    if used:
        pygame.draw.rect(screen, GRAY, rect, border_radius=20)
        sold = font.render("SOLD OUT", True, DARK_GRAY)
        screen.blit(sold, sold.get_rect(center=rect.center))
        return
    border_color = GOLD if selected else BLUE
    border_width = 6    if selected else 3
    pygame.draw.rect(screen, border_color, rect, border_width, border_radius=20)
    label = font.render(su.label,      True, BLACK)
    cost  = font.render(f"{su.cost}g", True, GOLD)
    screen.blit(label, label.get_rect(center=(rect.centerx, rect.centery - 16)))
    screen.blit(cost,  cost.get_rect( center=(rect.centerx, rect.centery + 20)))
