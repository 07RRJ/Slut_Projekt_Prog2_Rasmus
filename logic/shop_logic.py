import random
from models.card_model import Card

class ShopLogic:

    @staticmethod
    def generate_from_db(db_rows: list) -> list:
        cards = []
        for row in db_rows:
            cards.append(Card(
                id      = row["id"],
                card_id = row["id"],
                name    = row["name"],
                attack  = row["base_attack"],
                health  = row["base_health"],
                level   = 1,
                ability = row.get("ability", ""),
                slot    = -1,   # not placed yet
            ))
        return cards

    @staticmethod
    def can_afford(gold: int, cost: int) -> bool:
        return gold >= cost

    @staticmethod
    def first_free_slot(team: list) -> int | None:
        for i, card in enumerate(team):
            if card is None:
                return i
        return None   # team full