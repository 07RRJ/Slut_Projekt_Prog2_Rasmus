# screen and visuals
BASE_WIDTH, BASE_HEIGHT = 1920, 1080
MIDDLE_WIDTH, MIDDLE_HEIGHT = BASE_WIDTH // 2, BASE_HEIGHT // 2
MARGIN, PADDING = 32, 32
WIDTH_WITH_MARGIN, HEIGHT_WITH_MARGIN = BASE_WIDTH - MARGIN, BASE_HEIGHT - MARGIN
FPS = 60

# colours
BACKGROUND_COLOR = (200, 200, 200)
WHITE = (240, 240, 240)
LIGHT_GRAY = (180, 180, 180)
GRAY = (120, 120, 120)
DARK_GRAY = (60, 60, 60)
LIGHT_BLACK = (40, 40, 40)
BLACK = (20, 20, 20)
RED = (160, 30, 30)
LIGHT_GOLD = (220, 210, 170)
GOLD = (220, 180, 30)
DARK_GOLD = (180, 140, 10)
DIRTY_GOLD = (140, 100, 0)
BLUE = (100, 170, 255)

# match logic
P1_GONE_THRESHOLD = 120 # seconds before P1 considered disconnected
P2_GRACE_SECONDS = 30 # P2 countdown before default win
BATTLE_COUNTDOWN = 5 # seconds buffer after both ready before battle loads
POLL_EVERY = 2 # seconds

# cards
CARD_W, CARD_H = 180, 270
CARD_GAP = 20

# team and shop
TEAM_SIZE = 5
SHOP_SIZE = 3
GOLD_CAP = 100
SHOP_TIME_LIMIT, CHECKPOINT_TIME = 60, 30 # seconds

# battle logic
SLIDE_TIME = 0.5 # seconds
PAUSE_AFTER = 0.3 # seconds
WIN_GOAL = 5