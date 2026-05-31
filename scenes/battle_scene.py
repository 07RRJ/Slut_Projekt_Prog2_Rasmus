import pygame, time, copy
from scenes.base_scene import BaseScene
from logic.controllers.game_controller import GameController
from logic.battle_engine import BattleEngine
from ui.team_slot import TeamSlot
from ui.stat_box import StatBox
from core.constants import *
from ui.pos_helpers import *

class BattleScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        self.ctrl = GameController(game)
        self.font = game.assets.get_font("body")
        self.title = game.assets.get_font("title")
        self.stat_box = StatBox(game.state)

        self.ctrl.load_enemy_team() # store enemy
        self.result = self.ctrl.run_battle() # give data to simulation and save it
        self.log = self.result["log"]

        self.a_cards = [copy.copy(card) if card else None for card in game.state.team] # get identical cards to not tamper with og, since python variables just links the data to memory and all that
        self.b_cards = [copy.copy(card) if card else None for card in game.state.enemy_team]
        self.a_dead = set() # indexes of the fallen
        self.b_dead = set()

        self.my_slots = [TeamSlot(*my_slot_rect(i).topleft, i) for i in range(5)]
        self.opp_slots = [TeamSlot(*opp_slot_rect(i).topleft, i) for i in range(5)]

        self.event_idx = 0
        self.phase = "pause"
        self.phase_start = time.time()

        self.cur_event: BattleEngine | None = None

        self.anim_card_side = None
        self.anim_card_slot = None

        self.anim_start = (0, 0)
        self.anim_target = (0, 0)

        self.highlight_a_slot = -1
        self.highlight_b_slot = -1

        self.done = False
        self.phase = "initial_pause"
        self.phase_start = time.time()

    def advance(self): # drawing logic
        if self.event_idx >= len(self.log):
            self.phase = "done"
            self.done = True
            self.highlight_a_slot = -1
            self.highlight_b_slot = -1
            return

        event = self.log[self.event_idx]
        self.event_idx += 1
        self.cur_event = event

        if event.kind == "result":
            self.phase = "done"
            self.done = True
            self.highlight_a_slot = -1
            self.highlight_b_slot = -1
            return

        if event.kind == "death":
            if event.defender_side == "a":
                self.a_dead.add(event.defender_slot)
            else:
                self.b_dead.add(event.defender_slot)
            self.highlight_a_slot = -1
            self.highlight_b_slot = -1
            self.phase = "pause"
            self.phase_start = time.time()
            return

        if event.kind == "strike":
            if event.attacker_side == "a":
                self.highlight_a_slot = event.attacker_slot
                self.highlight_b_slot = -1
            else:
                self.highlight_b_slot = event.attacker_slot
                self.highlight_a_slot = -1

            self.anim_card_side = event.attacker_side
            self.anim_card_slot = event.attacker_slot

            self.anim_start = slot_center(event.attacker_side, event.attacker_slot)
            self.anim_target = slot_center(event.defender_side, event.defender_slot)
            overshoot_x = self.anim_target[0] + (self.anim_target[0] - self.anim_start[0]) * 0.1
            overshoot_y = self.anim_target[1] + (self.anim_target[1] - self.anim_start[1]) * 0.1
            self.anim_over = (overshoot_x, overshoot_y)
            self.phase = "attack_out"

            self.phase_start = time.time()

    def finish_strike(self): # change card stats, right now just hp after being attacked
        event = self.cur_event
        if event is None:
            return
        target_list = self.b_cards if event.defender_side == "b" else self.a_cards
        card = target_list[event.defender_slot]
        if card:
            card.health = event.defender_hp
        self.highlight_a_slot = -1
        self.highlight_b_slot = -1
        self.phase = "pause"
        self.phase_start = time.time()

    def get_attack_position(self): # give attacking cards tier location to aim thowrds 
        elapsed = time.time() - self.phase_start
        t = min(elapsed / SLIDE_TIME, 1.0)

        if self.phase == "attack_out":
            x = self.anim_start[0] + (self.anim_over[0] - self.anim_start[0]) * t
            y = self.anim_start[1] + (self.anim_over[1] - self.anim_start[1]) * t
        else:
            x = self.anim_over[0] + (self.anim_start[0] - self.anim_over[0]) * t
            y = self.anim_over[1] + (self.anim_start[1] - self.anim_over[1]) * t
        return (x, y)

    def update(self):
        now = time.time()
        elapsed = now - self.phase_start

        if self.phase == "initial_pause":
            if elapsed >= TIME_BEFORE_FIGHT:
                self.phase = "pause"
                self.phase_start = time.time()
            return 

        if self.phase == "attack_out":
            if elapsed >= SLIDE_TIME:
                self.phase = "attack_back"
                self.phase_start = time.time()

        elif self.phase == "attack_back":
            if elapsed >= SLIDE_TIME:
                self.finish_strike()

        elif self.phase == "pause":
            if elapsed >= PAUSE_AFTER:
                self.advance()

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and self.done:
                goal_reached = self.result.get("goal_reached", False)
                run_ended = self.result.get("run_ended", False)

                if goal_reached:
                    from scenes.menu_scene import MenuScene
                    self.game.scene_manager.switch_scene(MenuScene(self.game))
                elif run_ended:
                    from scenes.menu_scene import MenuScene
                    self.game.scene_manager.switch_scene(MenuScene(self.game))
                else:
                    self.game.state.match = None
                    self.ctrl.refresh_team()
                    from scenes.match_making_scene import MatchMakingScene
                    self.game.scene_manager.switch_scene(MatchMakingScene(self.game))

    def draw(self, screen):
        screen.fill(BACKGROUND_COLOR)

        for slot in self.opp_slots:
            skip_draw = (self.phase in ["attack_out", "attack_back"] and self.anim_card_side == "b" and self.anim_card_slot == slot.index)

            if skip_draw:
                continue

            card = self.b_cards[slot.index]
            hidden = slot.index in self.b_dead
            highlight = (slot.index == self.highlight_b_slot)

            slot.draw(screen, card, highlight=highlight, hidden=hidden)

        for slot in self.my_slots:
            skip_draw = (self.phase in ["attack_out", "attack_back"] and self.anim_card_side == "a" and self.anim_card_slot == slot.index)

            if skip_draw:
                continue

            card = self.a_cards[slot.index]
            hidden = slot.index in self.a_dead
            highlight = (slot.index == self.highlight_a_slot)
            slot.draw(screen, card, highlight=highlight, hidden=hidden)

        if self.phase in ["attack_out", "attack_back"]:
            x, y = self.get_attack_position()

            if self.anim_card_side == "a":
                slot = self.my_slots[self.anim_card_slot]
                card = self.a_cards[self.anim_card_slot]
            else:
                slot = self.opp_slots[self.anim_card_slot]
                card = self.b_cards[self.anim_card_slot]

            if card:
                original_topleft = slot.rect.topleft
                slot.rect.topleft = (x - CARD_W // 2, y - CARD_H // 2)
                slot.draw(screen, card)
                slot.rect.topleft = original_topleft

                vs = self.title.render("VS", True, GOLD)
                screen.blit(vs, vs.get_rect(center=(MIDDLE_WIDTH, MIDDLE_HEIGHT)))

        if self.cur_event and not self.done:
            txt = self.font.render(self.cur_event.text, True, DARK_GRAY)
            screen.blit(txt, txt.get_rect(center=(MIDDLE_WIDTH, MIDDLE_HEIGHT + 60)))

        if self.done:
            goal_reached = self.result.get("goal_reached", False)
            run_ended = self.result.get("run_ended", False)

            if goal_reached or run_ended:
                overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 200))
                screen.blit(overlay, (0, 0))

                if goal_reached:
                    banner = "YOU WIN"
                    sub = "5 battles won = run complete"
                    color = GOLD
                    sub_color = GOLD
                else:
                    banner = "GAME OVER"
                    sub = "Your health reached 0"
                    color = RED
                    sub_color = RED

                banner_surf = self.title.render(banner, True, color)
                screen.blit(banner_surf, banner_surf.get_rect(center=(MIDDLE_WIDTH, MIDDLE_HEIGHT - 60)))

                sub_surf = self.font.render(sub, True, sub_color)
                screen.blit(sub_surf, sub_surf.get_rect(center=(MIDDLE_WIDTH, MIDDLE_HEIGHT)))

                hint_surf = self.font.render("Click anywhere to return to menu", True, GRAY)
                screen.blit(hint_surf, hint_surf.get_rect(center=(MIDDLE_WIDTH, MIDDLE_HEIGHT + 80)))
            else:
                winner = self.result["winner"]
                if winner == "a":
                    banner, color, hint = "YOU WIN", GOLD, "Click to continue"
                elif winner == "b":
                    banner, color, hint = "YOU LOSE", RED, "Click to continue"
                else:
                    banner, color, hint = "DRAW", GRAY, "Click to continue"

                surf = self.title.render(banner, True, color)
                screen.blit(surf, surf.get_rect(center=(MIDDLE_WIDTH, 50)))
                hint_text = self.font.render(hint, True, GRAY)
                screen.blit(hint_text, hint_text.get_rect(center=(MIDDLE_WIDTH, BASE_HEIGHT - 50)))

        self.stat_box.draw(screen)
