import os
import random
from supabase import create_client, Client
from dotenv import load_dotenv
from general.functions import GetGameFolder

class Database:
    def __init__(self):
        load_dotenv(GetGameFolder() + "/.env")
        self.client: Client = create_client(
            os.getenv("DATABASE_URL"),
            os.getenv("DATABASE_PASSWORD")
        )

    def Register(self, username: str, password_hash: str) -> dict | None:
        res = self.client.table("users").insert({
            "username": username.upper(),
            "password_hash": password_hash
        }).execute()
        return res.data[0] if res.data else None

    def Login(self, username: str) -> dict | None:
        res = self.client.table("users") \
            .select("*").eq("username", username.upper()).single().execute()
        return res.data

    def GetUser(self, user_id: str) -> dict | None:
        res = self.client.table("users") \
            .select("*").eq("id", user_id).single().execute()
        return res.data

    def GetLeaderboard(self, by: str = "wins", limit: int = 10) -> list:
        res = self.client.table("users") \
            .select("username, wins, losses") \
            .order(by, desc=True).limit(limit).execute()
        return res.data

    def StartRun(self, user_id: str) -> dict:
        self.DeletePlayer(user_id)
        return self.CreatePlayer(user_id)

    def CreatePlayer(self, user_id: str) -> dict:
        res = self.client.table("player").insert({
            "user_id": user_id,
            "gold": 10,
            "turn": 1,
            "health": 10,
            "status": "shopping"
        }).execute()
        return res.data[0]

    def GetPlayer(self, user_id: str) -> dict | None:
        res = self.client.table("player") \
            .select("*").eq("user_id", user_id).single().execute()
        return res.data

    def UpdatePlayer(self, user_id: str, fields: dict) -> None:
        self.client.table("player").update(fields).eq("user_id", user_id).execute()

    def DeletePlayer(self, user_id: str) -> None:
        self.client.table("player").delete().eq("user_id", user_id).execute()

    def GetShopOffer(self, turn: int, count: int = 5) -> list:
        max_tier = min(1 + turn // 3, 6)
        res = self.client.table("cards") \
            .select("*").lte("tier", max_tier).execute()
        return random.sample(res.data, min(count, len(res.data)))

    def GetCardCatalogue(self) -> list:
        res = self.client.table("cards").select("*").execute()
        return res.data

    def BuyCard(self, user_id: str, card_id: str, slot: int) -> dict:
        existing = self.client.table("player_cards") \
            .select("*") \
            .eq("user_id", user_id) \
            .eq("card_id", card_id) \
            .lt("level", 3) \
            .limit(1).execute()

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
            "level":   1,
        }).execute()
        return {"merged": False, "card": res.data[0]}

    def SellCard(self, player_card_id: str, user_id: str) -> None:
        self.client.table("player_cards").delete() \
            .eq("id", player_card_id).execute()
        player = self.GetPlayer(user_id)
        self.UpdatePlayer(user_id, {"gold": player["gold"] + 1})

    def MoveCard(self, player_card_id: str, new_slot: int) -> None:
        self.client.table("player_cards") \
            .update({"slot": new_slot}).eq("id", player_card_id).execute()

    def UpgradeCard(self, player_card_id: str, attack: int, level: int) -> None:
        self.client.table("player_cards") \
            .update({"attack": attack, "level": level}) \
            .eq("id", player_card_id).execute()

    def GetTeam(self, user_id: str) -> list:
        res = self.client.table("player_cards") \
            .select("*, cards(name, ability, cost)") \
            .eq("user_id", user_id).order("slot").execute()
        return res.data

    def RerollShop(self, user_id: str) -> bool:
        player = self.GetPlayer(user_id)
        if player["gold"] < 1:
            return False
        self.UpdatePlayer(user_id, {"gold": player["gold"] - 1})
        return True

    def FindOrCreateMatch(self, user_id: str, turn: int) -> dict:
        return self.client.rpc("find_or_create_match", {
            "p_user_id": user_id,
            "p_turn":    turn
        }).execute().data

    def GetMatch(self, match_id: str) -> dict | None:
        res = self.client.table("game_manager") \
            .select("*").eq("id", match_id).single().execute()
        return res.data

    def ResolveMatch(self, match_id: str, winner_id: str | None) -> None:
        self.client.table("game_manager").update({
            "status":    "done",
            "winner_id": winner_id
        }).eq("id", match_id).execute()

    def EndRun(self, user_id: str, won: bool) -> None:
        user = self.GetUser(user_id)
        if won:
            self.client.table("users") \
                .update({"wins": user["wins"] + 1}).eq("id", user_id).execute()
        else:
            self.client.table("users") \
                .update({"losses": user["losses"] + 1}).eq("id", user_id).execute()
        self.DeletePlayer(user_id)