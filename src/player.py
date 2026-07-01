import math
import pygame
from src.settings import TILE_SIZE, WHITE, CHARACTER_STATS, TEAM_COLORS, NBA_TEAMS

ATTACK_RANGE     = TILE_SIZE * 1.5
SUPER_RANGE_TANK = TILE_SIZE * 3
TANK_SUPER_DAMAGE = 50

_FC = {}
def _font(sz):
    if sz not in _FC:
        _FC[sz] = pygame.font.Font(None, sz)
    return _FC[sz]


class Player:
    def __init__(self, x, y, char='tank', pid=0, team=None):
        if team and team in NBA_TEAMS:
            char = NBA_TEAMS[team]['char']
        stats = CHARACTER_STATS[char]
        self.rect          = pygame.Rect(x, y, TILE_SIZE - 4, TILE_SIZE - 4)
        self.base_speed    = stats['speed']
        self.speed         = stats['speed']
        self.health        = stats['health']
        self.max_health    = stats['health']
        self.attack_damage = stats['attack_damage']
        self.char          = char
        self.pid           = pid
        self.team          = team

        if team and team in NBA_TEAMS:
            td = NBA_TEAMS[team]
            self.color         = td['primary']
            self.accent_color  = td['secondary']
            self.team_color    = td['primary']
            self.jersey_number = td['number']
            self.team_abbr     = td['abbr']
            self.team_name     = td['name']
        else:
            self.color         = stats['color']
            self.accent_color  = TEAM_COLORS[pid % len(TEAM_COLORS)]
            self.team_color    = TEAM_COLORS[pid % len(TEAM_COLORS)]
            self.jersey_number = str(pid + 1)
            self.team_abbr     = char[:3].upper()
            self.team_name     = char.capitalize()

        self._atk_cd      = 30
        self._atk_t       = 0
        self._atk_flash   = 0
        self.super_meter  = 0
        self._super_active = 0
        self._dash_cd     = 120
        self._dash_t      = 0
        self._trail       = []
        self._dmg_flash   = 0
        self._facing      = (1, 0)

    @property
    def is_dead(self):
        return self.health <= 0

    # ------------------------------------------------------------------ input

    def handle_input(self, dungeon):
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx =  1
        if keys[pygame.K_UP]    or keys[pygame.K_w]: dy = -1
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: dy =  1
        self.move_dir(dx, dy, dungeon)

    def move_dir(self, dx, dy, dungeon):
        if dx or dy:
            self._facing = (dx, dy)
        self._move(dx, dy, dungeon)

    def try_dash(self, dungeon):
        if self._dash_t > 0:
            return
        self._dash_t = self._dash_cd
        dx, dy = self._facing
        for _ in range(5):
            self._trail.append([self.rect.x, self.rect.y, 160])
            self.rect.x += dx * TILE_SIZE
            if self._wall_collision(dungeon):
                self.rect.x -= dx * TILE_SIZE
                break
            self.rect.y += dy * TILE_SIZE
            if self._wall_collision(dungeon):
                self.rect.y -= dy * TILE_SIZE
                break

    def _in_range(self, target, rng):
        dx = abs(self.rect.centerx - target.rect.centerx)
        dy = abs(self.rect.centery - target.rect.centery)
        return dx <= rng and dy <= rng

    def attack(self, targets):
        if self._atk_t > 0:
            return []
        self._atk_t     = self._atk_cd
        self._atk_flash = 10
        hit = []
        for target in targets:
            if self._in_range(target, ATTACK_RANGE):
                target.take_hit(self.attack_damage)
                self.super_meter = min(100, self.super_meter + 12)
                if target.is_dead:
                    hit.append(target)
        return hit

    def use_super(self, targets):
        if self.super_meter < 100:
            return []
        self.super_meter = 0
        hit = []
        if self.char == 'tank':
            for target in targets:
                if self._in_range(target, SUPER_RANGE_TANK):
                    target.take_hit(TANK_SUPER_DAMAGE)
                    if target.is_dead:
                        hit.append(target)
        elif self.char == 'speedster':
            self._super_active = 240
            self.speed = int(self.base_speed * 2.5)
        return hit

    def try_attack_remote(self, opponent):
        if self._atk_t > 0:
            return False
        self._atk_t     = self._atk_cd
        self._atk_flash = 10
        connected = self._in_range(opponent, ATTACK_RANGE)
        if connected:
            self.super_meter = min(100, self.super_meter + 12)
        return connected

    def try_super_remote(self, opponent):
        if self.super_meter < 100:
            return False, False
        self.super_meter = 0
        if self.char == 'speedster':
            self._super_active = 240
            self.speed = int(self.base_speed * 2.5)
            return True, False
        return True, self._in_range(opponent, SUPER_RANGE_TANK)

    # ----------------------------------------------------------------- update

    def tick(self):
        if self._atk_t     > 0: self._atk_t     -= 1
        if self._dash_t    > 0: self._dash_t     -= 1
        if self._dmg_flash > 0: self._dmg_flash  -= 1
        if self._atk_flash > 0: self._atk_flash  -= 1
        if self._super_active > 0:
            self._super_active -= 1
            if self._super_active == 0:
                self.speed = self.base_speed
        for ghost in self._trail:
            ghost[2] -= 24
        self._trail = [g for g in self._trail if g[2] > 0]

    def take_damage(self, amount):
        self.health -= amount
        self._dmg_flash = 10

    take_hit = take_damage

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
            (self.rect.left,     self.rect.top),
            (self.rect.right-1,  self.rect.top),
            (self.rect.left,     self.rect.bottom-1),
            (self.rect.right-1,  self.rect.bottom-1),
        ]:
            if dungeon.is_wall(px // TILE_SIZE, py // TILE_SIZE):
                return True
        return False

    # ------------------------------------------------------------------ draw

    def draw(self, surface, label=None):
        self._draw_trail(surface)
        self._draw_shadow(surface)

        cx, cy = self.rect.center
        radius = self.rect.width // 2

        body_color = (255, 90, 90) if self._dmg_flash > 0 else self.color
        self._draw_body(surface, cx, cy, radius, body_color)

        ring_color = WHITE if self._dmg_flash > 0 else self.accent_color
        pygame.draw.circle(surface, ring_color, (cx, cy), radius + 2, 3)

        if self._super_active > 0:
            pulse = radius + 5 + int(3 * math.sin(pygame.time.get_ticks() * 0.02))
            pygame.draw.circle(surface, (0, 255, 210), (cx, cy), pulse, 2)
        elif self.super_meter >= 100:
            pulse = radius + 4 + int(2 * math.sin(pygame.time.get_ticks() * 0.015))
            pygame.draw.circle(surface, (200, 120, 255), (cx, cy), pulse, 2)

        # Facing indicator
        fx, fy = self._facing
        if fx or fy:
            mag = math.hypot(fx, fy) or 1
            tip = (cx + fx / mag * (radius + 4), cy + fy / mag * (radius + 4))
            pygame.draw.circle(surface, WHITE, (int(tip[0]), int(tip[1])), 3)

        # Attack flash
        if self._atk_flash > 0:
            alpha = int(255 * (self._atk_flash / 10))
            arc_r = radius + 14
            arc_surf = pygame.Surface((arc_r * 2 + 4, arc_r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(arc_surf, (255, 240, 120, alpha), (arc_r + 2, arc_r + 2), arc_r, 3)
            surface.blit(arc_surf, (cx - arc_r - 2, cy - arc_r - 2))

        self._draw_health_bar(surface)

        # Label: show team abbreviation + number
        disp = label
        if label and self.team:
            disp = f'{self.team_abbr} #{self.jersey_number}'
        if disp:
            lbl_color = ring_color if ring_color != WHITE else self.accent_color
            t = _font(18).render(disp, True, lbl_color)
            surface.blit(t, t.get_rect(centerx=cx, bottom=self.rect.top - 4))

    def _draw_body(self, surface, cx, cy, radius, color):
        darker  = tuple(max(0,   c - 55) for c in color)
        lighter = tuple(min(255, c + 80) for c in color)

        # Jersey body — main circle
        pygame.draw.circle(surface, darker,  (cx, cy + 2), radius)
        pygame.draw.circle(surface, color,   (cx, cy),     radius)
        # Highlight glint
        pygame.draw.circle(surface, lighter,
                           (cx - radius // 3, cy - radius // 3),
                           max(2, radius // 4))

        # Jersey number (contrast colour = accent)
        num_sz = max(14, int(radius * 0.9))
        num_s  = _font(num_sz).render(self.jersey_number, True, self.accent_color)
        # Dark drop-shadow for readability
        shadow_s = _font(num_sz).render(self.jersey_number, True, (0, 0, 0))
        surface.blit(shadow_s, shadow_s.get_rect(center=(cx + 1, cy + 3)))
        surface.blit(num_s,    num_s.get_rect(center=(cx,     cy + 2)))

    def _draw_trail(self, surface):
        for x, y, alpha in self._trail:
            ghost = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            pygame.draw.ellipse(ghost, (*self.color, max(0, alpha // 2)), ghost.get_rect())
            surface.blit(ghost, (x, y))

    def _draw_shadow(self, surface):
        sw = self.rect.width + 6
        sh = 10
        sx = self.rect.x - 3
        sy = self.rect.bottom - 5
        s  = pygame.Surface((sw, sh), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (0, 0, 0, 80), (0, 0, sw, sh))
        surface.blit(s, (sx, sy))

    def _draw_health_bar(self, surface):
        w     = TILE_SIZE - 4
        ratio = max(0, self.health / self.max_health)
        bar_color = (0, 200, 0) if ratio > 0.3 else (220, 60, 40)
        pygame.draw.rect(surface, (40, 0, 0),   (self.rect.x, self.rect.y - 9, w, 5))
        pygame.draw.rect(surface, bar_color,     (self.rect.x, self.rect.y - 9, int(w * ratio), 5))

    # ----------------------------------------------------------- serialise (MP)

    def to_dict(self):
        return {
            'x': self.rect.x, 'y': self.rect.y,
            'h': self.health, 'facing': self._facing,
            'super': self.super_meter,
        }
