import random
from models.card_model import Card

CARD_POOL = [
    Card("Spades", 3, 6, 1),
    Card("Hearts", 5, 3, 1),
    Card("Diamonds", 2, 8, 1),
    Card("Clubs", 6, 2, 1),
]

class ShopLogic:
    @staticmethod
    def generate_shop():
        return random.sample(CARD_POOL, 3)