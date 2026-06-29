import pygame

POTION_COLOR = (0, 220, 100)
HEAL_AMOUNT = 25


class Potion:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x + 8, y + 8, 20, 20)
        self.collected = False

    def collect(self, player):
        if self.rect.colliderect(player.rect):
            player.health = min(player.max_health, player.health + HEAL_AMOUNT)
            self.collected = True

    def draw(self, surface):
        pygame.draw.ellipse(surface, POTION_COLOR, self.rect)
        pygame.draw.ellipse(surface, (255, 255, 255), self.rect, 1)
