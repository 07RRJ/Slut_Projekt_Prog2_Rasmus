import random
from models.card_model import Card

STAT_UP_POOL = [
    ("+1 ATK", 1, 0, 0, 3),
    ("+2 ATK", 2, 0, 0, 4),
    ("+3 ATK", 3, 0, 0, 5),
    ("+1 HP", 0, 1, 0, 3),
    ("+2 HP", 0, 2, 0, 4),
    ("+3 HP", 0, 3, 0, 5),
    ("-1 SPD", 0, 0, -1, 3),
    ("-2 SPD", 0, 0, -2, 4),
    ("-3 SPD", 0, 0, -3, 5),
]

class StatUp:
    def __init__(self, label: str, d_attack: int, d_health: int, d_speed: int, cost: int):
        self.label = label
        self.d_attack = d_attack
        self.d_health = d_health
        self.d_speed = d_speed
        self.cost = cost

class ShopLogic:
    @staticmethod
    def generate_from_db(db_rows: list) -> list: # take db make the cards
        cards = []
        for row in db_rows:
            cards.append(Card(
                id = row["id"],
                card_id = row["id"],
                name = row["name"],
                attack = row["base_attack"],
                health = row["base_health"],
                level = 1,
                speed = row.get("speed", 5),
                ability = row.get("ability", ""),
                slot = -1,
            ))
        return cards

    @staticmethod
    def generate_stat_ups(count: int = 2) -> list: # get random random stat uppgrades and unpack them
        return [StatUp(*entry) for entry in random.sample(STAT_UP_POOL, min(count, len(STAT_UP_POOL)))]

    @staticmethod # broke?
    def can_afford(gold: int, cost: int) -> bool:
        return gold >= cost
