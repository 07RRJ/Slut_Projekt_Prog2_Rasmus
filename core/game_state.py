class GameState:
    def __init__(self):
        self.user_id: str = ""
        self.username: str = "codex"
        self.health: int = 5
        self.gold: int = 10
        self.turn: int = 1
        self.battle_wins: int = 0

        self.team: list = [None] * 5
        self.enemy_team: list = [None] * 5
        self.shop_cards: list = [] # new cards
        self.stat_ups: list = [] # stat upgrades
        self.match: dict|None = None

        self.selected_card = None

    def load_from_db(self, player_row: dict, session: dict) -> None:
        self.user_id = session["user_id"]
        self.username = session["username"]
        if player_row:
            self.health = player_row["health"]
            self.gold = player_row["gold"]
            self.turn = player_row["turn"]
            self.battle_wins = player_row.get("battle_wins", 0)

    def load_team(self, player_cards: list) -> None:
        from models.card_model import Card
        self.team = [None] * 5
        for row in player_cards:
            card_info = row["cards"]
            card = Card(
                id = row["id"],
                card_id = row["card_id"],
                name = card_info["name"],
                attack = row["attack"],
                health = row["health"],
                level = row["level"],
                speed = row["speed"],
                ability = card_info.get("ability", ""),
                slot = row["slot"],
            )
            self.team[row["slot"]] = card

    def load_enemy_team(self, player_cards: list) -> None:
        from models.card_model import Card
        self.enemy_team = [None] * 5
        for row in player_cards:
            card_info = row["cards"]
            card = Card(
                id = row["id"],
                card_id = row["card_id"],
                name = card_info["name"],
                attack = row["attack"],
                health = row["health"],
                level = row["level"],
                speed = row["speed"],
                ability = card_info.get("ability", ""),
                slot = row["slot"],
            )
            self.enemy_team[row["slot"]] = card
