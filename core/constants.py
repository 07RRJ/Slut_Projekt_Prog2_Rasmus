BASE_WIDTH, BASE_HEIGHT = 1920, 1080
MIDDLE_WIDTH, MIDDLE_HEIGHT = BASE_WIDTH // 2, BASE_HEIGHT // 2
MARGIN, PADDING = 32, 32
WIDTH_WITH_MARGIN, HEIGHT_WITH_MARGIN = BASE_WIDTH - MARGIN, BASE_HEIGHT - MARGIN

FPS = 60

TEAM_SIZE = 5
SHOP_SIZE = 3

BACKGROUND_COLOR = (200, 200, 200)
WHITE = (240, 240, 240)
BLACK = (20, 20, 20)
GRAY = (120, 120, 120)
DARK_GRAY = (60, 60, 60)
RED = (160, 30, 30)
GOLD = (220, 180, 30)
BLUE = (100, 170, 255)
# ── Card layout constants (shared across scenes) ──────────────
CARD_W, CARD_H = 120, 180
CARD_GAP       = 20

def my_slot_x(slot_index: int) -> int:
    """Player's card row: anchored bottom-left."""
    return MARGIN + slot_index * (CARD_W + CARD_GAP)

def my_slot_y() -> int:
    return BASE_HEIGHT - CARD_H - MARGIN

def opp_slot_x(slot_index: int) -> int:
    """Opponent's card row: anchored top-right, slot 0 rightmost."""
    return BASE_WIDTH - MARGIN - CARD_W - slot_index * (CARD_W + CARD_GAP)

def opp_slot_y() -> int:
    return MARGIN
