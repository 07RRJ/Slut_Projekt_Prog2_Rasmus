import os, random
from supabase import create_client, Client
from dotenv import load_dotenv
from core.constants import *

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

    def register(self, username: str, password_hash: str) -> dict | None: # make new acc
        try:
            res = self.client.table("users").insert({
                "username": username.upper(),
                "password_hash": password_hash,
            }).execute()
            return res.data[0] if res.data else None
        except Exception:
            return None

    def login(self, username: str) -> dict | None: # login....
        try:
            res = self.client.table("users") \
                .select("*").eq("username", username.upper()).single().execute()
            return res.data
        except Exception:
            return None

    def get_user(self, user_id: str) -> dict | None: # get a ser from user id
        try:
            res = self.client.table("users") \
                .select("*").eq("id", user_id).single().execute()
            return res.data
        except Exception:
            return None

    # def get_leaderboard(self, by: str = "wins", limit: int = 10) -> list: # tried implementing it but dont have enugh time
    #     res = self.client.table("users") \
    #         .select("username, wins, losses") \
    #         .order(by, desc=True).limit(limit).execute()
    #     return res.data

    def cleanup_stale_data(self, user_id: str) -> None: # remove old games to avoid "false" matches (user not there but game not done)
        try:
            self.client.table("player").delete() \
                .eq("user_id", user_id) \
                .lt("created_at", "now() - interval '2 hours'") \
                .execute()
            self.client.table("game_manager").delete() \
                .eq("player1_id", user_id) \
                .in_("phase", ["waiting", "previewing", "shopping"]) \
                .lt("created_at", "now() - interval '2 hours'") \
                .execute()
        except Exception:
            pass

    def force_cleanup_player(self, user_id: str) -> None: # no re enter glitch, if you dissconect progress bye bye
        self.client.table("player_cards").delete().eq("user_id", user_id).execute()
        self.client.table("player").delete().eq("user_id", user_id).execute()

    def start_run(self, user_id: str) -> dict: # "PLAY"
        self.force_cleanup_player(user_id)
        return self.create_player(user_id)

    def create_player(self, user_id: str) -> dict: # make player data on db
        res = self.client.table("player").insert({
            "user_id": user_id,
            "gold": 10,
            "turn": 1,
            "health": 5,
            "status": "shopping", # start in shop then (match making > preview > shop > battle)
        }).execute()
        return res.data[0]

    def get_player(self, user_id: str) -> dict | None: # player data instead of user
        try:
            res = self.client.table("player") \
                .select("*").eq("user_id", user_id).single().execute()
            return res.data
        except Exception:
            return None

    def update_player(self, user_id: str, fields: dict) -> None: # update db player
        if "gold" in fields:
            fields["gold"] = min(fields["gold"], GOLD_CAP)
        self.client.table("player").update(fields).eq("user_id", user_id).execute()

    def delete_player(self, user_id: str) -> None: # remove player and cascade
        self.client.table("player_cards").delete().eq("user_id", user_id).execute()
        self.client.table("player").delete().eq("user_id", user_id).execute()

    def end_run(self, user_id: str, won: bool) -> None: # add win or loss to db user
        user = self.get_user(user_id)
        if user:
            key = "wins" if won else "losses"
            self.client.table("users") \
                .update({key: user[key] + 1}).eq("id", user_id).execute()
        self.delete_player(user_id)

    def push_deck_state(self, user_id: str, team: list) -> None: # fix deck
        self.client.table("player_cards").delete().eq("user_id", user_id).execute()
        rows = []
        for card in team:
            if card is None:
                continue
            rows.append({
                "user_id": user_id,
                "card_id": card.card_id,
                "slot": card.slot,
                "attack": card.attack,
                "health": card.health,
                "speed": card.speed,
                "level": card.level,
            })
        if rows:
            self.client.table("player_cards").insert(rows).execute()

    def get_shop_offer(self, turn: int, count: int = 3) -> list: # give shop stuff
        max_tier = min(1 + turn // 3, 6) # could add rare cards later because i dont have enugh time
        res = self.client.table("cards") \
            .select("*").lte("tier", max_tier).execute()
        pool = res.data or []
        return random.sample(pool, min(count, len(pool)))

    def get_card_catalogue(self) -> list: # havent made codex or card skills so this should be a waste of space
        return self.client.table("cards").select("*").execute().data

    def get_team(self, user_id: str) -> list: # get team
        res = self.client.table("player_cards") \
            .select("*, cards(name, ability, cost, speed)") \
            .eq("user_id", user_id).order("slot").execute()
        return res.data

    def find_or_create_match(self, user_id: str, turn: int) -> dict: # if no match creat match else join same turn
        return self.client.rpc("find_or_create_match", {
            "p_user_id": user_id,
            "p_turn": turn,
        }).execute().data

    def get_match(self, match_id: str) -> dict | None: # get a match
        try:
            res = self.client.table("game_manager") \
                .select("*").eq("id", match_id).single().execute()
            return res.data
        except Exception:
            return None

    def force_phase(self, match_id: str, phase: str) -> None: # change phase if player 1 doesnt do it
        try:
            self.client.table("game_manager") \
                .update({"phase": phase}) \
                .eq("id", match_id).execute()
        except Exception:
            pass

    def resolve_match(self, match_id: str, winner_id: str | None) -> None: # when the match is done
        self.client.table("game_manager").update({
            "phase": "done",
            "winner_id": winner_id,
        }).eq("id", match_id).execute()

    def p1_last_seen(self, match_id: str) -> float | None: # a way to detect player 1 inactivity
        try:
            match = self.get_match(match_id)
            if not match:
                return None
            p1_id = match["player1_id"]
            res = self.client.table("player") \
                .select("last_seen").eq("user_id", p1_id).single().execute()
            last_seen_str = res.data.get("last_seen")
            if not last_seen_str:
                return None
            from datetime import datetime, timezone
            last_seen = datetime.fromisoformat(last_seen_str.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            return (now - last_seen).total_seconds()
        except Exception:
            return None
