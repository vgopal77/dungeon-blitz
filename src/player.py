import pygame
from src.settings import TILE_SIZE, PLAYER_COLOR, WHITE


class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TILE_SIZE - 4, TILE_SIZE - 4)
        self.speed = 3
        self.health = 100
        self.max_health = 100

    def handle_input(self, dungeon):
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = 1
        self._move(dx, dy, dungeon)

    def _move(self, dx, dy, dungeon):
        if dx != 0:
            self.rect.x += dx * self.speed
            if self._wall_collision(dungeon):
                self.rect.x -= dx * self.speed
        if dy != 0:
            self.rect.y += dy * self.speed
            if self._wall_collision(dungeon):
                self.rect.y -= dy * self.speed

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
        pygame.draw.rect(surface, PLAYER_COLOR, self.rect)
        pygame.draw.rect(surface, WHITE, self.rect, 1)
        self._draw_health_bar(surface)

    def _draw_health_bar(self, surface):
        bar_w = TILE_SIZE - 4
        ratio = self.health / self.max_health
        pygame.draw.rect(surface, (150, 0, 0), (self.rect.x, self.rect.y - 7, bar_w, 4))
        pygame.draw.rect(surface, (0, 200, 0), (self.rect.x, self.rect.y - 7, int(bar_w * ratio), 4))
