import time
import pygame
from scenes.base_scene import BaseScene
from logic.controllers.game_controller import GameController
from ui.button import Button
from ui.team_slot import TeamSlot
from ui.stat_box import StatBox
from core.constants import *
from ui.cards import *

class ShopScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        self.ctrl = GameController(game)

        if not game.state.shop_cards:
            self.ctrl.refresh_shop()

        self.team_slots = [TeamSlot(my_slot_x(i), my_slot_y(), i)for i in range(5)]

        shop_y = MARGIN + 60
        self.shop_positions = [(MARGIN + i * (CARD_W + CARD_GAP), shop_y) for i in range(3)]

        stat_start_x = MIDDLE_WIDTH + MARGIN
        self.stat_positions = [(stat_start_x + i * (CARD_W + CARD_GAP + 20), shop_y) for i in range(2)]

        btn_y = my_slot_y() - 100
        self.reroll_btn = Button((BASE_WIDTH - 420, btn_y, 180, 70), "reroll", self.reroll)
        self.ready_btn = Button((BASE_WIDTH - 220, btn_y, 180, 70), "ready", self.ready)
        self.stat_box = StatBox(game.state)

        self.selected_shop_idx = None
        self.selected_stat_idx = None
        self.selected_team_slot = None # for card swapping
        self.bought_shop_idx = set()
        self.bought_stat_idx = set()
        self.reroll_cost = 1 # this goes up with +1 per roll
        self.message = ""
        self.selecting_stat_target = False

        self.shop_start = time.time()
        self.auto_ready_fired = False
        self.checkpoint_saved = False # true after it saves in shop at 30 seconds
        # self.elapsed

    def seconds_left(self) -> int:
        return max(0, int(SHOP_TIME_LIMIT - (time.time() - self.shop_start)))

    def elapsed(self) -> float:
        return time.time() - self.shop_start

    def reroll(self): # reroll
        if self.ctrl.reroll_shop(self.reroll_cost):
            self.selected_shop_idx = None
            self.selected_stat_idx = None
            self.selected_team_slot = None
            self.selecting_stat_target = False
            self.bought_shop_idx = set()
            self.bought_stat_idx = set()
            self.reroll_cost += 1
            self.message = f"Rerolled"
        else:
            self.message = f"Not enough gold"

    def ready(self):
        self.clear_selection()
        self.auto_ready_fired = True
        if self.game.state.match is None:
            self.ctrl.push_deck_state()
            from scenes.match_making_scene import MatchMakingScene
            self.game.scene_manager.switch_scene(MatchMakingScene(self.game))
        else:
            self.ctrl.signal_shop_ready()
            from scenes.waiting_ready_scene import WaitingReadyScene
            self.game.scene_manager.switch_scene(WaitingReadyScene(self.game))

    def clear_selection(self):
        self.selected_shop_idx = None
        self.selected_stat_idx = None
        self.selected_team_slot = None
        self.selecting_stat_target = False

    def buy(self, shop_idx, target_slot):
        if shop_idx in self.bought_shop_idx:
            self.message = "Already bought that card"
            return
        card = self.game.state.shop_cards[shop_idx]
        if self.ctrl.buy_card(card, target_slot):
            self.bought_shop_idx.add(shop_idx)
            self.selected_shop_idx = None
            self.message = f"Bought {card.name}"
        else:
            existing = self.game.state.team[target_slot]
            if existing is not None:
                self.message = "That slot is occupied, sell first or pick another slot"
            else:
                self.message = "Not enough gold"

    def sell(self, slot_idx):
        if self.ctrl.sell_card(slot_idx):
            self.message = "Sold for 1 gold"
        else:
            self.message = "No card in that slot"

    def apply_stat_up(self, slot_idx):
        if self.selected_stat_idx in self.bought_stat_idx:
            self.message = "Already used that statup"
            self.clear_selection()
            return
        stat_up = self.game.state.stat_ups[self.selected_stat_idx]
        if self.ctrl.apply_stat_up(stat_up, slot_idx):
            self.bought_stat_idx.add(self.selected_stat_idx)
            self.message = f"Applied {stat_up.label}"
        else:
            self.message = "Cant apply, no card there or not enough gold"
        self.clear_selection()

    def update(self):
        elapsed = self.elapsed()

        if not self.checkpoint_saved and elapsed >= CHECKPOINT_TIME:
            self.checkpoint_saved = True
            try:
                self.ctrl.push_deck_state()
            except Exception as e: # just incase it fails... so it doesnt crash
                pass

        if not self.auto_ready_fired and self.seconds_left() == 0: # ready up automaticly after full shop time
            self.auto_ready_fired = True
            self.message = "Time is up, battle time(="
            self.ready()

    def handle_events(self, events):
        for event in events:
            self.reroll_btn.handle_event(event)
            self.ready_btn.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos

                for i, (sx, sy) in enumerate(self.stat_positions):
                    rect = pygame.Rect(sx, sy, CARD_W, CARD_H)
                    if rect.collidepoint(mx, my):
                        if i in self.bought_stat_idx:
                            self.message = "Already used that statup, reroll for more"
                        else:
                            self.selected_stat_idx = i
                            self.selected_shop_idx = None
                            self.selected_team_slot = None
                            self.selecting_stat_target = True
                            stat_up = self.game.state.stat_ups[i]
                            self.message = f"Selected {stat_up.label} ({stat_up.cost}g), click a team slot"

                for i, (shop_x, shop_y) in enumerate(self.shop_positions):
                    rect = pygame.Rect(shop_x, shop_y, CARD_W, CARD_H)
                    if rect.collidepoint(mx, my):
                        if i not in self.bought_shop_idx:
                            self.selected_shop_idx = i
                            self.selected_stat_idx = None
                            self.selected_team_slot = None
                            self.selecting_stat_target = False
                            card = self.game.state.shop_cards[i]
                            self.message = f"Selected {card.name}, click a team slot to place"

                for slot in self.team_slots:
                    if slot.rect.collidepoint(mx, my):
                        if event.button == 3:
                            self.clear_selection()
                            self.sell(slot.index)

                        elif self.selecting_stat_target and self.selected_stat_idx is not None:
                            self.apply_stat_up(slot.index)

                        elif self.selected_shop_idx is not None:
                            self.buy(self.selected_shop_idx, slot.index)

                        else:
                            if self.selected_team_slot is None:
                                if self.game.state.team[slot.index] is not None:
                                    self.selected_team_slot = slot.index
                                    card = self.game.state.team[slot.index]
                                    self.message = f"Selected {card.name}, click another slot to swap"
                                else:
                                    self.message = "That slot is empty"
                            else:
                                if slot.index == self.selected_team_slot:
                                    self.selected_team_slot = None
                                    self.message = ""
                                else:
                                    if self.ctrl.swap_cards(self.selected_team_slot, slot.index):
                                        self.message = "Cards swapped"
                                    else:
                                        self.message = "Nothing to swap"
                                    self.selected_team_slot = None

    def draw(self, screen):
        screen.fill(BACKGROUND_COLOR)
        body = self.game.assets.get_font("body")

        screen.blit(body.render("new cards:", True, GRAY), (MARGIN, MARGIN))
        screen.blit(body.render("stat up:", True, BLUE), (MIDDLE_WIDTH + MARGIN, MARGIN))

        for i, card in enumerate(self.game.state.shop_cards):
            shop_x, shop_y = self.shop_positions[i]
            bought = i in self.bought_shop_idx
            selected = (i == self.selected_shop_idx) and not bought
            card_view = CardView(card, shop_x, shop_y, selected=selected, greyed=bought)
            card_view.draw(screen)

        for i, stat_up in enumerate(self.game.state.stat_ups):
            shop_x, shop_y = self.stat_positions[i]
            used = i in self.bought_stat_idx
            selected = (i == self.selected_stat_idx) and not used
            stat_up_view = StatUpVeiw(stat_up, shop_x, shop_y, selected, used)
            stat_up_view.draw(screen)

        for slot in self.team_slots:
            swap_hl = (slot.index == self.selected_team_slot)
            slot.draw(screen, self.game.state.team[slot.index], highlight=swap_hl)

        rc_label = body.render(f"reroll ({self.reroll_cost}g)", True, DARK_GRAY)
        screen.blit(rc_label, (self.reroll_btn.rect.x, self.reroll_btn.rect.y - 28))
        self.reroll_btn.draw(screen)
        self.ready_btn.draw(screen)
        self.stat_box.draw(screen)

        seconds = self.seconds_left()
        timer_color = RED if seconds <= 10 else DARK_GRAY
        timer_surf = body.render(f"Shop closes in: {seconds}s", True, timer_color)
        screen.blit(timer_surf, timer_surf.get_rect(topright=(BASE_WIDTH - MARGIN, MARGIN)))

        if self.checkpoint_saved:
            saved = body.render("saved", True, GRAY)
            screen.blit(saved, saved.get_rect(topright=(BASE_WIDTH - MARGIN, MARGIN + 30)))

        if self.message:
            msg = body.render(self.message, True, DARK_GRAY)
            screen.blit(msg, msg.get_rect(center=(MIDDLE_WIDTH, my_slot_y() - 40)))