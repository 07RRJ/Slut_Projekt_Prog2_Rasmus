from logic.shop_logic import ShopLogic

class GameController:
    def __init__(self, game):
        self.game  = game
        self.state = game.state
        self.db    = game.db

    # ── Run lifecycle ────────────────────────────────────────
    def start_run(self) -> None:
        player = self.db.start_run(self.state.user_id)
        self.state.load_from_db(player, {
            "user_id":  self.state.user_id,
            "username": self.state.username,
        })
        self.state.match = None
        self.refresh_team()
        self.refresh_shop()

    def refresh_team(self) -> None:
        rows = self.db.get_team(self.state.user_id)
        self.state.load_team(rows)

    def refresh_shop(self) -> None:
        rows = self.db.get_shop_offer(self.state.turn)
        self.state.shop_cards = ShopLogic.generate_from_db(rows)
        self.state.stat_ups   = ShopLogic.generate_stat_ups(2)

    # ── Shop actions ─────────────────────────────────────────
    def buy_card(self, shop_card, slot: int) -> bool:
        player = self.db.get_player(self.state.user_id)
        cost   = getattr(shop_card, "cost", 3)
        if not ShopLogic.can_afford(player["gold"], cost):
            return False
        if self.state.team[slot] is not None:
            return False

        self.db.buy_card(self.state.user_id, shop_card.card_id, slot)
        self.db.update_player(self.state.user_id, {"gold": player["gold"] - cost})
        self.refresh_team()
        self.state.gold = min(player["gold"] - cost, 100)
        return True

    def apply_stat_up(self, stat_up, target_slot: int) -> bool:
        """Apply a StatUp item to the card in target_slot."""
        card = self.state.team[target_slot]
        if card is None:
            return False
        player = self.db.get_player(self.state.user_id)
        if not ShopLogic.can_afford(player["gold"], stat_up.cost):
            return False

        self.db.apply_stat_up(
            self.state.user_id, card.id,
            stat_up.d_attack, stat_up.d_health, stat_up.d_speed,
        )
        self.db.update_player(self.state.user_id, {"gold": player["gold"] - stat_up.cost})
        self.refresh_team()
        self.state.gold = min(player["gold"] - stat_up.cost, 100)
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

    def reroll_shop(self, reroll_cost: int) -> bool:
        if self.db.reroll_shop(self.state.user_id, reroll_cost):
            player = self.db.get_player(self.state.user_id)
            self.state.gold = player["gold"]
            self.refresh_shop()
            return True
        return False

    # ── Matchmaking ──────────────────────────────────────────
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
        updated = self.db.client.rpc(
            "player_ready", {"p_match_id": self.state.match["id"]}
        ).execute().data
        self.state.match = updated

    def poll_both_ready(self) -> bool:
        match = self.poll_match()
        return bool(match and match["phase"] == "battling")

    def load_enemy_team(self) -> None:
        if not self.state.match:
            return
        my_id  = self.state.user_id
        match  = self.state.match
        opp_id = match["player2_id"] if match["player1_id"] == my_id else match["player1_id"]
        rows   = self.db.get_team(opp_id)
        self.state.load_enemy_team(rows)

    # ── Battle ───────────────────────────────────────────────
    def run_battle(self) -> dict:
        from logic.battle_engine import BattleEngine
        result = BattleEngine.simulate(self.state.team, self.state.enemy_team)

        my_id  = self.state.user_id
        match  = self.state.match
        opp_id = match["player2_id"] if match["player1_id"] == my_id else match["player1_id"]

        if result["winner"] == "a":
            winner_id, i_won = my_id, True
        elif result["winner"] == "b":
            winner_id, i_won = opp_id, False
        else:
            winner_id, i_won = None, False

        # Only player1 writes the match result to avoid double-write
        if match["player1_id"] == my_id:
            self.db.resolve_match(match["id"], winner_id)

        player   = self.db.get_player(my_id)
        new_hp   = player["health"] - (0 if i_won or result["winner"] == "draw" else 1)
        new_turn = player["turn"] + 1
        # Gold carries over; just add the turn income (10), capped at 100
        new_gold = min(player["gold"] + 10, 100)

        if new_hp <= 0:
            self.db.end_run(my_id, won=False)
        else:
            self.db.update_player(my_id, {
                "health": new_hp,
                "turn":   new_turn,
                "gold":   new_gold,
                "status": "shopping",
            })
            self.state.health = new_hp
            self.state.turn   = new_turn
            self.state.gold   = new_gold
            self.state.match  = None   # clear so next shop → fresh matchmaking

        return result
