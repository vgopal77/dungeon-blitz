import pygame
from src.settings import TILE_SIZE, WHITE, CHARACTER_STATS


class Player:
    def __init__(self, x, y, char='tank', pid=0):
        stats = CHARACTER_STATS[char]
        self.rect = pygame.Rect(x, y, TILE_SIZE - 4, TILE_SIZE - 4)
        self.base_speed = stats['speed']
        self.speed = stats['speed']
        self.health = stats['health']
        self.max_health = stats['health']
        self.attack_damage = stats['attack_damage']
        self.color = stats['color']
        self.char = char
        self.pid = pid           # 0 = host, 1 = client
        self.gold = 0
        self.score = 0
        self.has_key = False

        # Attack
        self._atk_cd = 30
        self._atk_t = 0

        # Super
        self.super_meter = 0     # 0-100
        self._super_active = 0   # frames remaining

        # Dash
        self._dash_cd = 120
        self._dash_t = 0

        # Visual flashes
        self._dmg_flash = 0
        self._facing = (1, 0)

    # ------------------------------------------------------------------ input

    def handle_input(self, dungeon):
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx =  1
        if keys[pygame.K_UP]    or keys[pygame.K_w]: dy = -1
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: dy =  1
        if dx or dy:
            self._facing = (dx, dy)
        self._move(dx, dy, dungeon)

    def try_dash(self, dungeon):
        if self._dash_t > 0:
            return
        self._dash_t = self._dash_cd
        dx, dy = self._facing
        for _ in range(5):
            self.rect.x += dx * TILE_SIZE
            if self._wall_collision(dungeon):
                self.rect.x -= dx * TILE_SIZE
                break
            self.rect.y += dy * TILE_SIZE
            if self._wall_collision(dungeon):
                self.rect.y -= dy * TILE_SIZE
                break

    def attack(self, enemies):
        if self._atk_t > 0:
            return []
        self._atk_t = self._atk_cd
        killed = []
        for enemy in enemies:
            dx = abs(self.rect.centerx - enemy.rect.centerx)
            dy = abs(self.rect.centery - enemy.rect.centery)
            if dx <= TILE_SIZE * 1.5 and dy <= TILE_SIZE * 1.5:
                enemy.take_hit(self.attack_damage)
                self.super_meter = min(100, self.super_meter + 12)
                if enemy.is_dead:
                    killed.append(enemy)
        return killed

    def use_super(self, enemies):
        if self.super_meter < 100:
            return []
        self.super_meter = 0
        killed = []
        if self.char == 'tank':
            for enemy in enemies:
                dx = abs(self.rect.centerx - enemy.rect.centerx)
                dy = abs(self.rect.centery - enemy.rect.centery)
                if dx <= TILE_SIZE * 3 and dy <= TILE_SIZE * 3:
                    enemy.take_hit(50)
                    if enemy.is_dead:
                        killed.append(enemy)
        elif self.char == 'speedster':
            self._super_active = 240   # 4 seconds
            self.speed = int(self.base_speed * 2.5)
        return killed

    # ----------------------------------------------------------------- update

    def tick(self):
        if self._atk_t   > 0: self._atk_t   -= 1
        if self._dash_t  > 0: self._dash_t   -= 1
        if self._dmg_flash > 0: self._dmg_flash -= 1
        if self._super_active > 0:
            self._super_active -= 1
            if self._super_active == 0:
                self.speed = self.base_speed

    def take_damage(self, amount):
        self.health -= amount
        self._dmg_flash = 10

    # ------------------------------------------------------------------ move

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

    # ------------------------------------------------------------------ draw

    def draw(self, surface, label=None):
        self._draw_shadow(surface)
        color = (255, 80, 80) if self._dmg_flash > 0 else self.color
        if self._super_active > 0 and self.char == 'speedster':
            color = (0, 255, 200)
        pygame.draw.rect(surface, color, self.rect)
        # Bevel: light top-left, dark bottom-right
        hi = tuple(min(c + 60, 255) for c in color)
        sh = tuple(max(c - 50, 0)   for c in color)
        pygame.draw.line(surface, hi, self.rect.topleft,     (self.rect.right - 1, self.rect.top), 2)
        pygame.draw.line(surface, hi, self.rect.topleft,     (self.rect.left, self.rect.bottom - 1), 2)
        pygame.draw.line(surface, sh, self.rect.bottomleft,  (self.rect.right - 1, self.rect.bottom), 1)
        pygame.draw.line(surface, sh, self.rect.topright,    (self.rect.right, self.rect.bottom - 1), 1)
        self._draw_health_bar(surface)
        if label:
            font = pygame.font.Font(None, 20)
            t = font.render(label, True, WHITE)
            surface.blit(t, (self.rect.x, self.rect.y - 18))

    def _draw_shadow(self, surface):
        sw = self.rect.width + 4
        sh = 10
        sx = self.rect.x - 2
        sy = self.rect.bottom - 4
        s = pygame.Surface((sw, sh), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (0, 0, 0, 90), (0, 0, sw, sh))
        surface.blit(s, (sx, sy))

    def _draw_health_bar(self, surface):
        w = TILE_SIZE - 4
        ratio = max(0, self.health / self.max_health)
        pygame.draw.rect(surface, (150, 0, 0), (self.rect.x, self.rect.y - 7, w, 4))
        pygame.draw.rect(surface, (0, 200, 0), (self.rect.x, self.rect.y - 7, int(w * ratio), 4))

    # ----------------------------------------------------------- serialise (MP)

    def to_dict(self):
        return {
            'x': self.rect.x, 'y': self.rect.y,
            'h': self.health, 'key': self.has_key,
        }
