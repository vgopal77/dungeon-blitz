SCREEN_WIDTH  = 800
SCREEN_HEIGHT = 600
TILE_SIZE     = 40
FPS           = 60

# Change this to your deployed server URL after hosting
# Local testing: ws://localhost:8765
# Render.com:    wss://your-app-name.onrender.com
SERVER_URL = "ws://localhost:8765"

# Colors
BLACK        = (0,   0,   0)
WHITE        = (255, 255, 255)
GRAY         = (120, 120, 120)
DARK_GRAY    = (30,  30,  30)
WALL_COLOR   = (80,  60,  40)
FLOOR_COLOR  = (30,  20,  15)
PLAYER_COLOR = (50,  150, 255)
ENEMY_COLOR  = (220, 50,  50)
GOLD_COLOR   = (255, 200, 0)
GREEN        = (50,  220, 80)

# Team colors (PvP ring/outline so two same-character picks stay readable)
TEAM_COLORS = [
    (60,  220, 255),   # P1 / you — cyan
    (255, 70,  130),   # P2 / opponent — magenta
]

# Arena (PvP battle map) palette — indoor basketball arena
ARENA_BG_TOP      = (14,  10,   8)   # rafters / ceiling dark
ARENA_BG_BOTTOM   = (26,  18,  12)   # lower crowd
ARENA_FLOOR       = (196, 132,  54)  # maple hardwood light
ARENA_FLOOR_ALT   = (180, 116,  42)  # maple hardwood dark stripe
ARENA_GRID_LINE   = (214, 152,  70)  # wood grain
ARENA_WALL        = (18,   28, 100)  # bleacher / stand navy
ARENA_WALL_GLOW   = (60,  110, 220)  # arena neon blue
ARENA_PILLAR      = (210,  60,  16)  # orange barrier
ARENA_COURT_LINE  = (255, 255, 255)  # court markings
ARENA_COURT_PAINT = (168, 100,  38)  # paint / key (darker wood)
ARENA_HOOP        = (255, 118,   0)  # orange rim
ARENA_BACKBOARD   = (238, 238, 238)  # backboard white

# Character stats
CHARACTER_STATS = {
    'tank': {
        'health': 150, 'speed': 2, 'attack_damage': 35,
        'color': (220, 100, 40), 'super_name': 'GROUND SLAM',
        'desc': ['HP: 150  |  Speed: Slow', 'Super: Blast nearby foes'],
    },
    'speedster': {
        'health': 80, 'speed': 5, 'attack_damage': 20,
        'color': (50, 200, 255), 'super_name': 'SPEED BURST',
        'desc': ['HP: 80  |  Speed: Fast', 'Super: Double speed for 4 sec'],
    },
}
