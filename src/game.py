import pygame
import sys
import random
from src.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TILE_SIZE,
    BLACK, WHITE, GRAY, GOLD_COLOR, TEAM_COLORS,
    CHARACTER_STATS, SERVER_URL,
)
from src.arena import Arena, SPAWN_LEFT, SPAWN_RIGHT, build_arena_background
from src.player import Player, TANK_SUPER_DAMAGE
from src.ai_bot import AIBot
from src.potion import Potion
# NetworkClient imported lazily so the game works in browser (no threading)

POTION_LIMIT = 2
POTION_SPAWN_RANGE = (360, 600)   # frames (6-10s @ 60fps)


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Dungeon Blitz: Arena")
        self.clock = pygame.time.Clock()
        self.font       = pygame.font.Font(None, 32)
        self.big_font   = pygame.font.Font(None, 80)
        self.small_font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 100)

        self.net = None
        self.multiplayer = False
        self.is_host = False
        self._net_tick = 0
        self._mp_action = None

        self._code_input = ''
        self._waiting_msg = ''
        self._menu_banner = ''
        self._menu_sel = 0
        self._char_sel = 'tank'
        self._chosen_char = 'tank'

        self.mode = None           # 'ai' or 'mp'
        self.arena = None
        self.player = None
        self.opponent = None
        self.bot = None
        self.potions = []
        self._potion_timer = 0

        self._ambient_bg = build_arena_background((SCREEN_WIDTH, SCREEN_HEIGHT))
        self._particles = [self._make_particle() for _ in range(40)]

        self.state = 'menu'

    # ----------------------------------------------------------------- setup

    def _start_ai_match(self):
        self.mode = 'ai'
        self.multiplayer = False
        self.arena = Arena()
        self.player = Player(*SPAWN_LEFT, char=self._chosen_char, pid=0)
        opp_char = random.choice(list(CHARACTER_STATS.keys()))
        self.opponent = Player(*SPAWN_RIGHT, char=opp_char, pid=1)
        self.bot = AIBot(self.opponent)
        self.potions = []
        self._potion_timer = random.randint(*POTION_SPAWN_RANGE)
        self.state = 'playing'

    def _reset_match(self):
        if not self.player or not self.opponent:
            return
        p1_spawn = SPAWN_LEFT if self.player.pid == 0 else SPAWN_RIGHT
        p2_spawn = SPAWN_RIGHT if self.player.pid == 0 else SPAWN_LEFT
        self.player.health = self.player.max_health
        self.player.rect.topleft = p1_spawn
        self.player.super_meter = 0
        self.opponent.health = self.opponent.max_health
        self.opponent.rect.topleft = p2_spawn
        self.opponent.super_meter = 0
        self.potions = []
        self._potion_timer = random.randint(*POTION_SPAWN_RANGE)
        self.state = 'playing'

    # ------------------------------------------------------------------- run

    def tick(self):
        self.clock.tick(FPS)
        self._handle_events()
        self._update()
        self._draw()

    def run(self):
        while True:
            self.tick()

    # --------------------------------------------------------------- events

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type != pygame.KEYDOWN:
                continue
            key = event.key

            if key == pygame.K_ESCAPE:
                if self.state == 'menu':
                    pygame.quit(); sys.exit()
                else:
                    self.state = 'menu'
                    self._menu_sel = 0

            # ---------- MENU
            elif self.state == 'menu':
                opts = ['ai', 'mp']
                if key == pygame.K_UP:
                    self._menu_sel = (self._menu_sel - 1) % len(opts)
                elif key == pygame.K_DOWN:
                    self._menu_sel = (self._menu_sel + 1) % len(opts)
                elif key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._menu_banner = ''
                    if opts[self._menu_sel] == 'ai':
                        self.state = 'char_select'
                    else:
                        self.state = 'mp_menu'
                        self._menu_sel = 0

            # ---------- CHAR SELECT (AI)
            elif self.state == 'char_select':
                if key in (pygame.K_LEFT, pygame.K_RIGHT):
                    self._char_sel = 'speedster' if self._char_sel == 'tank' else 'tank'
                elif key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._chosen_char = self._char_sel
                    self._start_ai_match()

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
                if key == pygame.K_SPACE:
                    self._do_attack()
                elif key == pygame.K_q:
                    self._do_super()
                elif key == pygame.K_LSHIFT or key == pygame.K_RSHIFT:
                    self.player.try_dash(self.arena)

            # ---------- VICTORY / DEFEAT
            elif self.state in ('victory', 'defeat'):
                if key == pygame.K_r:
                    if self.mode == 'mp' and self.net:
                        self.net.relay({'t': 'rematch'})
                    self._reset_match()

    # ------------------------------------------------------------- networking

    def _start_host(self):
        try:
            from src.network import NetworkClient
        except Exception:
            self._waiting_msg = 'Multiplayer not available in browser.\nPlay vs AI instead!'
            self.state = 'mp_host'
            return
        self.is_host = True
        self.net = NetworkClient(SERVER_URL)
        self.net.start()
        self.net.send({'type': 'create'})
        self._waiting_msg = 'Connecting to server...'
        self.state = 'mp_host'

    def _start_join(self, code):
        try:
            from src.network import NetworkClient
        except Exception:
            self._waiting_msg = 'Multiplayer not available in browser.'
            return
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
                self._waiting_msg = f"Room code: {msg['code']}\nWaiting for opponent..."

            elif t == 'p2_joined':
                self._begin_pvp_match(pid=0)

            elif t == 'joined':
                self.net.player_id = 1
                self._begin_pvp_match(pid=1)
                self._waiting_msg = ''

            elif t == 'error':
                self._waiting_msg = f"Error: {msg.get('msg')}"

            elif t == 'p_left':
                self.net = None
                self.multiplayer = False
                self.mode = None
                self._menu_banner = 'Opponent disconnected.'
                self.state = 'menu'
                self._menu_sel = 0

            elif t == 'relay':
                self._handle_relay(msg.get('data', {}))

    def _begin_pvp_match(self, pid):
        self.mode = 'mp'
        self.multiplayer = True
        self.arena = Arena()
        my_spawn  = SPAWN_LEFT if pid == 0 else SPAWN_RIGHT
        opp_spawn = SPAWN_RIGHT if pid == 0 else SPAWN_LEFT
        self.player = Player(*my_spawn, char=self._chosen_char, pid=pid)
        self.opponent = Player(*opp_spawn, char='tank', pid=1 - pid)
        self.potions = []
        self._potion_timer = random.randint(*POTION_SPAWN_RANGE)
        self.net.relay({'t': 'char', 'char': self._chosen_char})
        self.state = 'playing'

    def _handle_relay(self, data):
        d = data.get('t')
        if d == 'pos' and self.opponent:
            self.opponent.rect.x = data['x']
            self.opponent.rect.y = data['y']
            self.opponent.health = data['h']
            self.opponent._facing = tuple(data.get('facing', self.opponent._facing))
            self.opponent.super_meter = data.get('super', self.opponent.super_meter)

        elif d == 'hit' and self.player:
            self.player.take_damage(data['dmg'])

        elif d == 'char' and self.opponent:
            old_pos = self.opponent.rect.topleft
            self.opponent = Player(old_pos[0], old_pos[1], char=data['char'], pid=self.opponent.pid)

        elif d == 'rematch':
            self._reset_match()

    def _send_pos(self):
        if self.net and self.state == 'playing':
            self._net_tick += 1
            if self._net_tick % 2 == 0:
                self.net.relay({'t': 'pos', **self.player.to_dict()})

    # --------------------------------------------------------------- combat

    def _do_attack(self):
        if self.mode == 'ai':
            self.player.attack([self.opponent])
        elif self.mode == 'mp':
            if self.player.try_attack_remote(self.opponent) and self.net:
                self.net.relay({'t': 'hit', 'dmg': self.player.attack_damage})

    def _do_super(self):
        if self.mode == 'ai':
            self.player.use_super([self.opponent])
        elif self.mode == 'mp':
            activated, hit = self.player.try_super_remote(self.opponent)
            if activated and hit and self.net:
                self.net.relay({'t': 'hit', 'dmg': TANK_SUPER_DAMAGE})

    # --------------------------------------------------------------- update

    def _update(self):
        self._poll_network()
        self._update_particles()

        if self.state != 'playing':
            return

        self.player.tick()
        self.opponent.tick()
        self.arena.update()
        self.player.handle_input(self.arena)
        self._send_pos()

        if self.mode == 'ai':
            self.bot.update(self.player, self.arena)

        self._update_potions()
        for p in self.potions:
            p.collect(self.player)
            if self.mode == 'ai':
                p.collect(self.opponent)
        self.potions = [p for p in self.potions if not p.collected]

        if self.player.is_dead:
            self.state = 'defeat'
        elif self.opponent.is_dead:
            self.state = 'victory'

    def _update_potions(self):
        self._potion_timer -= 1
        if self._potion_timer <= 0 and len(self.potions) < POTION_LIMIT:
            self._spawn_potion()
            self._potion_timer = random.randint(*POTION_SPAWN_RANGE)

    def _spawn_potion(self):
        for _ in range(20):
            c = random.randint(1, self.arena.cols - 2)
            r = random.randint(1, self.arena.rows - 2)
            if not self.arena.is_wall(c, r):
                self.potions.append(Potion(c * TILE_SIZE, r * TILE_SIZE))
                return

    # ------------------------------------------------------------ particles

    def _make_particle(self):
        return {
            'x': random.uniform(0, SCREEN_WIDTH),
            'y': random.uniform(0, SCREEN_HEIGHT),
            'vy': random.uniform(0.15, 0.5),
            'r': random.uniform(1, 2.5),
            'a': random.randint(40, 110),
        }

    def _update_particles(self):
        for p in self._particles:
            p['y'] -= p['vy']
            if p['y'] < -5:
                p['y'] = SCREEN_HEIGHT + 5
                p['x'] = random.uniform(0, SCREEN_WIDTH)

    def _draw_ambient_bg(self):
        self.screen.blit(self._ambient_bg, (0, 0))
        for p in self._particles:
            pygame.draw.circle(
                self.screen, (160, 140, 255),
                (int(p['x']), int(p['y'])), p['r'],
            )

    # ----------------------------------------------------------------- draw

    def _draw(self):
        self.screen.fill(BLACK)

        if self.state == 'menu':
            self._draw_ambient_bg()
            self._draw_menu()
        elif self.state in ('char_select', 'char_select_mp'):
            self._draw_ambient_bg()
            self._draw_char_select()
        elif self.state == 'mp_menu':
            self._draw_ambient_bg()
            self._draw_mp_menu()
        elif self.state in ('mp_host', 'mp_connecting'):
            self._draw_ambient_bg()
            self._draw_waiting()
        elif self.state == 'mp_join':
            self._draw_ambient_bg()
            self._draw_join_screen()
        elif self.state == 'playing':
            self._draw_game()
        elif self.state == 'victory':
            self._draw_game()
            self._draw_overlay('VICTORY!', GOLD_COLOR, 'Press R to rematch  |  ESC for menu')
        elif self.state == 'defeat':
            self._draw_game()
            self._draw_overlay('DEFEATED', (220, 50, 50), 'Press R to rematch  |  ESC for menu')

        pygame.display.flip()

    def _draw_game(self):
        self.arena.draw(self.screen)
        for p in self.potions:
            p.draw(self.screen)
        opp_label = 'AI' if self.mode == 'ai' else 'OPPONENT'
        self.opponent.draw(self.screen, label=opp_label)
        self.player.draw(self.screen, label='YOU')
        self._draw_hud()

    def _draw_hud(self):
        bar_w = 220
        self._draw_top_bar(10, 'YOU', self.player, TEAM_COLORS[self.player.pid % 2], align='left')
        self._draw_top_bar(SCREEN_WIDTH - 10 - bar_w, 'AI' if self.mode == 'ai' else 'OPPONENT',
                            self.opponent, TEAM_COLORS[self.opponent.pid % 2], align='right')

        pygame.draw.line(self.screen, GRAY, (0, 560), (SCREEN_WIDTH, 560), 1)
        pygame.draw.rect(self.screen, (60, 0, 80), (340, 568, 120, 18))
        pygame.draw.rect(self.screen, (180, 0, 255), (340, 568, int(1.2 * self.player.super_meter), 18))
        q = self.small_font.render('Q=SUPER', True, (200, 150, 255))
        self.screen.blit(q, (340, 588))
        hint = self.small_font.render('SPACE=atk  SHIFT=dash  WASD=move', True, GRAY)
        self.screen.blit(hint, hint.get_rect(midright=(SCREEN_WIDTH - 10, 577)))

    def _draw_top_bar(self, x, label, fighter, color, align='left'):
        bar_w, bar_h = 220, 16
        ratio = max(0, fighter.health / fighter.max_health)
        name = self.font.render(f'{label}  ({fighter.char})', True, color)
        if align == 'left':
            self.screen.blit(name, (x, 8))
        else:
            self.screen.blit(name, name.get_rect(topright=(x + bar_w, 8)))
        pygame.draw.rect(self.screen, (40, 0, 0), (x, 34, bar_w, bar_h), border_radius=4)
        fill_w = int(bar_w * ratio)
        fill_rect = (x, 34, fill_w, bar_h) if align == 'left' else (x + bar_w - fill_w, 34, fill_w, bar_h)
        bar_color = (0, 200, 0) if ratio > 0.3 else (220, 60, 40)
        pygame.draw.rect(self.screen, bar_color, fill_rect, border_radius=4)
        pygame.draw.rect(self.screen, color, (x, 34, bar_w, bar_h), 2, border_radius=4)
        hp_t = self.small_font.render(f'{max(0, int(fighter.health))}/{fighter.max_health}', True, WHITE)
        self.screen.blit(hp_t, hp_t.get_rect(center=(x + bar_w // 2, 42)))

    def _draw_overlay(self, title, color, subtitle):
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 170))
        self.screen.blit(surf, (0, 0))
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        t = self.big_font.render(title, True, color)
        b = self.font.render(subtitle, True, GRAY)
        self.screen.blit(t, t.get_rect(center=(cx, cy - 20)))
        self.screen.blit(b, b.get_rect(center=(cx, cy + 40)))

    def _draw_menu(self):
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        title = self.title_font.render('DUNGEON', True, GOLD_COLOR)
        title2 = self.title_font.render('BLITZ', True, (255, 100, 50))
        self.screen.blit(title,  title.get_rect(center=(cx, cy - 150)))
        self.screen.blit(title2, title2.get_rect(center=(cx, cy - 70)))
        opts = ['Battle AI', 'Battle Online Friend']
        for i, opt in enumerate(opts):
            sel = i == self._menu_sel
            color = GOLD_COLOR if sel else GRAY
            prefix = '> ' if sel else '  '
            t = self.font.render(prefix + opt, True, color)
            self.screen.blit(t, t.get_rect(center=(cx, cy + 30 + i * 50)))
        if self._menu_banner:
            banner = self.small_font.render(self._menu_banner, True, (255, 150, 150))
            self.screen.blit(banner, banner.get_rect(center=(cx, cy + 110)))
        hint = self.small_font.render('Arrow keys to navigate  |  SPACE / ENTER to select', True, GRAY)
        self.screen.blit(hint, hint.get_rect(center=(cx, SCREEN_HEIGHT - 30)))

    def _draw_mp_menu(self):
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        t = self.big_font.render('ONLINE FRIEND', True, GOLD_COLOR)
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
        t = self.big_font.render('CHOOSE FIGHTER', True, GOLD_COLOR)
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
            pygame.draw.circle(self.screen, stats['color'], (x_positions[i], cy - 35), 25)
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
            color = GOLD_COLOR if i == 0 and len(line) <= 16 else WHITE
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
