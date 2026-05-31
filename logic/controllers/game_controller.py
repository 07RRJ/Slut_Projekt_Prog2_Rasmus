from logic.shop_logic import ShopLogic
from models.card_model import Card
from core.constants import *
import copy

class GameController:
    def __init__(self, game):
        self.game = game
        self.state = game.state
        self.db = game.db

    def start_run(self) -> None: # start local and db stuff
        player = self.db.start_run(self.state.user_id)
        self.state.load_from_db(player, {
            "user_id": self.state.user_id,
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
        self.state.stat_ups = ShopLogic.generate_stat_ups(2)

    def push_deck_state(self) -> None: # tincy auto save system during battle to push deck changes when called at 30 sec intervals
        self.db.push_deck_state(self.state.user_id, self.state.team)
        self.db.update_player(self.state.user_id, {"gold": self.state.gold})

    def buy_card(self, shop_card, slot: int) -> bool: # try to buy a card from shop
        cost = getattr(shop_card, "cost", 3) # i could add specific card costs and that and that.... no all for 3
        if not ShopLogic.can_afford(self.state.gold, cost):
            return False

        for i, existing in enumerate(self.state.team): # enumenumnum
            if existing is not None and existing.card_id == shop_card.card_id and existing.level < 3:
                existing.level += 1
                existing.attack += 1
                existing.health += 1
                self.state.gold -= cost
                return True

        if self.state.team[slot] is not None:
            return False # slot is taken

        new_card = Card(
            id = f"local_{slot}_{shop_card.card_id}", # good way to make a string for something specific, just explain it while making it(=
            card_id = shop_card.card_id,
            name = shop_card.name,
            attack = shop_card.attack,
            health = shop_card.health,
            level = 1,
            speed = shop_card.speed,
            ability = shop_card.ability,
            slot = slot,
        )
        self.state.team[slot] = new_card
        self.state.gold -= cost
        return True

    def sell_card(self, slot: int) -> bool: 
        card = self.state.team[slot]
        if card is None:
            return False
        self.state.team[slot] = None
        self.state.gold = min(self.state.gold + 1, GOLD_CAP)
        return True

    def apply_stat_up(self, stat_up, target_slot: int) -> bool: # make a card stronger (hp, dmg, speed)
        card = self.state.team[target_slot]
        if card is None:
            return False
        if not ShopLogic.can_afford(self.state.gold, stat_up.cost):
            return False
        card.attack = card.attack + stat_up.d_attack
        card.health = card.health + stat_up.d_health
        card.speed = max(1, card.speed + stat_up.d_speed) # min 1 speed (to count ticks, low = good)
        self.state.gold -= stat_up.cost
        return True

    def swap_cards(self, slot_a: int, slot_b: int) -> bool: # swap card slots
        card_a = self.state.team[slot_a]
        card_b = self.state.team[slot_b]
        if card_a is None and card_b is None:
            return False
        self.state.team[slot_a] = card_b
        self.state.team[slot_b] = card_a
        if card_a is not None:
            card_a.slot = slot_b
        if card_b is not None:
            card_b.slot = slot_a
        return True

    def reroll_shop(self, reroll_cost: int) -> bool: # get new offers
        if not ShopLogic.can_afford(self.state.gold, reroll_cost):
            return False
        self.state.gold -= reroll_cost # where do i increese this?
        self.refresh_shop()
        return True

    def find_match(self) -> dict: # remove old data and get new match from db
        self.db.cleanup_stale_data(self.state.user_id)
        match = self.db.find_or_create_match(self.state.user_id, self.state.turn)
        self.state.match = match
        return match

    def poll_match(self) -> dict | None: # get the match
        if not self.state.match:
            return None
        match = self.db.get_match(self.state.match["id"])
        self.state.match = match
        return match

    def signal_shop_ready(self) -> None: # inform that shop is ready
        self.push_deck_state()
        if not self.state.match:
            return
        try:
            updated = self.game.db.client.rpc(
                "player_ready", {"p_match_id": self.state.match["id"]}
            ).execute().data
            if updated:
                self.state.match = updated
        except Exception as e:
            # print(e)
            pass

    def poll_both_ready(self) -> bool:
        match = self.poll_match()
        return bool(match and match["phase"] == "battling")

    def load_enemy_team(self) -> None: # opponent dech
        if not self.state.match:
            return
        my_id = self.state.user_id
        match = self.state.match
        opp_id = match["player2_id"] if match["player1_id"] == my_id else match["player1_id"]
        rows = self.db.get_team(opp_id)
        self.state.load_enemy_team(rows)

    def run_battle(self) -> dict: # based on data from db call battle simulation and use "result"
        from logic.battle_engine import BattleEngine
        result = BattleEngine.simulate(self.state.team, self.state.enemy_team)

        my_id = self.state.user_id
        match = self.state.match
        opp_id = match["player2_id"] if match["player1_id"] == my_id else match["player1_id"]

        if result["winner"] == "a":
            winner_id, i_won = my_id, True
        elif result["winner"] == "b":
            winner_id, i_won = opp_id, False
        else:
            winner_id, i_won = None, False

        if match["player1_id"] == my_id:
            self.db.resolve_match(match["id"], winner_id)

        player = self.db.get_player(my_id)
        new_hp = player["health"] - (0 if i_won or result["winner"] == "draw" else 1)
        new_turn = player["turn"] + 1
        new_wins = player.get("battle_wins", 0) + (1 if i_won else 0)

        if new_wins >= WIN_GOAL:
            self.db.end_run(my_id, won=True)
            result["goal_reached"] = True
            return result

        elif new_hp <= 0:
            self.db.end_run(my_id, won=False)
            result["run_ended"] = True
            return result

        self.db.update_player(my_id, {
            "health": new_hp,
            "turn": new_turn,
            "battle_wins": new_wins,
        })
        self.state.health = new_hp
        self.state.turn = new_turn
        self.state.battle_wins = new_wins
        self.state.match = None

        return result
