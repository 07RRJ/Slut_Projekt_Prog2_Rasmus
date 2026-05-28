class BatitleEngine:
    @staticmethod  
    def simulate(team_a, team_b):
        battle_log = []

        a_index = 4
        b_index = 4

        while a_index >= 0 and b_index >= 0:
            attacker = team_a[a_index]
            defender = team_b[b_index]

            if attacker is None:
                a_index -= 1
                continue

            if defender is None:
                b_index -= 1
                continue

            defender.health -= attacker.attack

            battle_log.append(
                f"{attacker.name} attacks {defender.name}"
            )

            if defender.health <= 0:
                battle_log.append(
                    f"{defender.name} died"
                )

                team_b[b_index] = None

                b_index -= 1

            attacker.health -= defender.attack

            if attacker.health <= 0:
                battle_log.append(
                    f"{attacker.name} died"
                )

                team_a[a_index] = None

                a_index -= 1

        return battle_log