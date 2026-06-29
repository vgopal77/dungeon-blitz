import pygame
from src.settings import TILE_SIZE, WALL_COLOR, FLOOR_COLOR

DUNGEON_MAP = [
    "####################",
    "#........#.........#",
    "#........#.........#",
    "#....##..#....###..#",
    "#....##............#",
    "#........#.........#",
    "####.#####.........#",
    "#..................#",
    "#....#######.......#",
    "#....#.....#.......#",
    "#....#.....####.###.",
    "#....#.............#",
    "#..................#",
    "####################",
]

# Pseudo-3D depth colours
_DEPTH      = 10                   # pixels of south-face visible
_EDEPTH     = 8                    # east-face width
_FLOOR_ALT  = (35, 24, 18)        # alternate floor tile (checkerboard)
_SOUTH_FACE = (44, 32, 18)        # south wall face (most in shadow)
_EAST_FACE  = (55, 40, 23)        # east wall face (slightly lighter)
_WALL_HL    = (118, 90, 58)       # wall top-left highlight
_WALL_SH    = (52, 38, 22)        # wall bottom-right shadow


class Dungeon:
    def __init__(self):
        self.map = DUNGEON_MAP
        self.rows = len(self.map)
        self.cols = len(self.map[0])

    def is_wall(self, col, row):
        if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
            return True
        return self.map[row][col] == '#'

    def draw(self, surface):
        # ── Pass 1: floor tiles (subtle checkerboard depth) ──────────────────
        for r, row in enumerate(self.map):
            for c, tile in enumerate(row):
                if tile == '#':
                    continue
                x, y = c * TILE_SIZE, r * TILE_SIZE
                shade = _FLOOR_ALT if (r + c) % 2 == 0 else FLOOR_COLOR
                pygame.draw.rect(surface, shade, (x, y, TILE_SIZE, TILE_SIZE))
                pygame.draw.rect(surface, (20, 13, 9), (x, y, TILE_SIZE, TILE_SIZE), 1)

        # ── Pass 2: depth faces projected onto floor tiles ────────────────────
        for r, row in enumerate(self.map):
            for c, tile in enumerate(row):
                if tile == '#':
                    continue
                x, y = c * TILE_SIZE, r * TILE_SIZE
                # South face of the wall directly above this floor tile
                if self.is_wall(c, r - 1):
                    pygame.draw.rect(surface, _SOUTH_FACE, (x, y, TILE_SIZE, _DEPTH))
                # East face of the wall directly to the left of this floor tile
                if self.is_wall(c - 1, r):
                    pygame.draw.rect(surface, _EAST_FACE, (x, y, _EDEPTH, TILE_SIZE))

        # ── Pass 3: wall tops with bevelled lighting ──────────────────────────
        for r, row in enumerate(self.map):
            for c, tile in enumerate(row):
                if tile != '#':
                    continue
                x, y = c * TILE_SIZE, r * TILE_SIZE
                pygame.draw.rect(surface, WALL_COLOR, (x, y, TILE_SIZE, TILE_SIZE))
                # Top and left edges — lit by virtual light from top-left
                pygame.draw.line(surface, _WALL_HL, (x, y), (x + TILE_SIZE - 1, y), 2)
                pygame.draw.line(surface, _WALL_HL, (x, y), (x, y + TILE_SIZE - 1), 2)
                # Bottom and right edges — in shadow
                pygame.draw.line(surface, _WALL_SH,
                                 (x, y + TILE_SIZE - 1), (x + TILE_SIZE - 1, y + TILE_SIZE - 1), 1)
                pygame.draw.line(surface, _WALL_SH,
                                 (x + TILE_SIZE - 1, y), (x + TILE_SIZE - 1, y + TILE_SIZE - 1), 1)
