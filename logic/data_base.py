import os
from supabase import create_client, Client
from dotenv import load_dotenv
from logic.functions import GetGameFolder

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

    def CreatePlayer(self, user_id: str) -> dict:
        res = self.client.table("player").insert({
            "user_id": user_id,
            "gold": 10, "turn": 1, "health": 10, "status": "shopping"
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

    def GetCardCatalogue(self) -> list:
        res = self.client.table("cards").select("*").execute()
        return res.data

    def BuyCard(self, user_id: str, card_id: str, slot: int) -> dict:
        blueprint = self.client.table("cards") \
            .select("*").eq("id", card_id).single().execute().data
        res = self.client.table("player_cards").insert({
            "user_id": user_id,
            "card_id": card_id,
            "slot": slot,
            "attack": blueprint["base_attack"],
            "health": blueprint["base_health"],
            "level": 1,
        }).execute()
        return res.data[0]

    def GetTeam(self, user_id: str) -> list:
        res = self.client.table("player_cards") \
            .select("*, cards(name, ability)") \
            .eq("user_id", user_id).order("slot").execute()
        return res.data

    def UpgradeCard(self, player_card_id: str, attack: int, level: int) -> None:
        self.client.table("player_cards") \
            .update({"attack": attack, "level": level}) \
            .eq("id", player_card_id).execute()

    def SellCard(self, player_card_id: str) -> None:
        self.client.table("player_cards").delete().eq("id", player_card_id).execute()

    def FindOrCreateMatch(self, user_id: str, turn: int) -> dict:
        return self.client.rpc("find_or_create_match", {
            "p_user_id": user_id,
            "p_turn": turn
        }).execute().data