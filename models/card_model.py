from dataclasses import dataclass, field

@dataclass
class Card:
    id:      str
    card_id: str
    name:    str
    attack:  int
    health:  int
    level:   int
    speed:   int          # lower = faster; min 1
    ability: str = ""
    slot:    int = 0
    is_stat_up: bool = False   # True for stat-up shop items (not real cards)

    def is_alive(self) -> bool:
        return self.health > 0

    def take_damage(self, amount: int) -> None:
        self.health -= amount
