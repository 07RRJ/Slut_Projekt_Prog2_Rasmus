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

# Card dimensions (matches CardView)
CARD_W, CARD_H = 120, 180
SLOT_GAP       = 20    # gap between cards in a row

# ── Shop timer ────────────────────────────────────────────────
SHOP_TIME_LIMIT    = 60   # seconds before auto-ready fires
HEARTBEAT_INTERVAL = 5    # seconds between heartbeat pings to DB

class ShopScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        self.ctrl = GameController(game)

        if not game.state.shop_cards:
            self.ctrl.refresh_shop()
        if all(c is None for c in game.state.team):
            self.ctrl.refresh_team()

        # ── Layout ───────────────────────────────────────────
        slot_start_x = MARGIN
        slot_y       = BASE_HEIGHT - CARD_H - MARGIN - 60
        self.team_slots = [
            TeamSlot(slot_start_x + i * (CARD_W + SLOT_GAP), slot_y, i)
            for i in range(5)
        ]

        shop_x = MARGIN
        shop_y = MARGIN + 60
        self.shop_positions = [
            (shop_x + i * (CARD_W + SLOT_GAP), shop_y) for i in range(3)
        ]

        stat_start_x = BASE_WIDTH // 2 + MARGIN
        self.stat_positions = [
            (stat_start_x + i * (CARD_W + SLOT_GAP + 20), shop_y) for i in range(2)
        ]

        btn_y = slot_y - 100
        self.reroll_btn = Button(
            (BASE_WIDTH - 420, btn_y, 180, 70), "reroll", self.reroll
        )
        self.ready_btn = Button(
            (BASE_WIDTH - 220, btn_y, 180, 70), "ready", self.ready
        )
        self.stat_box = StatBox(game.state)

        # ── State ─────────────────────────────────────────────
        self.selected_shop_idx  = None
        self.selected_stat_idx  = None
        self.bought_shop_idx    = set()
        self.reroll_cost        = 1
        self.message            = ""
        self.selecting_stat_target = False

        # ── Timer ─────────────────────────────────────────────
        self.shop_start         = time.time()
        self.auto_ready_fired   = False
        self.last_heartbeat     = time.time()

    # ── Internal helpers ─────────────────────────────────────

    def _seconds_left(self) -> int:
        elapsed = time.time() - self.shop_start
        return max(0, int(SHOP_TIME_LIMIT - elapsed))

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
            self.selecting_stat_target = False
            self.bought_shop_idx       = set()
            self.reroll_cost          += 1
            self.message = f"Rerolled! Next reroll costs {self.reroll_cost} gold"
        else:
            self.message = f"Not enough gold! (costs {self.reroll_cost})"

    def ready(self):
        self.selected_shop_idx     = None
        self.selected_stat_idx     = None
        self.selecting_stat_target = False
        self.auto_ready_fired      = True
        if self.game.state.match is None:
            from scenes.match_making_scene import MatchMakingScene
            self.game.scene_manager.switch_scene(MatchMakingScene(self.game))
        else:
            self.ctrl.signal_shop_ready()
            from scenes.waiting_ready_scene import WaitingReadyScene
            self.game.scene_manager.switch_scene(WaitingReadyScene(self.game))

    # ── Shop actions ─────────────────────────────────────────

    def buy(self, shop_idx):
        if shop_idx in self.bought_shop_idx:
            self.message = "Already bought that card!"
            return
        card = self.game.state.shop_cards[shop_idx]
        slot = None
        for i, tc in enumerate(self.game.state.team):
            if tc and tc.card_id == card.card_id and tc.level < 3:
                slot = i
                break
        if slot is None:
            slot = ShopLogic.first_free_slot(self.game.state.team)
        if slot is None:
            self.message = "Team full! Sell a card first"
            return
        if self.ctrl.buy_card(card, slot):
            self.bought_shop_idx.add(shop_idx)
            self.selected_shop_idx = None
            self.message = f"Bought {card.name}!"
        else:
            self.message = "Not enough gold!"

    def sell(self, slot_idx):
        if self.ctrl.sell_card(slot_idx):
            self.message = "Sold for 1 gold"
        else:
            self.message = "No card in that slot"

    def apply_stat_up(self, slot_idx):
        su = self.game.state.stat_ups[self.selected_stat_idx]
        if self.ctrl.apply_stat_up(su, slot_idx):
            self.message = f"Applied {su.label}!"
        else:
            self.message = "Can't apply: no card there or not enough gold"
        self.selected_stat_idx     = None
        self.selecting_stat_target = False

    # ── Update ───────────────────────────────────────────────

    def update(self):
        self._maybe_heartbeat()

        # Auto-ready when timer expires (only fires once)
        if not self.auto_ready_fired and self._seconds_left() == 0:
            self.auto_ready_fired = True
            self.message = "Time's up — auto-readying!"
            self.ready()

    # ── Event handling ───────────────────────────────────────

    def handle_events(self, events):
        for event in events:
            self.reroll_btn.handle_event(event)
            self.ready_btn.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos

                for i, (sx, sy) in enumerate(self.stat_positions):
                    r = pygame.Rect(sx, sy, CARD_W, CARD_H)
                    if r.collidepoint(mx, my):
                        self.selected_stat_idx     = i
                        self.selected_shop_idx     = None
                        self.selecting_stat_target = True
                        su = self.game.state.stat_ups[i]
                        self.message = f"Selected {su.label} ({su.cost}g) — click a team slot"

                for i, (sx, sy) in enumerate(self.shop_positions):
                    r = pygame.Rect(sx, sy, CARD_W, CARD_H)
                    if r.collidepoint(mx, my):
                        if i not in self.bought_shop_idx:
                            self.selected_shop_idx     = i
                            self.selected_stat_idx     = None
                            self.selecting_stat_target = False
                            card = self.game.state.shop_cards[i]
                            self.message = f"Selected {card.name} — click a slot"

                for slot in self.team_slots:
                    if slot.rect.collidepoint(mx, my):
                        if self.selecting_stat_target and self.selected_stat_idx is not None:
                            self.apply_stat_up(slot.index)
                        elif self.selected_shop_idx is not None:
                            self.buy(self.selected_shop_idx)
                        elif event.button == 3:
                            self.sell(slot.index)

    # ── Drawing ──────────────────────────────────────────────

    def draw(self, screen):
        screen.fill(BACKGROUND_COLOR)

        body = self.game.assets.get_font("body")

        screen.blit(body.render("new cards:", True, GRAY),
                    (MARGIN, MARGIN + 28))
        screen.blit(body.render("stat up:", True, BLUE),
                    (BASE_WIDTH // 2 + MARGIN, MARGIN + 28))

        for i, card in enumerate(self.game.state.shop_cards):
            sx, sy = self.shop_positions[i]
            bought  = i in self.bought_shop_idx
            sel     = (i == self.selected_shop_idx) and not bought
            cv      = CardView(card, sx, sy, selected=sel, greyed=bought)
            cv.draw(screen)

        for i, su in enumerate(self.game.state.stat_ups):
            sx, sy = self.stat_positions[i]
            sel    = (i == self.selected_stat_idx)
            _draw_stat_up(screen, su, sx, sy, sel, body)

        for slot in self.team_slots:
            slot.draw(screen, self.game.state.team[slot.index])

        rc_label = body.render(f"reroll ({self.reroll_cost}g)", True, DARK_GRAY)
        screen.blit(rc_label, (self.reroll_btn.rect.x,
                               self.reroll_btn.rect.y - 28))
        self.reroll_btn.draw(screen)
        self.ready_btn.draw(screen)
        self.stat_box.draw(screen)

        # ── Shop countdown timer (top-right) ─────────────────
        secs = self._seconds_left()
        timer_color = RED if secs <= 10 else DARK_GRAY
        timer_surf  = body.render(f"Shop closes in: {secs}s", True, timer_color)
        timer_rect  = timer_surf.get_rect(topright=(BASE_WIDTH - MARGIN, MARGIN))
        screen.blit(timer_surf, timer_rect)

        if self.message:
            msg = body.render(self.message, True, DARK_GRAY)
            screen.blit(msg, msg.get_rect(
                center=(BASE_WIDTH // 2, BASE_HEIGHT - CARD_H - MARGIN - 80)
            ))


def _draw_stat_up(screen, su, x, y, selected, font):
    rect         = pygame.Rect(x, y, CARD_W, CARD_H)
    border_color = GOLD if selected else BLUE
    border_width = 6    if selected else 3
    pygame.draw.rect(screen, border_color, rect, border_width, border_radius=20)

    label = font.render(su.label,          True, BLACK)
    cost  = font.render(f"{su.cost}g",     True, GOLD)
    screen.blit(label, label.get_rect(center=(rect.centerx, rect.centery - 16)))
    screen.blit(cost,  cost.get_rect( center=(rect.centerx, rect.centery + 20)))
