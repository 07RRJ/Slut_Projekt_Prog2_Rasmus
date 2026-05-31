from core.constants import *
import pygame

def my_slot_x(slot_index: int) -> int:
    return MARGIN + slot_index * (CARD_W + CARD_GAP)

def my_slot_y() -> int:
    return BASE_HEIGHT - CARD_H - MARGIN

def opp_slot_x(slot_index: int) -> int:
    return BASE_WIDTH - MARGIN - CARD_W - slot_index * (CARD_W + CARD_GAP)

def opp_slot_y() -> int:
    return MARGIN

def my_slot_rect(slot_index: int) -> pygame.Rect:
    return pygame.Rect(my_slot_x(slot_index), my_slot_y(), CARD_W, CARD_H)

def opp_slot_rect(slot_index: int) -> pygame.Rect:
    return pygame.Rect(opp_slot_x(slot_index), opp_slot_y(), CARD_W, CARD_H)

def slot_rect(side: str, slot: int) -> pygame.Rect:
    return my_slot_rect(slot) if side == "a" else opp_slot_rect(slot)

def slot_center(side: str, slot: int):
    rect = slot_rect(side, slot)
    return (rect.centerx, rect.centery)