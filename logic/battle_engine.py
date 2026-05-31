# import copy
# from models.card_model import Card

# class BattleEngine:

#     @staticmethod
#     def simulate(team_a: list, team_b: list) -> dict: # get cards > fix order > simulate and log > return result
#         a = [copy.copy(card) if card else None for card in team_a]
#         b = [copy.copy(card) if card else None for card in team_b]

#         log = []

#         def alive(team):
#             return [card for card in team if card and card.is_alive()]

#         MAX_TICKS = 10000
#         tick = 0

#         a_total_atk = sum(card.attack for card in alive(a))
#         b_total_atk = sum(card.attack for card in alive(b))
#         a_goes_first = b_total_atk > a_total_atk

#         a_pointer = 0
#         b_pointer = 0

#         while alive(a) and alive(b) and tick < MAX_TICKS:
#             tick += 1

#             alive_a = alive(a)
#             alive_b = alive(b)

#             attacker_a = alive_a[a_pointer % len(alive_a)]
#             defender_b = alive_b[-1] # last

#             attacker_b = alive_b[b_pointer % len(alive_b)]
#             defender_a = alive_a[-1]

#             if a_goes_first:
#                 BattleEngine.strike(attacker_a, defender_b, log) # attack idx vs last
#                 if not defender_b.is_alive():
#                     log.append(f"{defender_b.name} defeated")
#                 if defender_b.is_alive():
#                     BattleEngine.strike(attacker_b, defender_a, log)
#                     if not defender_a.is_alive():
#                         log.append(f"{defender_a.name} defeated")
#             else:
#                 BattleEngine.strike(attacker_b, defender_a, log) # attack idx vs last
#                 if not defender_a.is_alive():
#                     log.append(f"{defender_a.name} defeated")
#                 if defender_a.is_alive():
#                     BattleEngine.strike(attacker_a, defender_b, log)
#                     if not defender_b.is_alive():
#                         log.append(f"{defender_b.name} defeated")

#             a_pointer += 1 # move attack idx
#             b_pointer += 1

#         a_alive = alive(a) # get survivor
#         b_alive = alive(b)

#         if a_alive and not b_alive:
#             winner = "a"
#         elif b_alive and not a_alive:
#             winner = "b"
#         else:
#             winner = "draw"

#         log.append(f"Result: {winner.upper()} wins" if winner != "draw" else "Draw")

#         return {
#             "winner": winner,
#             "log": log,
#             "a_hp_remaining": len(a_alive),
#             "b_hp_remaining": len(b_alive),
#         }

#     @staticmethod
#     def strike(attacker: Card, defender: Card, log: list) -> None: # attack but fancy because cards are cool?
#         defender.take_damage(attacker.attack)
#         log.append(
#             f"{attacker.name} (slot {attacker.slot+1}) "
#             f"hits {defender.name} (slot {defender.slot+1}) "
#             f"for {attacker.attack} > {defender.name} HP: {max(defender.health, 0)}"
#         )

import copy
from models.card_model import Card
from logic.battle_event import BattleEvent

class BattleEngine:

    @staticmethod
    def simulate(team_a: list, team_b: list) -> dict:
        a = []
        for i, card in enumerate(team_a):
            if card:
                c = copy.copy(card)
                c.slot = i
                a.append(c)
            else:
                a.append(None)

        b = []
        for i, card in enumerate(team_b):
            if card:
                c = copy.copy(card)
                c.slot = i
                b.append(c)
            else:
                b.append(None)

        log = []

        def alive(team):
            return [card for card in team if card and card.is_alive()]

        MAX_TICKS = 10000
        tick = 0

        a_total_atk = sum(card.attack for card in alive(a))
        b_total_atk = sum(card.attack for card in alive(b))
        a_goes_first = b_total_atk > a_total_atk

        a_pointer = 0
        b_pointer = 0

        def do_strike(attacker, atk_side, defender, def_side):
            defender.take_damage(attacker.attack)
            log.append(BattleEvent(
                kind="strike",
                attacker_side=atk_side,
                attacker_slot=attacker.slot,
                defender_side=def_side,
                defender_slot=defender.slot,
                defender_hp=max(defender.health, 0),
                text=f"{attacker.name} hits {defender.name} for {attacker.attack}",
            ))
            if not defender.is_alive():
                log.append(BattleEvent(
                    kind="death",
                    defender_side=def_side,
                    defender_slot=defender.slot,
                    text=f"{defender.name} defeated",
                ))

        while alive(a) and alive(b) and tick < MAX_TICKS:
            tick += 1

            alive_a = alive(a)
            alive_b = alive(b)

            attacker_a = alive_a[a_pointer % len(alive_a)]
            defender_b = alive_b[-1]
            attacker_b = alive_b[b_pointer % len(alive_b)]
            defender_a = alive_a[-1]

            if a_goes_first:
                do_strike(attacker_a, "a", defender_b, "b")
                if defender_b.is_alive():
                    do_strike(attacker_b, "b", defender_a, "a")
            else:
                do_strike(attacker_b, "b", defender_a, "a")
                if defender_a.is_alive():
                    do_strike(attacker_a, "a", defender_b, "b")

            a_pointer += 1
            b_pointer += 1

        a_alive = alive(a)
        b_alive = alive(b)

        if a_alive and not b_alive:
            winner = "a"
        elif b_alive and not a_alive:
            winner = "b"
        else:
            winner = "draw"

        log.append(BattleEvent(
            kind="result",
            winner=winner,
            text="Draw" if winner == "draw" else f"{winner.upper()} wins",
        ))

        return {
            "winner": winner,
            "log": log,
            "a_hp_remaining": len(a_alive),
            "b_hp_remaining": len(b_alive),
        }

    @staticmethod
    def strike(attacker, defender, log):
        defender.take_damage(attacker.attack)