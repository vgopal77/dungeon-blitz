import pygame
from src.settings import TILE_SIZE, ENEMY_COLOR, WHITE


class Enemy:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TILE_SIZE - 4, TILE_SIZE - 4)
        self.health = 50
        self.max_health = 50
        self._timer = 0
        self._move_delay = 25  # frames between steps

    def update(self, player, dungeon):
        self._timer += 1
        if self._timer >= self._move_delay:
            self._timer = 0
            self._step_toward(player, dungeon)

    def _step_toward(self, player, dungeon):
        dx = 1 if player.rect.x > self.rect.x else -1 if player.rect.x < self.rect.x else 0
        dy = 1 if player.rect.y > self.rect.y else -1 if player.rect.y < self.rect.y else 0

        old_x = self.rect.x
        self.rect.x += dx * TILE_SIZE
        if self._wall_collision(dungeon):
            self.rect.x = old_x

        old_y = self.rect.y
        self.rect.y += dy * TILE_SIZE
        if self._wall_collision(dungeon):
            self.rect.y = old_y

    def _wall_collision(self, dungeon):
        for px, py in [
            (self.rect.left, self.rect.top),
            (self.rect.right - 1, self.rect.top),
            (self.rect.left, self.rect.bottom - 1),
            (self.rect.right - 1, self.rect.bottom - 1),
        ]:
            if dungeon.is_wall(px // TILE_SIZE, py // TILE_SIZE):
                return True
        return False

    def draw(self, surface):
        pygame.draw.rect(surface, ENEMY_COLOR, self.rect)
        pygame.draw.rect(surface, WHITE, self.rect, 1)
        self._draw_health_bar(surface)

    def _draw_health_bar(self, surface):
        bar_w = TILE_SIZE - 4
        ratio = self.health / self.max_health
        pygame.draw.rect(surface, (150, 0, 0), (self.rect.x, self.rect.y - 7, bar_w, 4))
        pygame.draw.rect(surface, (0, 200, 0), (self.rect.x, self.rect.y - 7, int(bar_w * ratio), 4))
