import pygame
import sys
import random
from src.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TILE_SIZE,
    BLACK, WHITE, GRAY, DARK_GRAY, GOLD_COLOR, GREEN,
    CHARACTER_STATS, SERVER_URL,
)
from src.dungeon import Dungeon
from src.player import Player
from src.enemy import Enemy
from src.potion import Potion
from src.items import Key, Portal
from src.network import NetworkClient

# Fixed spawn and item positions (verified floor tiles)
SPAWN_P1    = (42, 42)
SPAWN_P2    = (682, 42)
KEY_POS     = (15 * TILE_SIZE, 5 * TILE_SIZE)
PORTAL_POS  = (18 * TILE_SIZE, 12 * TILE_SIZE)

ENEMY_SPAWNS = [
    (202, 42), (122, 202), (482, 282),
    (602, 442), (282, 482), (682, 162),
]

LEVEL_CONFIGS = {
    1: [('goblin', 0), ('goblin', 1), ('goblin', 2)],
    2: [('goblin', 0), ('goblin', 1), ('orc', 2)],
    3: [('goblin', 0), ('goblin', 1), ('orc', 2), ('orc', 3)],
}
DEFAULT_CONFIG = [('goblin', 0), ('goblin', 2), ('orc', 3), ('orc', 4), ('goblin', 5)]


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Dungeon Blitz")
        self.clock = pygame.time.Clock()
        self.font       = pygame.font.Font(None, 32)
        self.big_font   = pygame.font.Font(None, 80)
        self.small_font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 100)

        self.net: NetworkClient | None = None
        self.multiplayer = False
        self.is_host = False
        self._net_tick = 0

        self._code_input = ''
        self._waiting_msg = ''
        self._menu_sel = 0
        self._char_sel = 'tank'
        self._chosen_char = 'tank'

        self.state = 'menu'
        self._init_game_vars()

    # ----------------------------------------------------------------- setup

    def _init_game_vars(self):
        self.level   = 1
        self.dungeon = Dungeon()
        self.player  = Player(*SPAWN_P1, char=self._chosen_char, pid=0)
        self.player2: Player | None = None
        self.enemies = self._make_enemies()
        self.potions: list[Potion] = []
        self.key     = Key(*KEY_POS)
        self.portal  = Portal(*PORTAL_POS)

    def _make_enemies(self):
        config = LEVEL_CONFIGS.get(self.level, DEFAULT_CONFIG)
        return [Enemy(ENEMY_SPAWNS[pos][0], ENEMY_SPAWNS[pos][1], kind) for kind, pos in config]

    def _next_level(self):
        self.level += 1
        gold_carry  = self.player.gold
        score_carry = self.player.score
        hp_carry    = min(self.player.max_health, self.player.health + 20)
        self._init_game_vars()
        self.player.gold  = gold_carry
        self.player.score = score_carry
        self.player.health = hp_carry
        self.state = 'playing'

    # ------------------------------------------------------------------- run

    def run(self):
        while True:
            dt = self.clock.tick(FPS)
            self._handle_events()
            self._update()
            self._draw()

    # --------------------------------------------------------------- events

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type != pygame.KEYDOWN:
                continue
            key = event.key

            if key == pygame.K_ESCAPE:
                if self.state == 'playing':
                    self.state = 'menu'
                else:
                    pygame.quit(); sys.exit()

            # ---------- MENU
            elif self.state == 'menu':
                opts = ['single', 'multiplayer']
                if key == pygame.K_UP:
                    self._menu_sel = (self._menu_sel - 1) % len(opts)
                elif key == pygame.K_DOWN:
                    self._menu_sel = (self._menu_sel + 1) % len(opts)
                elif key in (pygame.K_RETURN, pygame.K_SPACE):
                    if opts[self._menu_sel] == 'single':
                        self.state = 'char_select'
                    else:
                        self.state = 'mp_menu'
                        self._menu_sel = 0

            # ---------- CHAR SELECT
            elif self.state == 'char_select':
                if key in (pygame.K_LEFT, pygame.K_RIGHT):
                    self._char_sel = 'speedster' if self._char_sel == 'tank' else 'tank'
                elif key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._chosen_char = self._char_sel
                    self.multiplayer = False
                    self._init_game_vars()
                    self.state = 'playing'

            # ---------- MP MENU
            elif self.state == 'mp_menu':
                opts = ['host', 'join', 'back']
                if key == pygame.K_UP:
                    self._menu_sel = (self._menu_sel - 1) % len(opts)
                elif key == pygame.K_DOWN:
                    self._menu_sel = (self._menu_sel + 1) % len(opts)
                elif key in (pygame.K_RETURN, pygame.K_SPACE):
                    pick = opts[self._menu_sel]
                    if pick == 'back':
                        self.state = 'menu'; self._menu_sel = 0
                    else:
                        self.state = 'char_select_mp'
                        self._mp_action = pick

            # ---------- CHAR SELECT (MP)
            elif self.state == 'char_select_mp':
                if key in (pygame.K_LEFT, pygame.K_RIGHT):
                    self._char_sel = 'speedster' if self._char_sel == 'tank' else 'tank'
                elif key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._chosen_char = self._char_sel
                    if self._mp_action == 'host':
                        self._start_host()
                    else:
                        self.state = 'mp_join'
                        self._code_input = ''

            # ---------- MP JOIN (enter code)
            elif self.state == 'mp_join':
                if key == pygame.K_BACKSPACE:
                    self._code_input = self._code_input[:-1]
                elif key == pygame.K_RETURN and len(self._code_input) == 4:
                    self._start_join(self._code_input.upper())
                elif event.unicode.isalnum() and len(self._code_input) < 4:
                    self._code_input += event.unicode.upper()

            # ---------- PLAYING
            elif self.state == 'playing':
                if key == pygame.K_r:
                    self._init_game_vars(); self.state = 'playing'
                elif key == pygame.K_SPACE:
                    self._do_attack()
                elif key == pygame.K_q:
                    self._do_super()
                elif key == pygame.K_LSHIFT or key == pygame.K_RSHIFT:
                    self.player.try_dash(self.dungeon)

            # ---------- GAME OVER
            elif self.state == 'game_over':
                if key == pygame.K_r:
                    self.level = 1; self._init_game_vars(); self.state = 'playing'

            # ---------- LEVEL CLEAR
            elif self.state == 'level_clear':
                if key == pygame.K_SPACE:
                    self._next_level()

    # ------------------------------------------------------------- networking

    def _start_host(self):
        self.multiplayer = True
        self.is_host = True
        self.net = NetworkClient(SERVER_URL)
        self.net.start()
        self.net.send({'type': 'create'})
        self._waiting_msg = 'Connecting to server...'
        self.state = 'mp_host'

    def _start_join(self, code):
        self.multiplayer = True
        self.is_host = False
        self.net = NetworkClient(SERVER_URL)
        self.net.start()
        self.net.send({'type': 'join', 'code': code})
        self._waiting_msg = f'Joining room {code}...'
        self.state = 'mp_connecting'

    def _poll_network(self):
        if not self.net:
            return
        for msg in self.net.poll():
            t = msg.get('type')

            if t == 'created':
                self.net.room_code = msg['code']
                self.net.player_id = 0
                self._waiting_msg = f"Room code: {msg['code']}\nWaiting for player 2..."
                self._init_game_vars()

            elif t == 'p2_joined':
                self.player2 = Player(*SPAWN_P2, char='speedster', pid=1)
                self.state = 'playing'

            elif t == 'joined':
                self.net.player_id = 1
                self._init_game_vars()
                self.player = Player(*SPAWN_P2, char=self._chosen_char, pid=1)
                self.player2 = Player(*SPAWN_P1, char='tank', pid=0)
                self.state = 'playing'
                self._waiting_msg = ''

            elif t == 'error':
                self._waiting_msg = f"Error: {msg.get('msg')}"

            elif t == 'p_left':
                self._waiting_msg = 'Other player disconnected.'
                self.multiplayer = False

            elif t == 'relay':
                self._handle_relay(msg.get('data', {}))

    def _handle_relay(self, data):
        d = data.get('t')
        if d == 'pos' and self.player2:
            self.player2.rect.x = data['x']
            self.player2.rect.y = data['y']
            self.player2.health = data['h']
            self.player2.has_key = data.get('key', False)

        elif d == 'kill':
            idx = data.get('idx')
            if idx is not None and idx < len(self.enemies):
                enemy = self.enemies[idx]
                self.player.gold  += enemy.gold // 2
                self.player.score += enemy.score // 2
                self.enemies.pop(idx)
                if random.random() < 0.4:
                    self.potions.append(Potion(enemy.rect.x, enemy.rect.y))

        elif d == 'key':
            self.key.collected = True

        elif d == 'exit':
            self.state = 'level_clear'

    def _send_pos(self):
        if self.net and self.state == 'playing':
            self._net_tick += 1
            if self._net_tick % 2 == 0:
                self.net.relay({'t': 'pos', **self.player.to_dict()})

    # --------------------------------------------------------------- combat

    def _do_attack(self):
        killed = self.player.attack(self.enemies)
        for enemy in killed:
            idx = self.enemies.index(enemy)
            self.enemies.remove(enemy)
            self.player.gold  += enemy.gold
            self.player.score += enemy.score
            if random.random() < 0.4:
                self.potions.append(Potion(enemy.rect.x, enemy.rect.y))
            if self.multiplayer and self.net:
                self.net.relay({'t': 'kill', 'idx': idx})

    def _do_super(self):
        killed = self.player.use_super(self.enemies)
        for enemy in killed:
            idx = self.enemies.index(enemy)
            self.enemies.remove(enemy)
            self.player.gold  += enemy.gold
            self.player.score += enemy.score
            if self.multiplayer and self.net:
                self.net.relay({'t': 'kill', 'idx': idx})

    # --------------------------------------------------------------- update

    def _update(self):
        self._poll_network()

        if self.state != 'playing':
            return

        self.player.tick()
        self.player.handle_input(self.dungeon)
        self._send_pos()

        for enemy in self.enemies:
            enemy.update(self.player, self.dungeon)

        # Enemy contact damage
        for enemy in self.enemies:
            if self.player.rect.colliderect(enemy.rect):
                self.player.take_damage(0.3)
        if self.player.health <= 0:
            self.state = 'game_over'
            return

        # Potions
        for p in self.potions:
            p.collect(self.player)
        self.potions = [p for p in self.potions if not p.collected]

        # Key
        self.key.update()
        if self.key.collect(self.player):
            self.player.has_key = True
            if self.multiplayer and self.net:
                self.net.relay({'t': 'key'})

        # Portal
        self.portal.update()
        self.portal.active = self.player.has_key and not self.enemies
        if self.portal.active and self.portal.rect.colliderect(self.player.rect):
            if self.multiplayer and self.net:
                self.net.relay({'t': 'exit'})
            self.state = 'level_clear'

    # ----------------------------------------------------------------- draw

    def _draw(self):
        self.screen.fill(BLACK)

        if self.state == 'menu':
            self._draw_menu()
        elif self.state in ('char_select', 'char_select_mp'):
            self._draw_char_select()
        elif self.state == 'mp_menu':
            self._draw_mp_menu()
        elif self.state in ('mp_host', 'mp_connecting'):
            self._draw_waiting()
        elif self.state == 'mp_join':
            self._draw_join_screen()
        elif self.state == 'playing':
            self._draw_game()
        elif self.state == 'game_over':
            self._draw_game()
            self._draw_overlay('GAME OVER', (220, 50, 50), 'Press R to try again')
        elif self.state == 'level_clear':
            self._draw_game()
            self._draw_overlay(f'LEVEL {self.level} CLEAR!', GOLD_COLOR, 'Press SPACE for next level')

        pygame.display.flip()

    def _draw_game(self):
        self.dungeon.draw(self.screen)
        self.key.draw(self.screen)
        self.portal.draw(self.screen)
        for p in self.potions:
            p.draw(self.screen)
        for e in self.enemies:
            e.draw(self.screen)
        if self.player2:
            self.player2.draw(self.screen, label='P2')
        self.player.draw(self.screen, label='P1' if self.multiplayer else None)
        self._draw_hud()

    def _draw_hud(self):
        pygame.draw.line(self.screen, GRAY, (0, 560), (SCREEN_WIDTH, 560), 1)
        hp    = self.font.render(f'HP: {int(self.player.health)}', True, WHITE)
        gold  = self.font.render(f'Gold: {self.player.gold}', True, GOLD_COLOR)
        score = self.font.render(f'Score: {self.player.score}', True, (100, 200, 255))
        lv    = self.font.render(f'Lv.{self.level}', True, GRAY)
        key_s = self.font.render('KEY', True, GOLD_COLOR if self.player.has_key else (60, 60, 60))
        self.screen.blit(hp,    (10,  566))
        self.screen.blit(gold,  (110, 566))
        self.screen.blit(score, (240, 566))
        self.screen.blit(lv,    (385, 566))
        self.screen.blit(key_s, (435, 566))
        # Super meter
        pygame.draw.rect(self.screen, (60, 0, 80), (490, 568, 100, 18))
        pygame.draw.rect(self.screen, (180, 0, 255), (490, 568, self.player.super_meter, 18))
        q = self.small_font.render('Q=SUPER', True, (200, 150, 255))
        self.screen.blit(q, (595, 570))
        hint = self.small_font.render('SPACE=atk  SHIFT=dash  WASD=move', True, GRAY)
        self.screen.blit(hint, (680, 570))

    def _draw_overlay(self, title, color, subtitle):
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 160))
        self.screen.blit(surf, (0, 0))
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        t = self.big_font.render(title, True, color)
        s = self.font.render(f'Score: {self.player.score}   Gold: {self.player.gold}', True, WHITE)
        b = self.font.render(subtitle, True, GRAY)
        self.screen.blit(t, t.get_rect(center=(cx, cy - 60)))
        self.screen.blit(s, s.get_rect(center=(cx, cy + 10)))
        self.screen.blit(b, b.get_rect(center=(cx, cy + 50)))

    def _draw_menu(self):
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        title = self.title_font.render('DUNGEON', True, GOLD_COLOR)
        title2 = self.title_font.render('BLITZ', True, (255, 100, 50))
        self.screen.blit(title,  title.get_rect(center=(cx, cy - 130)))
        self.screen.blit(title2, title2.get_rect(center=(cx, cy - 50)))
        opts = ['Single Player', 'Multiplayer (2 Players)']
        for i, opt in enumerate(opts):
            sel = i == self._menu_sel
            color = GOLD_COLOR if sel else GRAY
            prefix = '> ' if sel else '  '
            t = self.font.render(prefix + opt, True, color)
            self.screen.blit(t, t.get_rect(center=(cx, cy + 40 + i * 50)))
        hint = self.small_font.render('Arrow keys to navigate  |  SPACE / ENTER to select', True, GRAY)
        self.screen.blit(hint, hint.get_rect(center=(cx, SCREEN_HEIGHT - 30)))

    def _draw_mp_menu(self):
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        t = self.big_font.render('MULTIPLAYER', True, GOLD_COLOR)
        self.screen.blit(t, t.get_rect(center=(cx, cy - 100)))
        opts = ['Host a Game', 'Join a Game', 'Back']
        for i, opt in enumerate(opts):
            sel = i == self._menu_sel
            color = GOLD_COLOR if sel else GRAY
            prefix = '> ' if sel else '  '
            s = self.font.render(prefix + opt, True, color)
            self.screen.blit(s, s.get_rect(center=(cx, cy - 10 + i * 50)))

    def _draw_char_select(self):
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        t = self.big_font.render('CHOOSE CHARACTER', True, GOLD_COLOR)
        self.screen.blit(t, t.get_rect(center=(cx, 60)))
        chars = ['tank', 'speedster']
        x_positions = [cx - 160, cx + 160]
        for i, char in enumerate(chars):
            stats = CHARACTER_STATS[char]
            selected = self._char_sel == char
            box_color = (60, 40, 20) if selected else (25, 25, 25)
            border = GOLD_COLOR if selected else GRAY
            box = pygame.Rect(x_positions[i] - 100, cy - 80, 200, 220)
            pygame.draw.rect(self.screen, box_color, box, border_radius=8)
            pygame.draw.rect(self.screen, border, box, 2, border_radius=8)
            # Character swatch
            swatch = pygame.Rect(x_positions[i] - 25, cy - 60, 50, 50)
            pygame.draw.rect(self.screen, stats['color'], swatch)
            name = self.font.render(char.upper(), True, WHITE)
            self.screen.blit(name, name.get_rect(center=(x_positions[i], cy + 10)))
            for j, line in enumerate(stats['desc']):
                d = self.small_font.render(line, True, GRAY)
                self.screen.blit(d, d.get_rect(center=(x_positions[i], cy + 45 + j * 22)))
            super_t = self.small_font.render(f"Super: {stats['super_name']}", True, (180, 80, 255))
            self.screen.blit(super_t, super_t.get_rect(center=(x_positions[i], cy + 100)))
        hint = self.font.render('LEFT / RIGHT to choose   SPACE to confirm', True, GRAY)
        self.screen.blit(hint, hint.get_rect(center=(cx, SCREEN_HEIGHT - 40)))

    def _draw_waiting(self):
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        for i, line in enumerate(self._waiting_msg.split('\n')):
            color = GOLD_COLOR if i == 0 and len(line) <= 10 else WHITE
            t = self.big_font.render(line, True, color) if i == 0 else self.font.render(line, True, WHITE)
            self.screen.blit(t, t.get_rect(center=(cx, cy - 40 + i * 60)))
        hint = self.small_font.render('Share this code with your friend', True, GRAY)
        self.screen.blit(hint, hint.get_rect(center=(cx, cy + 80)))

    def _draw_join_screen(self):
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        t = self.big_font.render('ENTER ROOM CODE', True, GOLD_COLOR)
        self.screen.blit(t, t.get_rect(center=(cx, cy - 80)))
        code_display = self._code_input + '_' * (4 - len(self._code_input))
        code_t = self.title_font.render(code_display, True, WHITE)
        self.screen.blit(code_t, code_t.get_rect(center=(cx, cy)))
        hint = self.font.render('Type 4-letter code then press ENTER', True, GRAY)
        self.screen.blit(hint, hint.get_rect(center=(cx, cy + 80)))
        if self._waiting_msg:
            err = self.font.render(self._waiting_msg, True, (220, 50, 50))
            self.screen.blit(err, err.get_rect(center=(cx, cy + 120)))
