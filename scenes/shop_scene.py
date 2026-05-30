import pygame
from scenes.base_scene import BaseScene
from logic.controllers.game_controller import GameController
from ui.button import Button
from ui.team_slot import TeamSlot
from ui.card_view import CardView
from ui.stat_box import StatBox
from core.constants import *

class ShopScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        self.ctrl = GameController(game)

        if not game.state.shop_cards:
            self.ctrl.refresh_shop()
        if all(card is None for card in game.state.team):
            self.ctrl.refresh_team()

        self.card_pos = [(50 + i * 150, BASE_HEIGHT-230) for i in range(5)]
        self.shop_card_pos = [(50 + i * 150, BASE_HEIGHT-840) for i in range(5)]

        self.team_slots = [TeamSlot(*self.card_pos[i], i) for i in range(5)]
        self.reroll_btn = Button((WIDTH_WITH_MARGIN-500, HEIGHT_WITH_MARGIN-MARGIN-280, 180, 80), "reroll", self.reroll)
        self.ready_btn = Button((WIDTH_WITH_MARGIN-180, HEIGHT_WITH_MARGIN-MARGIN-280, 180, 80), "ready", self.ready)
        self.stat_box = StatBox(game.state)

        self.selected_shop_idx = None
        self.message = ""

    def reroll(self):
        if self.ctrl.reroll_shop():
            self.selected_shop_idx = None
            self.message = "Shop rerolled!"
        else:
            self.message = "Not enough gold!"

    def ready(self):
        if self.game.state.match is None:
            from scenes.match_making_scene import MatchMakingScene
            self.game.scene_manager.switch_scene(MatchMakingScene(self.game))
        else:
            self.ctrl.signal_shop_ready()
            from scenes.waiting_ready_scene import WaitingReadyScene
            self.game.scene_manager.switch_scene(WaitingReadyScene(self.game))

    def buy(self, shop_idx):
        card = self.game.state.shop_cards[shop_idx]
        from logic.shop_logic import ShopLogic
        slot = ShopLogic.first_free_slot(self.game.state.team)
        if slot is None:
            self.message = "Team full! Sell a card first"
            return
        if self.ctrl.buy_card(card, slot):
            self.message = f"Bought {card.name}"
            self.selected_shop_idx = None
        else:
            self.message = "Not enough gold!"

    def sell(self, slot_idx):
        if self.ctrl.sell_card(slot_idx):
            self.message = "Sold for 1 gold"
        else:
            self.message = "No card there"

    def handle_events(self, events):
        for event in events:
            self.reroll_btn.handle_event(event)
            self.ready_btn.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                for i, card in enumerate(self.game.state.shop_cards):
                    card_view = CardView(card, *self.card_pos[i])
                    if card_view.rect.collidepoint(mx, my):
                        self.selected_shop_idx = i
                        self.message = f"Selected {card.name}, click a slot"

                for slot in self.team_slots:
                    if slot.rect.collidepoint(mx, my):
                        if self.selected_shop_idx is not None:
                            self.buy(self.selected_shop_idx)
                        elif event.button == 3:
                            self.sell(slot.index)

    def draw(self, screen):
        screen.fill(BACKGROUND_COLOR)

        body = self.game.assets.get_font("body")
        screen.blit(body.render("new cards:", True, GRAY), (50, 100))
        screen.blit(body.render("stat up:", True, BLUE), (600, 100))

        for i, card in enumerate(self.game.state.shop_cards):
            CardView(card, *self.shop_card_pos[i], selected=(i == self.selected_shop_idx)).draw(screen)

        for slot in self.team_slots:
            slot.draw(screen, self.game.state.team[slot.index])

        self.reroll_btn.draw(screen)
        self.ready_btn.draw(screen)
        self.stat_box.draw(screen)

        if self.message:
            screen.blit(body.render(self.message, True, DARK_GRAY), (50, 480))
