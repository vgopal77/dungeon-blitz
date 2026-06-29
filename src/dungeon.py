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
        for row_idx, row in enumerate(self.map):
            for col_idx, tile in enumerate(row):
                x = col_idx * TILE_SIZE
                y = row_idx * TILE_SIZE
                color = WALL_COLOR if tile == '#' else FLOOR_COLOR
                pygame.draw.rect(surface, color, (x, y, TILE_SIZE, TILE_SIZE))
                if tile == '#':
                    pygame.draw.rect(surface, (55, 40, 25), (x, y, TILE_SIZE, TILE_SIZE), 1)
