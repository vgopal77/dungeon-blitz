import pygame
import sys
import random
from src.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TILE_SIZE,
    BLACK, WHITE, GRAY, GOLD_COLOR, TEAM_COLORS,
    CHARACTER_STATS, SERVER_URL,
    NBA_TEAMS, NBA_TEAM_ORDER,
)
from src.arena import Arena, SPAWN_LEFT, SPAWN_RIGHT, build_arena_background
from src.player import Player, TANK_SUPER_DAMAGE
from src.ai_bot import AIBot
from src.potion import Potion

POTION_LIMIT       = 2
POTION_SPAWN_RANGE = (360, 600)


class Game:
    def __init__(self):
        self.screen     = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('Basketball Blitz: Arena')
        self.clock      = pygame.time.Clock()
        self.font       = pygame.font.Font(None, 32)
        self.big_font   = pygame.font.Font(None, 80)
        self.small_font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 96)
        self.micro_font = pygame.font.Font(None, 18)

        self.net         = None
        self.multiplayer = False
        self.is_host     = False
        self._net_tick   = 0
        self._mp_action  = None

        self._code_input   = ''
        self._waiting_msg  = ''
        self._menu_banner  = ''
        self._menu_sel     = 0

        # Team / character selection
        self._team_sel     = 0          # index into NBA_TEAM_ORDER
        self._chosen_team  = 'bulls'
        self._chosen_char  = 'tank'     # derived from team

        # Last-action overlay (NBA 2K-style)
        self._last_action       = ''
        self._last_action_timer = 0

        self.mode     = None
        self.arena    = None
        self.player   = None
        self.opponent = None
        self.bot      = None
        self.potions  = []
        self._potion_timer = 0

        self._ambient_bg = build_arena_background((SCREEN_WIDTH, SCREEN_HEIGHT))
        self._particles  = [self._make_particle() for _ in range(40)]

        self.state = 'menu'

    # ----------------------------------------------------------------- setup

    def _start_ai_match(self):
        self.mode        = 'ai'
        self.multiplayer = False
        self.arena       = Arena()
        self.player   = Player(*SPAWN_LEFT,  team=self._chosen_team, pid=0)
        opp_team      = random.choice([t for t in NBA_TEAM_ORDER if t != self._chosen_team])
        self.opponent = Player(*SPAWN_RIGHT, team=opp_team, pid=1)
        self.bot      = AIBot(self.opponent)
        self.potions  = []
        self._potion_timer = random.randint(*POTION_SPAWN_RANGE)
        self._last_action  = ''
        self.state     = 'playing'

    def _reset_match(self):
        if not self.player or not self.opponent:
            return
        p1_spawn = SPAWN_LEFT  if self.player.pid == 0 else SPAWN_RIGHT
        p2_spawn = SPAWN_RIGHT if self.player.pid == 0 else SPAWN_LEFT
        self.player.health      = self.player.max_health
        self.player.rect.topleft = p1_spawn
        self.player.super_meter  = 0
        self.opponent.health      = self.opponent.max_health
        self.opponent.rect.topleft = p2_spawn
        self.opponent.super_meter  = 0
        self.potions       = []
        self._potion_timer = random.randint(*POTION_SPAWN_RANGE)
        self._last_action  = ''
        self.state         = 'playing'

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
                    self.state    = 'menu'
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
                        self.state     = 'mp_menu'
                        self._menu_sel = 0

            # ---------- TEAM SELECT (AI)
            elif self.state == 'char_select':
                nl = len(NBA_TEAM_ORDER)
                if key == pygame.K_LEFT:
                    self._team_sel = (self._team_sel - 1) % nl
                elif key == pygame.K_RIGHT:
                    self._team_sel = (self._team_sel + 1) % nl
                elif key == pygame.K_UP:
                    self._team_sel = (self._team_sel - 3) % nl
                elif key == pygame.K_DOWN:
                    self._team_sel = (self._team_sel + 3) % nl
                elif key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._chosen_team = NBA_TEAM_ORDER[self._team_sel]
                    self._chosen_char = NBA_TEAMS[self._chosen_team]['char']
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
                        self.state      = 'char_select_mp'
                        self._mp_action = pick

            # ---------- TEAM SELECT (MP)
            elif self.state == 'char_select_mp':
                nl = len(NBA_TEAM_ORDER)
                if key == pygame.K_LEFT:
                    self._team_sel = (self._team_sel - 1) % nl
                elif key == pygame.K_RIGHT:
                    self._team_sel = (self._team_sel + 1) % nl
                elif key == pygame.K_UP:
                    self._team_sel = (self._team_sel - 3) % nl
                elif key == pygame.K_DOWN:
                    self._team_sel = (self._team_sel + 3) % nl
                elif key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._chosen_team = NBA_TEAM_ORDER[self._team_sel]
                    self._chosen_char = NBA_TEAMS[self._chosen_team]['char']
                    if self._mp_action == 'host':
                        self._start_host()
                    else:
                        self.state       = 'mp_join'
                        self._code_input = ''

            # ---------- MP JOIN
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
                    self._set_action('DASH!')

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
        self.net     = NetworkClient(SERVER_URL)
        self.net.start()
        self.net.send({'type': 'create'})
        self._waiting_msg = 'Connecting to server...'
        self.state        = 'mp_host'

    def _start_join(self, code):
        try:
            from src.network import NetworkClient
        except Exception:
            self._waiting_msg = 'Multiplayer not available in browser.'
            return
        self.is_host = False
        self.net     = NetworkClient(SERVER_URL)
        self.net.start()
        self.net.send({'type': 'join', 'code': code})
        self._waiting_msg = f'Joining room {code}...'
        self.state        = 'mp_connecting'

    def _poll_network(self):
        if not self.net:
            return
        for msg in self.net.poll():
            t = msg.get('type')
            if t == 'created':
                self.net.room_code  = msg['code']
                self.net.player_id  = 0
                self._waiting_msg   = f"Room code: {msg['code']}\nWaiting for opponent..."
            elif t == 'p2_joined':
                self._begin_pvp_match(pid=0)
            elif t == 'joined':
                self.net.player_id = 1
                self._begin_pvp_match(pid=1)
                self._waiting_msg  = ''
            elif t == 'error':
                self._waiting_msg = f"Error: {msg.get('msg')}"
            elif t == 'p_left':
                self.net  = None
                self.multiplayer  = False
                self.mode = None
                self._menu_banner = 'Opponent disconnected.'
                self.state        = 'menu'
                self._menu_sel    = 0
            elif t == 'relay':
                self._handle_relay(msg.get('data', {}))

    def _begin_pvp_match(self, pid):
        self.mode        = 'mp'
        self.multiplayer = True
        self.arena       = Arena()
        my_spawn    = SPAWN_LEFT  if pid == 0 else SPAWN_RIGHT
        opp_spawn   = SPAWN_RIGHT if pid == 0 else SPAWN_LEFT
        self.player   = Player(*my_spawn,  team=self._chosen_team, pid=pid)
        self.opponent = Player(*opp_spawn, team='bulls', pid=1 - pid)
        self.potions  = []
        self._potion_timer = random.randint(*POTION_SPAWN_RANGE)
        self.net.relay({'t': 'char', 'team': self._chosen_team, 'char': self._chosen_char})
        self.state = 'playing'

    def _handle_relay(self, data):
        d = data.get('t')
        if d == 'pos' and self.opponent:
            self.opponent.rect.x   = data['x']
            self.opponent.rect.y   = data['y']
            self.opponent.health   = data['h']
            self.opponent._facing  = tuple(data.get('facing', self.opponent._facing))
            self.opponent.super_meter = data.get('super', self.opponent.super_meter)
        elif d == 'hit' and self.player:
            self.player.take_damage(data['dmg'])
        elif d == 'char' and self.opponent:
            old_pos = self.opponent.rect.topleft
            team    = data.get('team')
            char    = data.get('char', 'tank')
            if team:
                self.opponent = Player(old_pos[0], old_pos[1], team=team, pid=self.opponent.pid)
            else:
                self.opponent = Player(old_pos[0], old_pos[1], char=char, pid=self.opponent.pid)
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
            hits = self.player.attack([self.opponent])
            if self.player._atk_flash:
                self._set_action('ATTACK!')
        elif self.mode == 'mp':
            if self.player.try_attack_remote(self.opponent) and self.net:
                self.net.relay({'t': 'hit', 'dmg': self.player.attack_damage})
                self._set_action('ATTACK!')

    def _do_super(self):
        if self.player.super_meter < 100:
            return
        sname = NBA_TEAMS.get(self.player.team, {}).get('char', self.player.char)
        action = 'GROUND SLAM!' if sname == 'tank' else 'SPEED BURST!'
        if self.mode == 'ai':
            self.player.use_super([self.opponent])
            self._set_action(action)
        elif self.mode == 'mp':
            activated, hit = self.player.try_super_remote(self.opponent)
            if activated:
                self._set_action(action)
                if hit and self.net:
                    self.net.relay({'t': 'hit', 'dmg': TANK_SUPER_DAMAGE})

    def _set_action(self, text):
        self._last_action       = text
        self._last_action_timer = 150   # ~2.5 s at 60 fps

    # --------------------------------------------------------------- update

    def _update(self):
        self._poll_network()
        self._update_particles()

        if self._last_action_timer > 0:
            self._last_action_timer -= 1

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
            'x':  random.uniform(0, SCREEN_WIDTH),
            'y':  random.uniform(0, SCREEN_HEIGHT),
            'vy': random.uniform(0.15, 0.5),
            'r':  random.uniform(1, 2.5),
            'a':  random.randint(40, 110),
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
            pygame.draw.circle(self.screen, (180, 155, 80),
                               (int(p['x']), int(p['y'])), p['r'])

    # ----------------------------------------------------------------- draw

    def _draw(self):
        self.screen.fill(BLACK)

        if self.state == 'menu':
            self._draw_ambient_bg()
            self._draw_menu()
        elif self.state in ('char_select', 'char_select_mp'):
            self._draw_ambient_bg()
            self._draw_team_select()
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
        self._draw_controls_box()
        if self._last_action_timer > 0:
            self._draw_last_action()

    # ----------------------------------------------------------------- HUD

    def _draw_hud(self):
        # Left fighter bar
        self._draw_fighter_bar(10, self.player,
                               align='left', is_you=True)
        # Right fighter bar
        bar_w = 230
        self._draw_fighter_bar(SCREEN_WIDTH - 10 - bar_w, self.opponent,
                               align='right', is_you=False)

        # VS divider + super meter
        pygame.draw.line(self.screen, (80, 60, 30), (0, 560), (SCREEN_WIDTH, 560), 1)

        vs = self.font.render('VS', True, (180, 140, 50))
        self.screen.blit(vs, vs.get_rect(center=(SCREEN_WIDTH // 2, 38)))

        # Super meter
        mx, my, mw, mh = 310, 568, 180, 14
        pygame.draw.rect(self.screen, (50, 0, 70), (mx, my, mw, mh), border_radius=4)
        fill = int(mw * self.player.super_meter / 100)
        if fill > 0:
            pygame.draw.rect(self.screen, (180, 0, 255), (mx, my, fill, mh), border_radius=4)
        pygame.draw.rect(self.screen, (120, 0, 180), (mx, my, mw, mh), 1, border_radius=4)
        q = self.micro_font.render('Q = SUPER', True, (200, 150, 255))
        self.screen.blit(q, q.get_rect(center=(mx + mw // 2, my + mh + 8)))

    def _draw_fighter_bar(self, x, fighter, align, is_you):
        bar_w, bar_h = 230, 14
        td   = NBA_TEAMS.get(fighter.team, {})
        abbr = td.get('abbr', fighter.team_abbr if hasattr(fighter, 'team_abbr') else '???')
        name = td.get('name', fighter.team_name if hasattr(fighter, 'team_name') else '')
        prim = td.get('primary', fighter.color)
        num  = td.get('number', '?')

        # Team name + abbreviation
        abbr_surf = self.font.render(abbr, True, prim)
        name_surf = self.micro_font.render(name, True, (180, 160, 130))
        if align == 'left':
            self.screen.blit(abbr_surf, (x, 6))
            self.screen.blit(name_surf, (x, 30))
        else:
            self.screen.blit(abbr_surf, abbr_surf.get_rect(topright=(x + bar_w, 6)))
            self.screen.blit(name_surf, name_surf.get_rect(topright=(x + bar_w, 30)))

        # Health bar
        ratio    = max(0, fighter.health / fighter.max_health)
        bar_col  = (0, 200, 0) if ratio > 0.3 else (220, 60, 40)
        pygame.draw.rect(self.screen, (40, 0, 0),   (x, 46, bar_w, bar_h), border_radius=4)
        fill_w   = int(bar_w * ratio)
        fill_r   = (x, 46, fill_w, bar_h) if align == 'left' else (x + bar_w - fill_w, 46, fill_w, bar_h)
        pygame.draw.rect(self.screen, bar_col, fill_r, border_radius=4)
        pygame.draw.rect(self.screen, prim, (x, 46, bar_w, bar_h), 2, border_radius=4)
        hp_t = self.micro_font.render(f'{max(0, int(fighter.health))}/{fighter.max_health}', True, WHITE)
        self.screen.blit(hp_t, hp_t.get_rect(center=(x + bar_w // 2, 53)))

    # ----------------------------------------------------------------- Controls box (NBA 2K-style)

    def _draw_controls_box(self):
        bx, by = 8, 470
        bw, bh = 188, 86

        box = pygame.Surface((bw, bh), pygame.SRCALPHA)
        box.fill((0, 0, 0, 175))
        pygame.draw.rect(box, (*GOLD_COLOR, 160), (0, 0, bw, bh), 2, border_radius=6)
        self.screen.blit(box, (bx, by))

        # Header
        hdr = self.small_font.render('CONTROLS', True, GOLD_COLOR)
        self.screen.blit(hdr, (bx + 7, by + 6))
        pygame.draw.line(self.screen, (180, 140, 40),
                         (bx + 2, by + 20), (bx + bw - 2, by + 20), 1)

        controls = [
            ('WASD / Arrows', 'Move'),
            ('SPACE',         'Attack'),
            ('SHIFT',         'Dash'),
            ('Q',             'Super'),
        ]
        for i, (k, action) in enumerate(controls):
            ky = by + 26 + i * 15
            k_s = self.micro_font.render(k,      True, WHITE)
            a_s = self.micro_font.render(action, True, GRAY)
            self.screen.blit(k_s, (bx + 7, ky))
            self.screen.blit(a_s, a_s.get_rect(topright=(bx + bw - 6, ky)))

    # ----------------------------------------------------------------- Last-action banner

    def _draw_last_action(self):
        bx, by = SCREEN_WIDTH - 230, 70
        bw, bh = 222, 52

        alpha = min(255, self._last_action_timer * 3)
        box   = pygame.Surface((bw, bh), pygame.SRCALPHA)
        box.fill((0, 0, 0, min(180, alpha)))
        pygame.draw.rect(box, (*GOLD_COLOR, min(200, alpha)), (0, 0, bw, bh), 2, border_radius=6)
        self.screen.blit(box, (bx, by))

        lbl = self.micro_font.render('Last Move:', True, GRAY)
        self.screen.blit(lbl, (bx + 8, by + 6))
        act = self.font.render(self._last_action, True, GOLD_COLOR)
        self.screen.blit(act, act.get_rect(centerx=bx + bw // 2, y=by + 22))

    # ----------------------------------------------------------------- Team select

    def _draw_team_select(self):
        cx = SCREEN_WIDTH // 2

        title = self.big_font.render('CHOOSE YOUR TEAM', True, GOLD_COLOR)
        self.screen.blit(title, title.get_rect(center=(cx, 45)))

        sub = self.small_font.render('Select a team and take the court', True, GRAY)
        self.screen.blit(sub, sub.get_rect(center=(cx, 78)))

        bw, bh  = 168, 138
        gap_x   = 16
        gap_y   = 14
        grid_w  = 3 * bw + 2 * gap_x
        sx      = cx - grid_w // 2
        sy      = 96

        for i, key in enumerate(NBA_TEAM_ORDER):
            td      = NBA_TEAMS[key]
            col     = i % 3
            row     = i // 3
            bx      = sx + col * (bw + gap_x)
            by      = sy + row * (bh + gap_y)
            sel     = (i == self._team_sel)

            # Box background
            bg = (48, 34, 18) if sel else (20, 15, 10)
            pygame.draw.rect(self.screen, bg, (bx, by, bw, bh), border_radius=8)

            # Border
            bc     = td['primary'] if sel else tuple(c // 4 for c in td['primary'])
            bthick = 3 if sel else 1
            pygame.draw.rect(self.screen, bc, (bx, by, bw, bh), bthick, border_radius=8)

            # Glow when selected
            if sel:
                for gi in range(3, 0, -1):
                    gs = pygame.Surface((bw + gi * 6, bh + gi * 6), pygame.SRCALPHA)
                    pygame.draw.rect(gs, (*td['primary'], 28 * gi),
                                     (0, 0, bw + gi * 6, bh + gi * 6),
                                     border_radius=10 + gi)
                    self.screen.blit(gs, (bx - gi * 3, by - gi * 3))

            # Jersey circle preview
            jcx = bx + bw // 2
            jcy = by + 40
            pygame.draw.circle(self.screen, td['primary'],   (jcx, jcy), 26)
            pygame.draw.circle(self.screen, td['secondary'], (jcx, jcy), 26, 3)
            num_s = self.small_font.render(td['number'], True, td['secondary'])
            self.screen.blit(num_s, num_s.get_rect(center=(jcx, jcy)))

            # Team abbreviation
            abbr_s = self.font.render(td['abbr'], True, WHITE if sel else GRAY)
            self.screen.blit(abbr_s, abbr_s.get_rect(center=(jcx, by + 76)))

            # City name
            city_s = self.micro_font.render(td['city'], True, (160, 140, 110) if sel else (90, 80, 70))
            self.screen.blit(city_s, city_s.get_rect(center=(jcx, by + 94)))

            # Team type badge
            ctype   = td['char']
            tc_col  = (255, 170, 0) if ctype == 'tank' else (0, 200, 255)
            type_s  = self.micro_font.render('POWER' if ctype == 'tank' else 'SPEED', True, tc_col)
            self.screen.blit(type_s, type_s.get_rect(center=(jcx, by + 112)))

        hint = self.font.render('← → ↑ ↓ to browse  |  SPACE / ENTER to pick', True, GRAY)
        self.screen.blit(hint, hint.get_rect(center=(cx, SCREEN_HEIGHT - 28)))

    # ----------------------------------------------------------------- Other screens

    def _draw_overlay(self, title, color, subtitle):
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 175))
        self.screen.blit(surf, (0, 0))
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        t = self.big_font.render(title,    True, color)
        b = self.font.render(subtitle,     True, GRAY)
        self.screen.blit(t, t.get_rect(center=(cx, cy - 20)))
        self.screen.blit(b, b.get_rect(center=(cx, cy + 44)))

    def _draw_menu(self):
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        title  = self.title_font.render('BASKETBALL', True, GOLD_COLOR)
        title2 = self.title_font.render('BLITZ',      True, (255, 100, 50))
        self.screen.blit(title,  title.get_rect(center=(cx, cy - 155)))
        self.screen.blit(title2, title2.get_rect(center=(cx, cy - 70)))
        opts = ['Battle AI', 'Battle Online Friend']
        for i, opt in enumerate(opts):
            sel    = (i == self._menu_sel)
            color  = GOLD_COLOR if sel else GRAY
            prefix = '▶  ' if sel else '   '
            t = self.font.render(prefix + opt, True, color)
            self.screen.blit(t, t.get_rect(center=(cx, cy + 30 + i * 52)))
        if self._menu_banner:
            banner = self.small_font.render(self._menu_banner, True, (255, 150, 150))
            self.screen.blit(banner, banner.get_rect(center=(cx, cy + 120)))
        hint = self.small_font.render('Arrow keys to navigate  |  SPACE / ENTER to select', True, GRAY)
        self.screen.blit(hint, hint.get_rect(center=(cx, SCREEN_HEIGHT - 28)))

    def _draw_mp_menu(self):
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        t = self.big_font.render('ONLINE FRIEND', True, GOLD_COLOR)
        self.screen.blit(t, t.get_rect(center=(cx, cy - 100)))
        opts = ['Host a Game', 'Join a Game', 'Back']
        for i, opt in enumerate(opts):
            sel   = (i == self._menu_sel)
            color = GOLD_COLOR if sel else GRAY
            s     = self.font.render(('▶  ' if sel else '   ') + opt, True, color)
            self.screen.blit(s, s.get_rect(center=(cx, cy - 10 + i * 52)))

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
