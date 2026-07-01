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

# Obstacles — symmetric pairs giving cover without blocking court lines
PILLARS = [(5, 4), (14, 9), (14, 4), (5, 9), (9, 6), (10, 7)]

SPAWN_LEFT  = (2 * TILE_SIZE + 2,  6 * TILE_SIZE + 2)
SPAWN_RIGHT = (17 * TILE_SIZE + 2, 6 * TILE_SIZE + 2)

# Court geometry (pixel coords)
_CL = TILE_SIZE           # court left  x = 40
_CR = TILE_SIZE * 19      # court right x = 760
_CT = TILE_SIZE           # court top   y = 40
_CB = TILE_SIZE * 13      # court bot   y = 520
_CW = _CR - _CL           # 720
_CH = _CB - _CT           # 480
_CCX = (_CL + _CR) // 2  # center x = 400
_CCY = (_CT + _CB) // 2  # center y = 280

# Basketball geometry
_PAINT_W    = 160   # width of paint / key in px
_PAINT_H    = 200   # height of paint box
_FT_R       = 60    # free-throw circle radius
_CC_R       = 62    # center-circle radius
_3PT_R      = 175   # 3-point arc radius (from hoop center)
_HOOP_CX_L  = _CL + 20   # left rim center x  = 60
_HOOP_CX_R  = _CR - 20   # right rim center x = 740
_HOOP_CY    = _CCY        # rim center y        = 280
_RIM_RX     = 18          # rim ellipse x-radius
_RIM_RY     = 7           # rim ellipse y-radius (flattened for 3D)


def vertical_gradient(top, bottom, size):
    w, h = size
    surf = pygame.Surface((w, h))
    for y in range(h):
        t = y / h
        color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        pygame.draw.line(surf, color, (0, y), (w, y))
    return surf


# ------------------------------------------------------------------ background

def build_arena_background(size=(SCREEN_WIDTH, SCREEN_HEIGHT)):
    """Indoor arena ceiling: dark gradient + overhead spotlights + scoreboard."""
    w, h = size
    surf = vertical_gradient(ARENA_BG_TOP, ARENA_BG_BOTTOM, size)

    # Overhead spotlight cones (soft elliptical glow pools on the floor)
    for lx in (w * 0.20, w * 0.50, w * 0.80):
        cone = pygame.Surface((260, h), pygame.SRCALPHA)
        for r in range(9, 0, -1):
            a = r * 4
            ex = int(260 * r / 9)
            ey = int(h * r / 9)
            pygame.draw.ellipse(cone, (255, 240, 200, a), (130 - ex // 2, 0, ex, ey))
        surf.blit(cone, (int(lx - 130), 0))

    # Scoreboard hanging at top centre
    bw, bh = 210, 55
    bx, by = w // 2 - bw // 2, 12
    pygame.draw.rect(surf, (25, 25, 25), (bx - 4, by - 4, bw + 8, bh + 8), border_radius=5)
    pygame.draw.rect(surf, (38, 38, 38), (bx, by, bw, bh), border_radius=4)
    # Score digits (simplified LED blocks)
    for col_i, (score_txt, tx) in enumerate([('00', bx + 24), ('00', bx + bw - 58)]):
        for ci, ch in enumerate(score_txt):
            cx_ = tx + ci * 18
            pygame.draw.rect(surf, (200, 60, 10), (cx_, by + 10, 14, 22), border_radius=2)
    # Team label strips
    pygame.draw.rect(surf, (20, 60, 180), (bx + 4, by + 4, 70, 18), border_radius=2)
    pygame.draw.rect(surf, (200, 30, 80), (bx + bw - 74, by + 4, 70, 18), border_radius=2)
    # Quarter indicator
    pygame.draw.circle(surf, (255, 200, 50), (bx + bw // 2, by + 30), 8)

    # Rafters — thin horizontal lines across the top
    for ry in range(0, 30, 8):
        pygame.draw.line(surf, (30, 22, 16), (0, ry), (w, ry), 1)

    # Faint crowd silhouettes
    rng = random.Random(13)
    for _ in range(600):
        hx = rng.randint(0, w - 1)
        hy = rng.randint(0, h - 1)
        bri = rng.randint(25, 65)
        col = (bri, bri - 10, bri - 15)
        if hy < 30 or hy > h - 20:
            pygame.draw.circle(surf, col, (hx, hy), 2)

    return surf


# ------------------------------------------------------------------ court

def _draw_court(surf):
    """Hardwood floor + all basketball markings + 3-D hoops.
    Drawn onto an SRCALPHA surface so wall tiles can cover the border."""

    # --- hardwood stripes (horizontal, full court width) ---
    stripe_h = 13
    for row_y in range(_CT, _CB, stripe_h):
        color = ARENA_FLOOR if (row_y // stripe_h) % 2 == 0 else ARENA_FLOOR_ALT
        pygame.draw.rect(surf, color, (_CL, row_y, _CW, min(stripe_h, _CB - row_y)))

    # Subtle centre spotlight: alpha overlay brightest at middle
    spot = pygame.Surface((_CW, _CH), pygame.SRCALPHA)
    for step in range(12, 0, -1):
        a = step * 3
        ex = int(_CW * step / 14)
        ey = int(_CH * step / 14)
        pygame.draw.ellipse(spot, (255, 240, 200, a),
                            (_CW // 2 - ex // 2, _CH // 2 - ey // 2, ex, ey))
    surf.blit(spot, (_CL, _CT))

    # --- wood grain lines ---
    for gx in range(_CL, _CR + 1, 8):
        pygame.draw.line(surf, ARENA_GRID_LINE, (gx, _CT), (gx, _CB), 1)

    # --- court boundary ---
    pygame.draw.rect(surf, ARENA_COURT_LINE,
                     (_CL, _CT, _CW, _CH), 3)

    # --- half-court line ---
    pygame.draw.line(surf, ARENA_COURT_LINE, (_CCX, _CT), (_CCX, _CB), 2)

    # --- centre circle ---
    pygame.draw.circle(surf, ARENA_COURT_LINE, (_CCX, _CCY), _CC_R, 2)

    # --- paint / key areas ---
    for hoop_x, side in ((_HOOP_CX_L, 1), (_HOOP_CX_R, -1)):
        paint_x = _CL if side == 1 else _CR - _PAINT_W
        paint_y = _CCY - _PAINT_H // 2
        # Paint fill (slightly different wood shade)
        pygame.draw.rect(surf, ARENA_COURT_PAINT,
                         (paint_x, paint_y, _PAINT_W, _PAINT_H))
        # Paint outline
        pygame.draw.rect(surf, ARENA_COURT_LINE,
                         (paint_x, paint_y, _PAINT_W, _PAINT_H), 2)
        # Free-throw line
        ft_x = _CL + _PAINT_W if side == 1 else _CR - _PAINT_W
        pygame.draw.line(surf, ARENA_COURT_LINE,
                         (ft_x, _CCY - _PAINT_H // 2),
                         (ft_x, _CCY + _PAINT_H // 2), 2)
        # Free-throw circle
        pygame.draw.circle(surf, ARENA_COURT_LINE, (ft_x, _CCY), _FT_R, 2)

    # --- 3-point arcs ---
    three_rect_l = (_HOOP_CX_L - _3PT_R, _HOOP_CY - _3PT_R, _3PT_R * 2, _3PT_R * 2)
    pygame.draw.arc(surf, ARENA_COURT_LINE, three_rect_l, -math.pi / 2, math.pi / 2, 2)

    three_rect_r = (_HOOP_CX_R - _3PT_R, _HOOP_CY - _3PT_R, _3PT_R * 2, _3PT_R * 2)
    pygame.draw.arc(surf, ARENA_COURT_LINE, three_rect_r, math.pi / 2, 3 * math.pi / 2, 2)

    # --- restricted area arcs (small under-hoop arc) ---
    ra_r = 36
    for hx in (_HOOP_CX_L, _HOOP_CX_R):
        ang0 = -math.pi / 2 if hx == _HOOP_CX_L else math.pi / 2
        ang1 = math.pi / 2 if hx == _HOOP_CX_L else 3 * math.pi / 2
        pygame.draw.arc(surf, ARENA_COURT_LINE,
                        (hx - ra_r, _HOOP_CY - ra_r, ra_r * 2, ra_r * 2), ang0, ang1, 2)

    # --- hoops (3-D perspective) ---
    _draw_hoop(surf, _HOOP_CX_L, _HOOP_CY, facing_right=True)
    _draw_hoop(surf, _HOOP_CX_R, _HOOP_CY, facing_right=False)


def _draw_hoop(surf, cx, cy, facing_right):
    """Basketball hoop with backboard + elliptical rim (faked 3-D) + net."""
    d = 1 if facing_right else -1          # direction toward court centre
    board_x = int(cx - d * (_RIM_RX + 20))
    board_w, board_h = 7, 58

    # Floor shadow under rim
    shadow = pygame.Surface((_RIM_RX * 2 + 12, _RIM_RY * 2 + 10), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 55),
                        (0, 4, _RIM_RX * 2 + 12, _RIM_RY * 2 + 4))
    surf.blit(shadow, (cx - _RIM_RX - 6, cy + _RIM_RY + 2))

    # Backboard
    pygame.draw.rect(surf, (60, 60, 60),
                     (board_x - 1, cy - board_h // 2 - 1, board_w + 2, board_h + 2),
                     border_radius=2)
    pygame.draw.rect(surf, ARENA_BACKBOARD,
                     (board_x, cy - board_h // 2, board_w, board_h),
                     border_radius=1)
    # Target box (the square inside the backboard)
    tb_h = board_h // 2
    pygame.draw.rect(surf, ARENA_HOOP,
                     (board_x, cy - tb_h // 2, board_w, tb_h), 2)

    # Support arm (backboard → rim)
    arm_start = (board_x + (board_w if facing_right else 0), cy)
    arm_end   = (cx - d * _RIM_RX, cy)
    pygame.draw.line(surf, (130, 130, 130), arm_start, arm_end, 3)

    # Rim (orange ellipse — flattened to suggest a 3-D circle viewed at angle)
    pygame.draw.ellipse(surf, (100, 50, 0),
                        (cx - _RIM_RX + 2, cy - _RIM_RY + 3, _RIM_RX * 2 - 2, _RIM_RY * 2),
                        0)   # dark interior
    pygame.draw.ellipse(surf, ARENA_HOOP,
                        (cx - _RIM_RX, cy - _RIM_RY, _RIM_RX * 2, _RIM_RY * 2),
                        4)   # orange ring

    # Net (lines from rim points down to a central meeting point)
    net_tip = (cx, cy + _RIM_RY + 20)
    for i in range(6):
        angle = (i / 5) * math.pi   # 0 → π across the bottom of ellipse
        sx = int(cx + _RIM_RX * math.cos(angle + math.pi))
        sy = int(cy + _RIM_RY * math.sin(angle + math.pi))
        pygame.draw.line(surf, (220, 220, 220), (sx, sy), net_tip, 1)
    # Horizontal cross-line mid-net
    pygame.draw.line(surf, (200, 200, 200),
                     (cx - _RIM_RX + 4, cy + _RIM_RY + 10),
                     (cx + _RIM_RX - 4, cy + _RIM_RY + 10), 1)


# ------------------------------------------------------------------ arena

class Arena:
    def __init__(self):
        self.cols = ARENA_COLS
        self.rows = PLAY_ROWS
        self._walls = set()
        for c in range(self.cols):
            self._walls.add((c, 0))
            self._walls.add((c, self.rows - 1))
        for r in range(self.rows):
            self._walls.add((0, r))
            self._walls.add((self.cols - 1, r))
        for p in PILLARS:
            self._walls.add(p)
        self._t = 0
        self._bg_cache    = self._build_background()
        self._court_cache = self._build_court_cache()

    def is_wall(self, col, row):
        if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
            return True
        return (col, row) in self._walls

    def update(self):
        self._t += 1

    # ------------------------------------------------------------- cache build

    def _build_background(self):
        return build_arena_background((SCREEN_WIDTH, SCREEN_HEIGHT))

    def _build_court_cache(self):
        """Pre-render the static court (hardwood + markings + hoops) once."""
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        _draw_court(surf)
        return surf

    # ------------------------------------------------------------- draw

    def draw(self, surface):
        surface.blit(self._bg_cache, (0, 0))
        surface.blit(self._court_cache, (0, 0))

        pulse = (math.sin(self._t * 0.06) + 1) / 2

        for (c, r) in self._walls:
            x, y = c * TILE_SIZE, r * TILE_SIZE
            is_border = c == 0 or r == 0 or c == self.cols - 1 or r == self.rows - 1

            if is_border:
                self._draw_bleacher_tile(surface, x, y, c, r, pulse)
            else:
                self._draw_pillar(surface, x, y, pulse)

    def _draw_bleacher_tile(self, surface, x, y, c, r, pulse):
        """Draw a wall cell as a stadium bleacher section."""
        base = tuple(min(255, int(v * (0.9 + pulse * 0.15))) for v in ARENA_WALL)
        pygame.draw.rect(surface, base, (x, y, TILE_SIZE, TILE_SIZE))

        # Seat-row lines
        is_top    = r == 0
        is_bottom = r == self.rows - 1
        is_left   = c == 0
        is_right  = c == self.cols - 1

        line_col = tuple(min(255, v + 25) for v in ARENA_WALL)
        if is_top or is_bottom:
            for ly in range(y + 8, y + TILE_SIZE, 10):
                pygame.draw.line(surface, line_col, (x, ly), (x + TILE_SIZE, ly), 1)
        else:
            for lx in range(x + 8, x + TILE_SIZE, 10):
                pygame.draw.line(surface, line_col, (lx, y), (lx, y + TILE_SIZE), 1)

        # Court-edge highlight (the row/col bordering the floor)
        hi = ARENA_WALL_GLOW
        alpha = int(80 + pulse * 60)
        edge = pygame.Surface((TILE_SIZE, 4), pygame.SRCALPHA)
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
        """Draw an obstacle as a glowing orange barrier."""
        pad = 5
        glow = pygame.Surface((TILE_SIZE + pad * 2, TILE_SIZE + pad * 2), pygame.SRCALPHA)
        a_base = int(40 + pulse * 50)
        for i in range(4, 0, -1):
            a = max(0, a_base - i * 12)
            rect = (pad - i * 2, pad - i * 2, TILE_SIZE + i * 4, TILE_SIZE + i * 4)
            pygame.draw.rect(glow, (*ARENA_PILLAR, a), rect, border_radius=5)
        surface.blit(glow, (x - pad, y - pad))

        pygame.draw.rect(surface, ARENA_PILLAR, (x, y, TILE_SIZE, TILE_SIZE), border_radius=4)
        hi = tuple(min(255, v + 60) for v in ARENA_PILLAR)
        pygame.draw.rect(surface, hi, (x, y, TILE_SIZE, TILE_SIZE), 2, border_radius=4)
