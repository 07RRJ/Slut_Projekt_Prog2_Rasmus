from logic.shop_logic import ShopLogic

class GameController:
    def __init__(self, game):
        self.game = game          # full Game instance
        self.state = game.state
        self.db = game.db

    def start_run(self) -> None:
        player = self.db.start_run(self.state.user_id)
        self.state.load_from_db(player, {
            "user_id": self.state.user_id,
            "username": self.state.username,
        })
        self.refresh_team()
        self.refresh_shop()

    def refresh_team(self) -> None:
        rows = self.db.get_team(self.state.user_id)
        self.state.load_team(rows)

    def refresh_shop(self) -> None:
        rows = self.db.get_shop_offer(self.state.turn)
        self.state.shop_cards = ShopLogic.generate_from_db(rows)

    def buy_card(self, shop_card, slot: int) -> bool:
        player = self.db.get_player(self.state.user_id)
        cost = 3   # TODO: use shop_card.cost when added to Card model
        if not ShopLogic.can_afford(player["gold"], cost):
            return False
        if self.state.team[slot] is not None:
            return False   # slot occupied

        self.db.buy_card(self.state.user_id, shop_card.card_id, slot)
        self.db.update_player(self.state.user_id, {"gold": player["gold"] - cost})
        self.refresh_team()
        self.state.gold = player["gold"] - cost
        return True

    def sell_card(self, slot: int) -> bool:
        card = self.state.team[slot]
        if card is None:
            return False
        self.db.sell_card(card.id, self.state.user_id)
        self.refresh_team()
        player = self.db.get_player(self.state.user_id)
        self.state.gold = player["gold"]
        return True

    def move_card(self, from_slot: int, to_slot: int) -> bool:
        card = self.state.team[from_slot]
        if card is None or self.state.team[to_slot] is not None:
            return False
        self.db.move_card(card.id, to_slot)
        self.refresh_team()
        return True

    def reroll_shop(self) -> bool:
        if self.db.reroll_shop(self.state.user_id):
            player = self.db.get_player(self.state.user_id)
            self.state.gold = player["gold"]
            self.refresh_shop()
            return True
        return False

    def find_match(self) -> dict:
        match = self.db.find_or_create_match(self.state.user_id, self.state.turn)
        self.state.match = match
        return match

    def poll_match(self) -> dict | None:
        if not self.state.match:
            return None
        match = self.db.get_match(self.state.match["id"])
        self.state.match = match
        return match

    def signal_shop_ready(self) -> None:
        if not self.state.match:
            return
        match = self.db.get_match(self.state.match["id"])
        new_count = match["shop_ready"] + 1
        phase = "battling" if new_count >= 2 else "shopping"
        self.db.client.table("game_manager").update({
            "shop_ready": new_count,
            "phase": phase,
        }).eq("id", match["id"]).execute()
        self.state.match["shop_ready"] = new_count
        self.state.match["phase"] = phase

    def poll_both_ready(self) -> bool:
        match = self.poll_match()
        return match and match["phase"] == "battling"

    def load_enemy_team(self) -> None:
        if not self.state.match:
            return
        my_id = self.state.user_id
        match = self.state.match
        opp_id = match["player2_id"] if match["player1_id"] == my_id else match["player1_id"]
        rows = self.db.get_team(opp_id)
        self.state.load_enemy_team(rows)

    def run_battle(self) -> dict:
        from logic.battle_engine import BattleEngine
        result = BattleEngine.simulate(self.state.team, self.state.enemy_team)

        my_id = self.state.user_id
        match = self.state.match
        opp_id = match["player2_id"] if match["player1_id"] == my_id else match["player1_id"]

        if result["winner"] == "a":
            winner_id = my_id
            i_won = True
        elif result["winner"] == "b":
            winner_id = opp_id
            i_won = False
        else:
            winner_id = None
            i_won = False

        self.db.resolve_match(match["id"], winner_id)

        player = self.db.get_player(my_id)
        new_hp = player["health"] - (0 if i_won or result["winner"] == "draw" else 1)
        new_turn = player["turn"] + 1

        if new_hp <= 0:
            self.db.end_run(my_id, won=False)
        else:
            self.db.update_player(my_id, {
                "health": new_hp,
                "turn": new_turn,
                "gold": 10,
                "status": "shopping",
            })
            self.state.health = new_hp
            self.state.turn = new_turn
            self.state.gold = 10

        return result
