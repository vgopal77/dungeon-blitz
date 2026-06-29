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

# Character stats
CHARACTER_STATS = {
    'tank': {
        'health': 150, 'speed': 2, 'attack_damage': 35,
        'color': (220, 100, 40), 'super_name': 'GROUND SLAM',
        'desc': ['HP: 150  |  Speed: Slow', 'Super: Blast all nearby enemies'],
    },
    'speedster': {
        'health': 80, 'speed': 5, 'attack_damage': 20,
        'color': (50, 200, 255), 'super_name': 'SPEED BURST',
        'desc': ['HP: 80  |  Speed: Fast', 'Super: Double speed for 4 sec'],
    },
}
