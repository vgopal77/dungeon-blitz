import math
import random
import pygame
from src.settings import (
    TILE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT,
    ARENA_BG_TOP, ARENA_BG_BOTTOM,
    ARENA_FLOOR, ARENA_FLOOR_ALT, ARENA_GRID_LINE,
    ARENA_WALL, ARENA_WALL_GLOW, ARENA_PILLAR,
    ARENA_COURT_LINE, ARENA_COURT_PAINT, ARENA_HOOP, ARENA_BACKBOARD,
)

ARENA_COLS = SCREEN_WIDTH  // TILE_SIZE   # 20
ARENA_ROWS = SCREEN_HEIGHT // TILE_SIZE   # 15
PLAY_ROWS  = 14

PILLARS = [(5, 4), (14, 9), (14, 4), (5, 9), (9, 6), (10, 7)]

SPAWN_LEFT  = (2 * TILE_SIZE + 2,  6 * TILE_SIZE + 2)
SPAWN_RIGHT = (17 * TILE_SIZE + 2, 6 * TILE_SIZE + 2)

# Court geometry (pixel coords)
_CL  = TILE_SIZE           # 40
_CR  = TILE_SIZE * 19      # 760
_CT  = TILE_SIZE           # 40
_CB  = TILE_SIZE * 13      # 520
_CW  = _CR - _CL           # 720
_CH  = _CB - _CT           # 480
_CCX = (_CL + _CR) // 2   # 400
_CCY = (_CT + _CB) // 2   # 280

_PAINT_W   = 155
_PAINT_H   = 200
_FT_R      = 58
_CC_R      = 60
_3PT_R     = 172
_HOOP_CX_L = _CL + 20
_HOOP_CX_R = _CR - 20
_HOOP_CY   = _CCY
_RIM_RX    = 18
_RIM_RY    = 7


def vertical_gradient(top, bottom, size):
    w, h = size
    surf = pygame.Surface((w, h))
    for y in range(h):
        t = y / h
        color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        pygame.draw.line(surf, color, (0, y), (w, y))
    return surf


def build_arena_background(size=(SCREEN_WIDTH, SCREEN_HEIGHT)):
    """Pre-render arena ceiling, crowd rows, hanging scoreboard."""
    w, h = size
    surf = vertical_gradient(ARENA_BG_TOP, ARENA_BG_BOTTOM, size)

    # Overhead spotlights
    for lx in (w * 0.18, w * 0.50, w * 0.82):
        cone = pygame.Surface((280, h), pygame.SRCALPHA)
        for r in range(10, 0, -1):
            a  = r * 4
            ex = int(280 * r / 10)
            ey = int(h  * r / 10)
            pygame.draw.ellipse(cone, (255, 240, 200, a), (140 - ex // 2, 0, ex, ey))
        surf.blit(cone, (int(lx - 140), 0))

    # Scoreboard hanging at top-centre
    bw, bh = 220, 58
    bx, by = w // 2 - bw // 2, 10
    pygame.draw.rect(surf, (18, 18, 18), (bx - 5, by - 5, bw + 10, bh + 10), border_radius=6)
    pygame.draw.rect(surf, (35, 35, 35), (bx, by, bw, bh), border_radius=5)
    # LED score panels
    for tx in (bx + 18, bx + bw - 44):
        for ci in range(2):
            pygame.draw.rect(surf, (210, 55, 10), (tx + ci * 18, by + 10, 14, 24), border_radius=2)
    # Team colour strips
    pygame.draw.rect(surf, (18,  60, 180), (bx + 4,         by + 4, 68, 18), border_radius=2)
    pygame.draw.rect(surf, (200, 25,  75), (bx + bw - 72,   by + 4, 68, 18), border_radius=2)
    # Quarter dot
    pygame.draw.circle(surf, (255, 200, 50), (bx + bw // 2, by + 32), 7)
    # Rafters
    for ry in range(0, 28, 7):
        pygame.draw.line(surf, (28, 20, 14), (0, ry), (w, ry), 1)
    # Faint crowd
    rng = random.Random(17)
    for _ in range(500):
        hx  = rng.randint(0, w - 1)
        hy  = rng.randint(0, h - 1)
        bri = rng.randint(28, 70)
        pygame.draw.circle(surf, (bri, bri - 8, bri - 14), (hx, hy), 2)

    return surf


def _draw_court(surf):
    """NBA-style hardwood court: maple stripes, red paint, white lines, 3-D hoops."""

    # --- hardwood stripes (horizontal planks) ---
    stripe_h = 12
    for row_y in range(_CT, _CB, stripe_h):
        color = ARENA_FLOOR if (row_y // stripe_h) % 2 == 0 else ARENA_FLOOR_ALT
        pygame.draw.rect(surf, color, (_CL, row_y, _CW, min(stripe_h, _CB - row_y)))

    # Centre spotlight glow
    spot = pygame.Surface((_CW, _CH), pygame.SRCALPHA)
    for step in range(14, 0, -1):
        a  = step * 3
        ex = int(_CW * step / 16)
        ey = int(_CH * step / 16)
        pygame.draw.ellipse(spot, (255, 240, 200, a),
                            (_CW // 2 - ex // 2, _CH // 2 - ey // 2, ex, ey))
    surf.blit(spot, (_CL, _CT))

    # Vertical wood grain lines (board joints running length of court)
    for gx in range(_CL, _CR + 1, 7):
        pygame.draw.line(surf, ARENA_GRID_LINE, (gx, _CT), (gx, _CB), 1)

    # --- RED paint / key areas ---
    for side in (1, -1):
        paint_x = _CL if side == 1 else _CR - _PAINT_W
        paint_y = _CCY - _PAINT_H // 2
        pygame.draw.rect(surf, ARENA_COURT_PAINT, (paint_x, paint_y, _PAINT_W, _PAINT_H))
        # White outline for the key
        pygame.draw.rect(surf, ARENA_COURT_LINE, (paint_x, paint_y, _PAINT_W, _PAINT_H), 2)
        # Free-throw line
        ft_x = _CL + _PAINT_W if side == 1 else _CR - _PAINT_W
        pygame.draw.line(surf, ARENA_COURT_LINE,
                         (ft_x, _CCY - _PAINT_H // 2),
                         (ft_x, _CCY + _PAINT_H // 2), 2)
        # Free-throw circle
        pygame.draw.circle(surf, ARENA_COURT_LINE, (ft_x, _CCY), _FT_R, 2)

    # --- Court boundary ---
    pygame.draw.rect(surf, ARENA_COURT_LINE, (_CL, _CT, _CW, _CH), 3)

    # --- Half-court line ---
    pygame.draw.line(surf, ARENA_COURT_LINE, (_CCX, _CT), (_CCX, _CB), 2)

    # --- Centre circle ---
    pygame.draw.circle(surf, ARENA_COURT_LINE, (_CCX, _CCY), _CC_R, 2)

    # --- Basketball logo in centre circle ---
    _draw_basketball(surf, _CCX, _CCY, _CC_R - 8)

    # --- 3-point arcs ---
    pygame.draw.arc(surf, ARENA_COURT_LINE,
                    (_HOOP_CX_L - _3PT_R, _HOOP_CY - _3PT_R, _3PT_R * 2, _3PT_R * 2),
                    -math.pi / 2, math.pi / 2, 2)
    pygame.draw.arc(surf, ARENA_COURT_LINE,
                    (_HOOP_CX_R - _3PT_R, _HOOP_CY - _3PT_R, _3PT_R * 2, _3PT_R * 2),
                    math.pi / 2, 3 * math.pi / 2, 2)

    # --- Restricted-area arcs ---
    ra_r = 34
    for hx in (_HOOP_CX_L, _HOOP_CX_R):
        a0 = -math.pi / 2 if hx == _HOOP_CX_L else  math.pi / 2
        a1 =  math.pi / 2 if hx == _HOOP_CX_L else  3 * math.pi / 2
        pygame.draw.arc(surf, ARENA_COURT_LINE,
                        (hx - ra_r, _HOOP_CY - ra_r, ra_r * 2, ra_r * 2), a0, a1, 2)

    # --- Hoops ---
    _draw_hoop(surf, _HOOP_CX_L, _HOOP_CY, facing_right=True)
    _draw_hoop(surf, _HOOP_CX_R, _HOOP_CY, facing_right=False)


def _draw_basketball(surf, cx, cy, r):
    """Draw a basketball graphic — orange circle with seam lines."""
    if r < 6:
        return
    pygame.draw.circle(surf, (230, 95, 18), (cx, cy), r)
    pygame.draw.circle(surf, (175, 65, 10), (cx, cy), r, 2)
    sc = (100, 42, 8)
    # Horizontal seam
    pygame.draw.line(surf, sc, (cx - r, cy), (cx + r, cy), 2)
    # Vertical seam
    pygame.draw.line(surf, sc, (cx, cy - r), (cx, cy + r), 2)
    # Left curved seam (arc on left half-ellipse)
    lw = max(1, r // 2)
    pygame.draw.arc(surf, sc,
                    (cx - lw * 2, cy - r, lw * 2, r * 2), -math.pi / 2, math.pi / 2, 2)
    # Right curved seam
    pygame.draw.arc(surf, sc,
                    (cx, cy - r, lw * 2, r * 2), math.pi / 2, 3 * math.pi / 2, 2)


def _draw_hoop(surf, cx, cy, facing_right):
    d = 1 if facing_right else -1
    board_x  = int(cx - d * (_RIM_RX + 20))
    board_w  = 8
    board_h  = 56

    # Floor shadow
    shadow = pygame.Surface((_RIM_RX * 2 + 14, _RIM_RY * 2 + 12), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 60),
                        (0, 4, _RIM_RX * 2 + 14, _RIM_RY * 2 + 4))
    surf.blit(shadow, (cx - _RIM_RX - 7, cy + _RIM_RY + 2))

    # Backboard
    pygame.draw.rect(surf, (50, 50, 50),
                     (board_x - 1, cy - board_h // 2 - 1, board_w + 2, board_h + 2),
                     border_radius=2)
    pygame.draw.rect(surf, ARENA_BACKBOARD,
                     (board_x, cy - board_h // 2, board_w, board_h), border_radius=1)
    # Target box on backboard
    tb_h = board_h // 2
    pygame.draw.rect(surf, ARENA_HOOP,
                     (board_x, cy - tb_h // 2, board_w, tb_h), 2)

    # Support arm
    arm_start = (board_x + (board_w if facing_right else 0), cy)
    arm_end   = (cx - d * _RIM_RX, cy)
    pygame.draw.line(surf, (110, 110, 110), arm_start, arm_end, 3)

    # Rim
    pygame.draw.ellipse(surf, (110, 55, 5),
                        (cx - _RIM_RX + 2, cy - _RIM_RY + 3, _RIM_RX * 2 - 2, _RIM_RY * 2))
    pygame.draw.ellipse(surf, ARENA_HOOP,
                        (cx - _RIM_RX, cy - _RIM_RY, _RIM_RX * 2, _RIM_RY * 2), 4)

    # Net
    net_tip = (cx, cy + _RIM_RY + 22)
    for i in range(7):
        angle = (i / 6) * math.pi
        sx = int(cx + _RIM_RX * math.cos(angle + math.pi))
        sy = int(cy + _RIM_RY * math.sin(angle + math.pi))
        pygame.draw.line(surf, (215, 215, 215), (sx, sy), net_tip, 1)
    pygame.draw.line(surf, (200, 200, 200),
                     (cx - _RIM_RX + 4, cy + _RIM_RY + 11),
                     (cx + _RIM_RX - 4, cy + _RIM_RY + 11), 1)


class Arena:
    def __init__(self):
        self.cols   = ARENA_COLS
        self.rows   = PLAY_ROWS
        self._walls = set()
        for c in range(self.cols):
            self._walls.add((c, 0))
            self._walls.add((c, self.rows - 1))
        for r in range(self.rows):
            self._walls.add((0, r))
            self._walls.add((self.cols - 1, r))
        for p in PILLARS:
            self._walls.add(p)
        self._t          = 0
        self._bg_cache   = build_arena_background((SCREEN_WIDTH, SCREEN_HEIGHT))
        self._court_cache = self._build_court_cache()

    def is_wall(self, col, row):
        if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
            return True
        return (col, row) in self._walls

    def update(self):
        self._t += 1

    def _build_court_cache(self):
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        _draw_court(surf)
        return surf

    def draw(self, surface):
        surface.blit(self._bg_cache,   (0, 0))
        surface.blit(self._court_cache, (0, 0))

        pulse = (math.sin(self._t * 0.06) + 1) / 2

        for (c, r) in self._walls:
            x, y      = c * TILE_SIZE, r * TILE_SIZE
            is_border = (c == 0 or r == 0 or c == self.cols - 1 or r == self.rows - 1)
            if is_border:
                self._draw_bleacher_tile(surface, x, y, c, r, pulse)
            else:
                self._draw_pillar(surface, x, y, pulse)

    def _draw_bleacher_tile(self, surface, x, y, c, r, pulse):
        """Dark-wood bleacher seat rows."""
        base = tuple(min(255, int(v * (0.88 + pulse * 0.14))) for v in ARENA_WALL)
        pygame.draw.rect(surface, base, (x, y, TILE_SIZE, TILE_SIZE))

        is_top    = r == 0
        is_bottom = r == self.rows - 1
        is_left   = c == 0
        is_right  = c == self.cols - 1

        # Seat-row lines (lighter wood tone)
        row_col = tuple(min(255, v + 22) for v in ARENA_WALL)
        if is_top or is_bottom:
            for ly in range(y + 7, y + TILE_SIZE, 9):
                pygame.draw.line(surface, row_col, (x, ly), (x + TILE_SIZE, ly), 1)
        else:
            for lx in range(x + 7, x + TILE_SIZE, 9):
                pygame.draw.line(surface, row_col, (lx, y), (lx, y + TILE_SIZE), 1)

        # Warm amber court-edge glow
        hi    = ARENA_WALL_GLOW
        alpha = int(70 + pulse * 55)
        edge  = pygame.Surface((TILE_SIZE, 4), pygame.SRCALPHA)
        edge.fill((*hi, alpha))
        if is_top:
            surface.blit(edge, (x, y + TILE_SIZE - 4))
        elif is_bottom:
            surface.blit(edge, (x, y))
        if is_left:
            v_edge = pygame.Surface((4, TILE_SIZE), pygame.SRCALPHA)
            v_edge.fill((*hi, alpha))
            surface.blit(v_edge, (x + TILE_SIZE - 4, y))
        elif is_right:
            v_edge = pygame.Surface((4, TILE_SIZE), pygame.SRCALPHA)
            v_edge.fill((*hi, alpha))
            surface.blit(v_edge, (x, y))

    def _draw_pillar(self, surface, x, y, pulse):
        pad    = 5
        glow   = pygame.Surface((TILE_SIZE + pad * 2, TILE_SIZE + pad * 2), pygame.SRCALPHA)
        a_base = int(38 + pulse * 48)
        for i in range(4, 0, -1):
            a    = max(0, a_base - i * 12)
            rect = (pad - i * 2, pad - i * 2, TILE_SIZE + i * 4, TILE_SIZE + i * 4)
            pygame.draw.rect(glow, (*ARENA_PILLAR, a), rect, border_radius=5)
        surface.blit(glow, (x - pad, y - pad))
        pygame.draw.rect(surface, ARENA_PILLAR, (x, y, TILE_SIZE, TILE_SIZE), border_radius=4)
        hi = tuple(min(255, v + 60) for v in ARENA_PILLAR)
        pygame.draw.rect(surface, hi, (x, y, TILE_SIZE, TILE_SIZE), 2, border_radius=4)
