import pygame
import sys
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, BLACK, WHITE, GRAY
from src.dungeon import Dungeon
from src.player import Player
from src.enemy import Enemy


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Dungeon Blitz")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 32)
        self._new_game()

    def _new_game(self):
        self.dungeon = Dungeon()
        self.player = Player(42, 42)
        self.enemies = [
            Enemy(82, 202),
            Enemy(482, 282),
            Enemy(602, 442),
        ]

    def run(self):
        while True:
            self._handle_events()
            self._update()
            self._draw()
            self.clock.tick(FPS)

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_r:
                    self._new_game()

    def _update(self):
        self.player.handle_input(self.dungeon)
        for enemy in self.enemies:
            enemy.update(self.player, self.dungeon)
        self._check_combat()

    def _check_combat(self):
        for enemy in self.enemies:
            if self.player.rect.colliderect(enemy.rect):
                self.player.health -= 0.3
        if self.player.health <= 0:
            self._new_game()

    def _draw(self):
        self.screen.fill(BLACK)
        self.dungeon.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)
        self.player.draw(self.screen)
        self._draw_hud()
        pygame.display.flip()

    def _draw_hud(self):
        pygame.draw.line(self.screen, GRAY, (0, 560), (SCREEN_WIDTH, 560), 1)
        hp = self.font.render(f"HP: {int(self.player.health)}", True, WHITE)
        hint = self.font.render("WASD / Arrows to move   R to restart   ESC to quit", True, GRAY)
        self.screen.blit(hp, (10, 568))
        self.screen.blit(hint, (130, 568))
