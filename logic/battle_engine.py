"""
Battle engine — speed-based turn order.

All 10 cards (5 per side) are sorted by speed ascending (lowest = fastest).
Ties broken by slot index (lower slot acts first within same speed).
Each card acts once per "round"; rounds repeat until one side is wiped.

Attacker always targets the opponent's last alive card (highest slot index
that still has health > 0), matching the intended design from pvp.png.

Returns a structured log of BattleEvent objects so BattleScene can drive
animations without re-running the simulation.
"""

import copy
from dataclasses import dataclass
from models.card_model import Card


@dataclass
class BattleEvent:
    """One atomic animation step."""
    kind:          str    # "strike" | "death" | "result"
    attacker_side: str    # "a" | "b"
    attacker_slot: int    # original slot index (0-4)
    defender_side: str
    defender_slot: int
    damage:        int    = 0
    defender_hp:   int    = 0   # hp after hit
    text:          str    = ""  # human-readable summary


class BattleEngine:

    @staticmethod
    def simulate(team_a: list, team_b: list) -> dict:
        """
        team_a / team_b: list[Card|None] length 5, index = slot.
        Returns:
          {
            "winner":         "a" | "b" | "draw",
            "events":         list[BattleEvent],
            "a_hp_remaining": int,
            "b_hp_remaining": int,
          }
        """
        a = [copy.copy(c) if c else None for c in team_a]
        b = [copy.copy(c) if c else None for c in team_b]

        events: list[BattleEvent] = []

        def alive(team, side):
            return [(i, c) for i, c in enumerate(team) if c and c.is_alive()]

        MAX_ROUNDS = 200
        rounds = 0

        while alive(a, "a") and alive(b, "b") and rounds < MAX_ROUNDS:
            rounds += 1

            # Build this round's action queue sorted by speed asc, then slot asc
            queue = []
            for i, c in enumerate(a):
                if c and c.is_alive():
                    queue.append(("a", i, c))
            for i, c in enumerate(b):
                if c and c.is_alive():
                    queue.append(("b", i, c))

            queue.sort(key=lambda x: (x[2].speed, x[1]))

            for side, slot, attacker in queue:
                if not attacker.is_alive():
                    continue   # died earlier this round

                # Find target: opponent's last (highest-slot) alive card
                if side == "a":
                    targets = alive(b, "b")
                else:
                    targets = alive(a, "a")

                if not targets:
                    break   # opponent wiped mid-round

                target_slot, defender = targets[-1]   # last alive = back row
                defender_side = "b" if side == "a" else "a"

                defender.take_damage(attacker.attack)
                events.append(BattleEvent(
                    kind          = "strike",
                    attacker_side = side,
                    attacker_slot = slot,
                    defender_side = defender_side,
                    defender_slot = target_slot,
                    damage        = attacker.attack,
                    defender_hp   = max(defender.health, 0),
                    text=(
                        f"{attacker.name} (slot {slot+1}, spd {attacker.speed}) "
                        f"hits {defender.name} (slot {target_slot+1}) "
                        f"for {attacker.attack}  →  HP {max(defender.health,0)}"
                    ),
                ))

                if not defender.is_alive():
                    events.append(BattleEvent(
                        kind          = "death",
                        attacker_side = side,
                        attacker_slot = slot,
                        defender_side = defender_side,
                        defender_slot = target_slot,
                        text          = f"{defender.name} defeated",
                    ))

        a_alive = alive(a, "a")
        b_alive = alive(b, "b")

        if a_alive and not b_alive:
            winner = "a"
        elif b_alive and not a_alive:
            winner = "b"
        else:
            winner = "draw"

        events.append(BattleEvent(
            kind="result", attacker_side="", attacker_slot=-1,
            defender_side="", defender_slot=-1,
            text=f"Result: {'DRAW' if winner == 'draw' else winner.upper() + ' wins'}",
        ))

        return {
            "winner":         winner,
            "events":         events,
            "a_hp_remaining": len(a_alive),
            "b_hp_remaining": len(b_alive),
        }
