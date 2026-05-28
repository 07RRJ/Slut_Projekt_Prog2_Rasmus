from logic.shop_logic import ShopLogic

class GameController:
    def __init__(self, state):
        self.state = state

    def reroll_shop(self):
        self.state.shop_cards = ShopLogic.generate_shop()

    def start_game(self):
        self.reroll_shop()

    def add_card_to_team(self, card, slot_index):
        self.state.team[slot_index] = card