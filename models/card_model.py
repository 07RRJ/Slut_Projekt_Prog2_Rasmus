from dataclasses import dataclass

@dataclass
class Card:
    name: str
    attack: int
    health: int
    tier: int
    ability: str = ""