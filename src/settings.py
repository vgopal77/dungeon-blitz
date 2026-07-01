SCREEN_WIDTH  = 800
SCREEN_HEIGHT = 600
TILE_SIZE     = 40
FPS           = 60

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

TEAM_COLORS = [
    (60,  220, 255),
    (255, 70,  130),
]

# Arena palette — NBA basketball court
ARENA_BG_TOP      = (22,  15,  10)   # arena ceiling / rafters
ARENA_BG_BOTTOM   = (40,  28,  18)   # lower crowd / courtside
ARENA_FLOOR       = (215, 180, 125)  # light maple hardwood
ARENA_FLOOR_ALT   = (200, 162, 108)  # darker maple stripe
ARENA_GRID_LINE   = (228, 195, 142)  # subtle wood grain
ARENA_WALL        = (50,  36,  24)   # dark wood bleacher seat
ARENA_WALL_GLOW   = (185, 138,  75)  # warm courtside amber glow
ARENA_PILLAR      = (210,  60,  16)  # orange courtside barrier
ARENA_COURT_LINE  = (255, 255, 255)  # white court markings
ARENA_COURT_PAINT = (200,  17,  46)  # NBA red paint / key area
ARENA_HOOP        = (255, 118,   0)  # orange rim
ARENA_BACKBOARD   = (245, 245, 245)  # white backboard

# NBA Teams
NBA_TEAMS = {
    'bulls':    {
        'name': 'Chicago Bulls',         'city': 'Chicago',
        'primary': (206,  17,  65),  'secondary': (  0,   0,   0),
        'abbr': 'CHI', 'char': 'tank',      'number': '23',
    },
    'lakers':   {
        'name': 'Los Angeles Lakers',    'city': 'Los Angeles',
        'primary': ( 85,  37, 130),  'secondary': (253, 185,  39),
        'abbr': 'LAL', 'char': 'tank',      'number': '24',
    },
    'warriors': {
        'name': 'Golden State Warriors', 'city': 'Golden State',
        'primary': ( 29,  66, 138),  'secondary': (255, 199,  44),
        'abbr': 'GSW', 'char': 'speedster', 'number': '30',
    },
    'celtics':  {
        'name': 'Boston Celtics',        'city': 'Boston',
        'primary': (  0, 122,  51),  'secondary': (255, 255, 255),
        'abbr': 'BOS', 'char': 'tank',      'number': '11',
    },
    'heat':     {
        'name': 'Miami Heat',            'city': 'Miami',
        'primary': (152,   0,  46),  'secondary': (255, 162,   0),
        'abbr': 'MIA', 'char': 'speedster', 'number':  '3',
    },
    'nets':     {
        'name': 'Brooklyn Nets',         'city': 'Brooklyn',
        'primary': ( 25,  25,  25),  'secondary': (255, 255, 255),
        'abbr': 'BKN', 'char': 'speedster', 'number': '11',
    },
}
NBA_TEAM_ORDER = ['bulls', 'lakers', 'warriors', 'celtics', 'heat', 'nets']

# Character stats (referenced by teams via 'char' key)
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
