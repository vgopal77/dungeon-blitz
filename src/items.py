import pygame
import math
from src.settings import TILE_SIZE, GOLD_COLOR, GREEN


class Key:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x + 10, y + 10, 16, 16)
        self.collected = False
        self._t = 0

    def update(self):
        self._t += 0.08

    def collect(self, player):
        if not self.collected and self.rect.colliderect(player.rect):
            self.collected = True
            return True
        return False

    def draw(self, surface):
        if self.collected:
            return
        cx, cy = self.rect.center
        bob = int(math.sin(self._t) * 3)
        pygame.draw.circle(surface, GOLD_COLOR, (cx, cy + bob), 10)
        pygame.draw.circle(surface, (255, 255, 150), (cx, cy + bob), 6)
        pygame.draw.circle(surface, (180, 130, 0), (cx, cy + bob), 3)


class Portal:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x + 4, y + 4, TILE_SIZE - 8, TILE_SIZE - 8)
        self.active = False
        self._t = 0

    def update(self):
        self._t += 0.1

    def draw(self, surface):
        pulse = abs(math.sin(self._t))
        if self.active:
            r = int(0   + 30  * pulse)
            g = int(160 + 95  * pulse)
            b = int(80  + 100 * pulse)
            border = (80, 255, 120)
        else:
            r, g, b = 40, 40, 55
            border = (70, 70, 90)
        pygame.draw.ellipse(surface, (r, g, b), self.rect)
        pygame.draw.ellipse(surface, border, self.rect, 2)
        if not self.active:
            cx, cy = self.rect.center
            pygame.draw.lines(surface, (90, 90, 110), True, [
                (cx, cy - 6), (cx + 5, cy + 4), (cx - 5, cy + 4)
            ], 2)
