import math
import random
from src.player import ATTACK_RANGE
from src.settings import TILE_SIZE

CLOSE_RANGE = ATTACK_RANGE * 0.85
FLEE_HEALTH_RATIO = 0.3
STUCK_THRESHOLD = 6     # frames of near-zero progress before we commit to a dodge
DODGE_LOCK_FRAMES = 22  # long enough to clear a tile at typical bot speed


def _sign(v, deadzone=4):
    if v > deadzone:
        return 1
    if v < -deadzone:
        return -1
    return 0


class AIBot:
    """Drives a Player instance against another Player. Greedy chase/attack/flee,
    with a committed perpendicular dodge to escape pillar obstacles — a purely
    reactive steer (recomputed every frame from the live target vector) ends up
    in a 2-frame oscillation whenever the target sits dead-on with an obstacle,
    since the direct move back toward the target undoes the previous dodge step."""

    def __init__(self, bot_player):
        self.player = bot_player
        self._dodge_dir = random.choice([-1, 1])
        self._dodge_vec = (0, 0)
        self._dodge_lock = 0
        self._stuck_timer = 0
        self._last_dist = None

    def update(self, opponent, arena):
        bot = self.player
        if bot.is_dead or opponent.is_dead:
            return

        dx = opponent.rect.centerx - bot.rect.centerx
        dy = opponent.rect.centery - bot.rect.centery
        dist = math.hypot(dx, dy) or 1

        fleeing = bot.health <= bot.max_health * FLEE_HEALTH_RATIO and bot.char != 'tank'
        move_x, move_y = _sign(dx), _sign(dy)
        if fleeing:
            move_x, move_y = -move_x or 1, -move_y

        # Progress toward the goal (closing distance when chasing, opening it
        # when fleeing), not raw movement: sliding sideways while a diagonal
        # attempt is half-blocked still counts as "movement" but makes no
        # real headway, and would otherwise keep resetting the stuck counter
        # forever (see _steer_direct).
        if self._last_dist is None:
            progress = 999
        else:
            progress = (dist - self._last_dist) if fleeing else (self._last_dist - dist)
        self._last_dist = dist

        if fleeing or dist > CLOSE_RANGE:
            self._chase_step(bot, move_x, move_y, progress, arena)
            if not fleeing and dist > 120 and bot._dash_t == 0 and random.random() < 0.02:
                bot._facing = (move_x or 1, move_y or 1)
                bot.try_dash(arena)
        else:
            bot.attack([opponent])

        if bot.super_meter >= 100 and dist < CLOSE_RANGE * 3:
            bot.use_super([opponent])

    def _chase_step(self, bot, move_x, move_y, progress, arena):
        if self._dodge_lock > 0:
            # check every frame whether the original path has opened up (e.g.
            # we've cleared the obstacle's row/col band) and bail out early.
            # Must be a non-mutating combined-rect test: Player._move() applies
            # x and y independently, so a mutating probe can "succeed" via the
            # y-component alone while the actually-blocked x-component stays
            # stuck — and worse, that spurious y-only step can walk straight
            # back through the dodge progress just made.
            if self._can_move(bot, move_x, move_y, arena):
                bot.move_dir(move_x, move_y, arena)
                self._dodge_lock = 0
                self._stuck_timer = 0
                return
            self._dodge_lock -= 1
            self._try_move(bot, *self._dodge_vec, arena)
            return

        self._stuck_timer = self._stuck_timer + 1 if progress < 0.5 else 0
        if self._stuck_timer <= STUCK_THRESHOLD:
            self._steer_direct(bot, move_x, move_y, arena)
            return

        # stuck against an obstacle — commit to a perpendicular dodge for a
        # fixed window instead of recomputing toward the target every frame.
        # (dist > CLOSE_RANGE guarantees move_x/move_y aren't both 0, so no
        # zero-fallback is needed here — one was tried before and it
        # corrupted the perpendicular whenever an axis was legitimately 0.)
        self._stuck_timer = 0
        perp_x, perp_y = -move_y, move_x
        vec_a = (perp_x * self._dodge_dir, perp_y * self._dodge_dir)
        vec_b = (-vec_a[0], -vec_a[1])
        if self._try_move(bot, *vec_a, arena):
            self._dodge_vec = vec_a
        elif self._try_move(bot, *vec_b, arena):
            self._dodge_vec = vec_b
            self._dodge_dir *= -1
        else:
            self._dodge_vec = vec_a
        self._dodge_lock = DODGE_LOCK_FRAMES

    def _steer_direct(self, bot, move_x, move_y, arena):
        if move_x == 0 and move_y == 0:
            return
        # Only commit to the diagonal if both axes are actually clear —
        # otherwise Player._move()'s independent x/y resolution can "succeed"
        # via the open axis alone while sliding along the blocked one, which
        # looks like progress but can walk the bot straight back where it
        # came from (see the progress-tracking comment in update()).
        if move_x and move_y and self._can_move(bot, move_x, move_y, arena):
            bot.move_dir(move_x, move_y, arena)
            return
        if move_x and self._try_move(bot, move_x, 0, arena):
            return
        if move_y:
            self._try_move(bot, 0, move_y, arena)

    @staticmethod
    def _try_move(bot, dx, dy, arena):
        before = bot.rect.topleft
        bot.move_dir(dx, dy, arena)
        return bot.rect.topleft != before

    @staticmethod
    def _can_move(bot, dx, dy, arena):
        if dx == 0 and dy == 0:
            return False
        test = bot.rect.move(dx * bot.speed, dy * bot.speed)
        for px, py in (
            (test.left, test.top), (test.right - 1, test.top),
            (test.left, test.bottom - 1), (test.right - 1, test.bottom - 1),
        ):
            if arena.is_wall(px // TILE_SIZE, py // TILE_SIZE):
                return False
        return True
