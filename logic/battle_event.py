from dataclasses import dataclass

@dataclass
class BattleEvent:
    kind: str

    attacker_side: str = None
    attacker_slot: int = None
    defender_side: str = None
    defender_slot: int = None
    defender_hp: int = None

    winner: str = None

    text: str = ""