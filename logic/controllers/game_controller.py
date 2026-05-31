from logic.shop_logic import ShopLogic
from models.card_model import Card
import copy

GOLD_CAP = 100
GOAL_TURN = 10  # Win requirement: reach turn 10

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
        """Load team from DB — only called at run start / after battle."""
        rows = self.db.get_team(self.state.user_id)
        self.state.load_team(rows)

    def refresh_shop(self) -> None:
        rows = self.db.get_shop_offer(self.state.turn)
        self.state.shop_cards = ShopLogic.generate_from_db(rows)
        self.state.stat_ups   = ShopLogic.generate_stat_ups(2)

    # ── Deck push ────────────────────────────────────────────
    def push_deck_state(self) -> None:
        """Flush the in-memory team to the DB. Called at: ready, auto-ready, 30s checkpoint."""
        self.db.push_deck_state(self.state.user_id, self.state.team)
        self.db.update_player(self.state.user_id, {"gold": self.state.gold})

    # ── Local-only shop actions (NO DB calls) ────────────────
    def buy_card(self, shop_card, slot: int) -> bool:
        """
        Buy a card into a specific slot — pure in-memory, no DB.
        Returns False if can't afford or slot is occupied by a different card.
        Merges if same card_id exists at <level 3 anywhere in team.
        """
        cost = getattr(shop_card, "cost", 3)
        if not ShopLogic.can_afford(self.state.gold, cost):
            return False

        # First: search ALL slots for a mergeable card (same card_id, level < 3)
        for i, existing in enumerate(self.state.team):
            if existing is not None and existing.card_id == shop_card.card_id and existing.level < 3:
                existing.level  += 1
                existing.attack += 1
                existing.health += 1
                self.state.gold -= cost
                return True

        # Second: check if target slot is empty
        if self.state.team[slot] is not None:
            return False  # slot occupied by a different card

        # Third: place new card in the slot
        new_card = Card(
            id      = f"local_{slot}_{shop_card.card_id}",
            card_id = shop_card.card_id,
            name    = shop_card.name,
            attack  = shop_card.attack,
            health  = shop_card.health,
            level   = 1,
            speed   = shop_card.speed,
            ability = shop_card.ability,
            slot    = slot,
        )
        self.state.team[slot] = new_card
        self.state.gold -= cost
        return True

    def sell_card(self, slot: int) -> bool:
        """Sell card at slot — pure in-memory."""
        card = self.state.team[slot]
        if card is None:
            return False
        self.state.team[slot] = None
        self.state.gold = min(self.state.gold + 1, GOLD_CAP)
        return True

    def apply_stat_up(self, stat_up, target_slot: int) -> bool:
        """Apply a StatUp to a card — pure in-memory."""
        card = self.state.team[target_slot]
        if card is None:
            return False
        if not ShopLogic.can_afford(self.state.gold, stat_up.cost):
            return False
        card.attack = card.attack + stat_up.d_attack
        card.health = card.health + stat_up.d_health
        card.speed  = max(1, card.speed + stat_up.d_speed)
        self.state.gold -= stat_up.cost
        return True

    def swap_cards(self, slot_a: int, slot_b: int) -> bool:
        """Swap two team slots — pure in-memory, instant."""
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

    def reroll_shop(self, reroll_cost: int) -> bool:
        """Reroll the shop offer — deducts gold locally, refreshes shop from DB."""
        if not ShopLogic.can_afford(self.state.gold, reroll_cost):
            return False
        self.state.gold -= reroll_cost
        self.refresh_shop()
        return True

    # ── Matchmaking ──────────────────────────────────────────
    def find_match(self) -> dict:
        self.db.cleanup_stale_data(self.state.user_id)
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
        """Push deck state then signal ready — the two things that must happen together."""
        self.push_deck_state()
        if not self.state.match:
            return
        try:
            updated = self.game.db.client.rpc(
                "player_ready", {"p_match_id": self.state.match["id"]}
            ).execute().data
            if updated:
                self.state.match = updated
            else:
                print("ERROR: player_ready RPC returned empty!")
                print("SOLUTION: Run this SQL in your Supabase editor:")
                print("""
CREATE OR REPLACE FUNCTION player_ready(p_match_id uuid)
RETURNS json LANGUAGE plpgsql AS $$
DECLARE result json;
BEGIN
  UPDATE game_manager
  SET shop_ready = shop_ready + 1,
      phase = CASE WHEN shop_ready + 1 >= 2 THEN 'battling' ELSE phase END
  WHERE id = p_match_id;
  SELECT row_to_json(g) INTO result FROM game_manager g WHERE id = p_match_id;
  RETURN result;
END; $$;
                """)
        except Exception as e:
            print(f"ERROR calling player_ready RPC: {e}")
            print("SOLUTION: Make sure you've run the db.sql script in Supabase to create the function.")

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
        """Run battle simulation and handle results. Returns result dict."""
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

        if match["player1_id"] == my_id:
            self.db.resolve_match(match["id"], winner_id)

        player   = self.db.get_player(my_id)
        new_hp   = player["health"] - (0 if i_won or result["winner"] == "draw" else 1)
        new_turn = player["turn"] + 1

        # Check if we reached the goal
        if new_turn > GOAL_TURN:
            # Goal reached! End the run successfully
            self.db.end_run(my_id, won=True)
            result["goal_reached"] = True
            return result

        if new_hp <= 0:
            # Health depleted — run ends in failure
            self.db.end_run(my_id, won=False)
            result["run_ended"] = True
            return result

        # Run continues to next turn
        new_gold = min(player["gold"] + 10, 100)
        self.db.update_player(my_id, {
            "health": new_hp,
            "turn":   new_turn,
            "gold":   new_gold,
            "status": "shopping",
        })
        self.state.health = new_hp
        self.state.turn   = new_turn
        self.state.gold   = new_gold
        self.state.match  = None

        return result
