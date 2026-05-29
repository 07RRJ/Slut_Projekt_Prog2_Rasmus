from dataclasses import dataclass

@dataclass
class Card:
    id:      str
    card_id: str
    name:    str
    attack:  int
    health:  int
    level:   int
    ability: str = ""
    slot:    int = 0

    def is_alive(self) -> bool:
        return self.health > 0

    def take_damage(self, amount: int) -> None:
        self.health -= amount