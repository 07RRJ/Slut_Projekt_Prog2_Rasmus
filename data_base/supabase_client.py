import os, random
from supabase import create_client, Client
from dotenv import load_dotenv

GOLD_CAP = 100

def find_env() -> str:
    from pathlib import Path
    p = Path(__file__).resolve().parent
    for _ in range(5):
        candidate = p / ".env"
        if candidate.exists():
            return str(candidate)
        p = p.parent
    return ".env"

class Database:
    def __init__(self):
        load_dotenv(find_env())
        self.client: Client = create_client(
            os.getenv("DATABASE_URL"),
            os.getenv("DATABASE_PASSWORD"),
        )

    # ── Auth ─────────────────────────────────────────────────
    def register(self, username: str, password_hash: str) -> dict | None:
        try:
            res = self.client.table("users").insert({
                "username":      username.upper(),
                "password_hash": password_hash,
            }).execute()
            return res.data[0] if res.data else None
        except Exception:
            return None

    def login(self, username: str) -> dict | None:
        try:
            res = self.client.table("users") \
                .select("*").eq("username", username.upper()).single().execute()
            return res.data
        except Exception:
            return None

    def get_user(self, user_id: str) -> dict | None:
        try:
            res = self.client.table("users") \
                .select("*").eq("id", user_id).single().execute()
            return res.data
        except Exception:
            return None

    def get_leaderboard(self, by: str = "wins", limit: int = 10) -> list:
        res = self.client.table("users") \
            .select("username, wins, losses") \
            .order(by, desc=True).limit(limit).execute()
        return res.data

    # ── Player run ───────────────────────────────────────────
    def start_run(self, user_id: str) -> dict:
        self.delete_player(user_id)
        return self.create_player(user_id)

    def create_player(self, user_id: str) -> dict:
        res = self.client.table("player").insert({
            "user_id": user_id,
            "gold":    10,
            "turn":    1,
            "health":  10,
            "status":  "shopping",
        }).execute()
        return res.data[0]

    def get_player(self, user_id: str) -> dict | None:
        try:
            res = self.client.table("player") \
                .select("*").eq("user_id", user_id).single().execute()
            return res.data
        except Exception:
            return None

    def update_player(self, user_id: str, fields: dict) -> None:
        # Enforce gold cap before writing
        if "gold" in fields:
            fields["gold"] = min(fields["gold"], GOLD_CAP)
        self.client.table("player").update(fields).eq("user_id", user_id).execute()

    def delete_player(self, user_id: str) -> None:
        self.client.table("player").delete().eq("user_id", user_id).execute()

    def end_run(self, user_id: str, won: bool) -> None:
        user = self.get_user(user_id)
        if user:
            key = "wins" if won else "losses"
            self.client.table("users") \
                .update({key: user[key] + 1}).eq("id", user_id).execute()
        self.delete_player(user_id)

    # ── Shop ─────────────────────────────────────────────────
    def get_shop_offer(self, turn: int, count: int = 3) -> list:
        max_tier = min(1 + turn // 3, 6)
        res = self.client.table("cards") \
            .select("*").lte("tier", max_tier).execute()
        pool = res.data or []
        return random.sample(pool, min(count, len(pool)))

    def get_card_catalogue(self) -> list:
        return self.client.table("cards").select("*").execute().data

    # ── Cards ────────────────────────────────────────────────
    def buy_card(self, user_id: str, card_id: str, slot: int) -> dict:
        # Check for mergeable copy already in team
        existing = self.client.table("player_cards") \
            .select("*").eq("user_id", user_id).eq("card_id", card_id) \
            .lt("level", 3).limit(1).execute()

        if existing.data:
            card = existing.data[0]
            self.client.table("player_cards").update({
                "level":  card["level"]  + 1,
                "attack": card["attack"] + 1,
                "health": card["health"] + 1,
            }).eq("id", card["id"]).execute()
            return {"merged": True, "card": card}

        blueprint = self.client.table("cards") \
            .select("*").eq("id", card_id).single().execute().data

        res = self.client.table("player_cards").insert({
            "user_id": user_id,
            "card_id": card_id,
            "slot":    slot,
            "attack":  blueprint["base_attack"],
            "health":  blueprint["base_health"],
            "speed":   blueprint["speed"],
            "level":   1,
        }).execute()
        return {"merged": False, "card": res.data[0]}

    def apply_stat_up(self, user_id: str, player_card_id: str,
                      d_attack: int, d_health: int, d_speed: int) -> None:
        """Apply a stat-up item to a player card already in the team."""
        res = self.client.table("player_cards") \
            .select("attack, health, speed") \
            .eq("id", player_card_id).single().execute().data
        new_speed = max(1, res["speed"] + d_speed)   # speed floor = 1
        self.client.table("player_cards").update({
            "attack": res["attack"] + d_attack,
            "health": res["health"] + d_health,
            "speed":  new_speed,
        }).eq("id", player_card_id).execute()

    def sell_card(self, player_card_id: str, user_id: str) -> None:
        self.client.table("player_cards").delete().eq("id", player_card_id).execute()
        player = self.get_player(user_id)
        if player:
            self.update_player(user_id, {"gold": player["gold"] + 1})

    def move_card(self, player_card_id: str, new_slot: int) -> None:
        self.client.table("player_cards") \
            .update({"slot": new_slot}).eq("id", player_card_id).execute()

    def get_team(self, user_id: str) -> list:
        # include speed from both player_cards and cards blueprint
        res = self.client.table("player_cards") \
            .select("*, cards(name, ability, cost, speed)") \
            .eq("user_id", user_id).order("slot").execute()
        return res.data

    def reroll_shop(self, user_id: str, reroll_cost: int) -> bool:
        player = self.get_player(user_id)
        if not player or player["gold"] < reroll_cost:
            return False
        self.update_player(user_id, {"gold": player["gold"] - reroll_cost})
        return True

    # ── Matchmaking ──────────────────────────────────────────
    def find_or_create_match(self, user_id: str, turn: int) -> dict:
        return self.client.rpc("find_or_create_match", {
            "p_user_id": user_id,
            "p_turn":    turn,
        }).execute().data

    def get_match(self, match_id: str) -> dict | None:
        try:
            res = self.client.table("game_manager") \
                .select("*").eq("id", match_id).single().execute()
            return res.data
        except Exception:
            return None

    def resolve_match(self, match_id: str, winner_id: str | None) -> None:
        self.client.table("game_manager").update({
            "phase":     "done",
            "winner_id": winner_id,
        }).eq("id", match_id).execute()
