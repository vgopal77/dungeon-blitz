import pygame
from src.settings import TILE_SIZE, WHITE

ENEMY_STATS = {
    'goblin': {
        'health': 30, 'move_delay': 14, 'color': (60, 180, 60),
        'size': TILE_SIZE - 12, 'gold': 5, 'score': 50,
    },
    'orc': {
        'health': 80, 'move_delay': 35, 'color': (140, 50, 190),
        'size': TILE_SIZE - 2, 'gold': 20, 'score': 200,
    },
}


class Enemy:
    def __init__(self, x, y, kind='goblin'):
        stats = ENEMY_STATS[kind]
        self.rect = pygame.Rect(x, y, stats['size'], stats['size'])
        self.health = stats['health']
        self.max_health = stats['health']
        self.move_delay = stats['move_delay']
        self.color = stats['color']
        self.gold = stats['gold']
        self.score = stats['score']
        self.kind = kind
        self._timer = 0
        self._flash_timer = 0

    @property
    def is_dead(self):
        return self.health <= 0

    def take_hit(self, damage):
        self.health -= damage
        self._flash_timer = 8

    def update(self, player, dungeon):
        if self._flash_timer > 0:
            self._flash_timer -= 1
        self._timer += 1
        if self._timer >= self.move_delay:
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
        color = WHITE if self._flash_timer > 0 else self.color
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, WHITE, self.rect, 1)
        self._draw_health_bar(surface)

    def _draw_health_bar(self, surface):
        bar_w = self.rect.width
        ratio = max(0, self.health / self.max_health)
        pygame.draw.rect(surface, (150, 0, 0), (self.rect.x, self.rect.y - 7, bar_w, 4))
        pygame.draw.rect(surface, (0, 200, 0), (self.rect.x, self.rect.y - 7, int(bar_w * ratio), 4))
