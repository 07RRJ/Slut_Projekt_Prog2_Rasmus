import pygame
from scenes.base_scene               import BaseScene
from logic.controllers.game_controller import GameController
from ui.button                       import Button
from ui.team_slot                    import TeamSlot
from ui.card_view                    import CardView
from ui.stat_box                     import StatBox
from core.constants                  import *

class ShopScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        self.ctrl = GameController(game)

        if not game.state.shop_cards:
            self.ctrl.refresh_shop()
        if all(c is None for c in game.state.team):
            self.ctrl.refresh_team()

        self.team_slots = [TeamSlot(50 + i * 150, 520, i) for i in range(5)]
        self.reroll_btn = Button((950, 450, 180, 70),  "reroll", self._reroll)
        self.ready_btn  = Button((1150, 450, 180, 70), "ready",  self._ready)
        self.stat_box   = StatBox(game.state)

        self.selected_shop_idx = None
        self.message = ""

    # ── Callbacks ────────────────────────────────────────────

    def _reroll(self):
        if self.ctrl.reroll_shop():
            self.selected_shop_idx = None
            self.message = "Shop rerolled!"
        else:
            self.message = "Not enough gold!"

    def _ready(self):
        """Signal ready; if no match yet, go to matchmaking first."""
        if self.game.state.match is None:
            from scenes.match_making_scene import MatchMakingScene
            self.game.scene_manager.switch_scene(MatchMakingScene(self.game))
        else:
            # Already matched (came back from preview) → signal and poll
            self.ctrl.signal_shop_ready()
            from scenes.waiting_ready_scene import WaitingReadyScene
            self.game.scene_manager.switch_scene(WaitingReadyScene(self.game))

    def _buy(self, shop_idx):
        card = self.game.state.shop_cards[shop_idx]
        from logic.shop_logic import ShopLogic
        slot = ShopLogic.first_free_slot(self.game.state.team)
        if slot is None:
            self.message = "Team full! Sell a card first."
            return
        if self.ctrl.buy_card(card, slot):
            self.message = f"Bought {card.name}!"
            self.selected_shop_idx = None
        else:
            self.message = "Not enough gold!"

    def _sell(self, slot_idx):
        if self.ctrl.sell_card(slot_idx):
            self.message = "Sold for 1 gold."
        else:
            self.message = "No card there."

    # ── Scene interface ──────────────────────────────────────

    def handle_events(self, events):
        for event in events:
            self.reroll_btn.handle_event(event)
            self.ready_btn.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                for i, card in enumerate(self.game.state.shop_cards):
                    cv = CardView(card, 50 + i * 150, 140)
                    if cv.rect.collidepoint(mx, my):
                        self.selected_shop_idx = i
                        self.message = f"Selected {card.name}. Click a slot."

                for slot in self.team_slots:
                    if slot.rect.collidepoint(mx, my):
                        if self.selected_shop_idx is not None:
                            self._buy(self.selected_shop_idx)
                        elif event.button == 3:
                            self._sell(slot.index)

    def draw(self, screen):
        screen.fill(BACKGROUND_COLOR)

        body = self.game.assets.get_font("body")
        screen.blit(body.render("new cards:",  True, GRAY), (50,  100))
        screen.blit(body.render("stat up:",    True, BLUE), (600, 100))

        for i, card in enumerate(self.game.state.shop_cards):
            CardView(card, 50 + i * 150, 140, selected=(i == self.selected_shop_idx)).draw(screen)

        for slot in self.team_slots:
            slot.draw(screen, self.game.state.team[slot.index])

        self.reroll_btn.draw(screen)
        self.ready_btn.draw(screen)
        self.stat_box.draw(screen)

        if self.message:
            screen.blit(body.render(self.message, True, DARK_GRAY), (50, 480))
