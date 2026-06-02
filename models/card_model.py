from dataclasses import dataclass, field

@dataclass
class Card:
    id: str
    card_id: str
    name: str
    attack: int
    health: int
    level: int
    speed: int # lower = faster = min(1) because this is ticks it waits untill next card
    ability: str = ""
    slot: int = 0
    is_stat_up: bool = False

    def is_alive(self) -> bool: # probably should have said duriblity instead since it is an object... cant be botherd now since im only writing comments because it is a criteria
        return self.health > 0

    def take_damage(self, amount: int) -> None:
        self.health -= amount