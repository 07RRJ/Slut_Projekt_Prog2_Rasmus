class GameState:
    def __init__(self):
        self.username = "codex"

        self.health = 5
        self.gold = 5
        self.turn = 1

        self.team = [None] * 5
        self.enemy_team = [None] * 5

        self.shop_cards = []

        self.selected_card = None