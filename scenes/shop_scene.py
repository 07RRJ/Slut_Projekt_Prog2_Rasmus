import pygame
from scenes.base_scene import BaseScene
from ui.button import Button
from ui.team_slot import TeamSlot
from ui.stat_box import StatBox
from ui.card_view import CardView
from logic.controllers.game_controller import GameController

class ShopScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)

        self.controller = GameController(game.state)

        self.controller.start_game()

        self.team_slots = []

        start_x = 50

        for i in range(5):
            slot = TeamSlot(
                start_x + i * 150,
                520,
                i
            )

            self.team_slots.append(slot)

        self.reroll_button = Button(
            (950, 450, 180, 80),
            "reroll",
            self.controller.reroll_shop
        )

        self.ready_button = Button(
            (1150, 450, 180, 80),
            "ready",
            self.ready
        )

        self.stat_box = StatBox(game.state)

    def ready(self):
        print("READY")

    def handle_events(self, events):
        for event in events:
            self.reroll_button.handle_event(event)
            self.ready_button.handle_event(event)

    def update(self):
        pass

    def draw(self, screen):
        for slot in self.team_slots:
            slot.draw(screen)

        self.reroll_button.draw(screen)
        self.ready_button.draw(screen)

        self.stat_box.draw(screen)

        start_x = 50

        for i, card in enumerate(self.game.state.shop_cards):
            card_view = CardView(
                card,
                start_x + i * 150,
                140
            )

            card_view.draw(screen)