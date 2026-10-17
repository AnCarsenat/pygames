import math
import random
import sys
import traceback

import pygame

from .config import (
    ACCENT, BACKGROUND, DEFAULT_ROUNDS, DT, FPS, INTRO_TIME, MAX_HP, MUTED,
    RESULT_TIME, SCREEN_H, SCREEN_W, TEXT, player_color,
)
from .input import InputManager
from .player import Player
from .render import dim, draw_hud, draw_overlay, draw_roster, draw_text, draw_text_block

CENTER_X = SCREEN_W / 2
CONFIRM_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER)
IGNORED_EVENTS = (pygame.MOUSEMOTION, pygame.TEXTINPUT, pygame.TEXTEDITING)


def is_confirm(event):
    return event.type == pygame.KEYDOWN and event.key in CONFIRM_KEYS


def is_escape(event):
    return event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE


class Match:
    def __init__(self, players, game_types, rounds, rng):
        self.players = players
        self.game_types = list(game_types)
        self.rounds = rounds
        self.rng = rng
        self.round = 0
        self._last_game = None

    @property
    def alive(self):
        return [p for p in self.players if not p.eliminated]

    @property
    def is_solo(self):
        return len(self.players) == 1

    @property
    def over(self):
        survivors_needed = 0 if self.is_solo else 1
        return self.round >= self.rounds or len(self.alive) <= survivors_needed

    def next_game(self):
        while self.game_types:
            game_type = self._pick_game_type()
            try:
                game = game_type(self.alive, self.rng)
            except Exception:
                print(f"Removing {game_type.name}, setup failed:", file=sys.stderr)
                traceback.print_exc()
                self.game_types.remove(game_type)
                continue
            self._last_game = game_type
            self.round += 1
            return game
        raise RuntimeError("No playable mini-games left")

    def _pick_game_type(self):
        count = len(self.alive)
        candidates = [g for g in self.game_types if g.supports(count)] or list(self.game_types)
        if len(candidates) > 1 and self._last_game in candidates:
            candidates.remove(self._last_game)
        return self.rng.choice(candidates)

    def apply_losses(self, game):
        for player in game.dead:
            player.lose_hp()
        return list(game.dead)

    def winners(self):
        alive = self.alive
        if not alive:
            return []
        best = max(p.hp for p in alive)
        return [p for p in alive if p.hp == best]


class Scene:
    def __init__(self, app):
        self.app = app

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, surface):
        pass


class LobbyScene(Scene):
    LIST_TOP = 180
    LIST_BOTTOM = SCREEN_H - 90

    def __init__(self, app, joined=()):
        super().__init__(app)
        self.joined = [c for c in joined if c.connected]

    def handle_event(self, event):
        if is_confirm(event):
            self._start()
        elif is_escape(event):
            self.app.quit()

    def update(self, dt):
        inputs = self.app.inputs
        for controls in inputs.devices:
            if controls.pressed("action"):
                self._toggle(controls)
        self.joined = [c for c in self.joined if c.connected]
        if inputs.any_pressed("start"):
            self._start()

    def _toggle(self, controls):
        if controls in self.joined:
            self.joined.remove(controls)
        else:
            self.joined.append(controls)

    def _start(self):
        if self.joined:
            order = self.app.inputs.devices
            self.app.start_match(sorted(self.joined, key=order.index))

    def draw(self, surface):
        surface.fill(BACKGROUND)
        draw_text(surface, "PARTY", 80, ACCENT, center=(CENTER_X, 70))
        info = f"{len(self.app.game_types)} mini-games  ·  {self.app.rounds} rounds  ·  {MAX_HP} hearts each"
        draw_text(surface, info, 26, MUTED, center=(CENTER_X, 122))
        draw_text(surface, "Test your keys: the arrows light up while held", 22, MUTED, center=(CENTER_X, 150))

        devices = self.app.inputs.devices
        row_h = min(64, (self.LIST_BOTTOM - self.LIST_TOP) / len(devices))
        for i, controls in enumerate(devices):
            self._draw_device(surface, controls, self.LIST_TOP + i * row_h, row_h)

        if self.joined:
            hint = f"{len(self.joined)} ready   ·   ENTER / START to begin   ·   ESC to quit"
        else:
            hint = "Press your ACTION key or A to join"
        draw_text(surface, hint, 30, TEXT, center=(CENTER_X, SCREEN_H - 45))

    def _draw_device(self, surface, controls, top, row_h):
        joined = controls in self.joined
        color = player_color(controls.color_index)
        shown = color if joined else dim(color)
        text_color = TEXT if joined else MUTED
        box = max(16, int(row_h) - 20)
        middle = top + row_h / 2

        pygame.draw.rect(surface, shown, (90, middle - box / 2, box, box), border_radius=box // 4)
        draw_text(surface, controls.name, 30, text_color, midleft=(90 + box + 14, middle))
        draw_text(surface, controls.describe(), 24, text_color, midleft=(300, middle))
        self._draw_key_tester(surface, controls, SCREEN_W - 270, middle, color)

        status = "READY" if joined else f"press {controls.join_hint}"
        draw_text(surface, status, 28, shown if joined else MUTED, midright=(SCREEN_W - 90, middle))

    @staticmethod
    def _draw_key_tester(surface, controls, x, y, color):
        off = (60, 62, 72)
        cell = 9
        for action, (dx, dy) in (("up", (0, -1)), ("down", (0, 1)), ("left", (-1, 0)), ("right", (1, 0))):
            rect = pygame.Rect(0, 0, cell, cell)
            rect.center = (x + dx * (cell + 2), y + dy * (cell + 2))
            pygame.draw.rect(surface, color if controls.held(action) else off, rect, border_radius=2)
        pygame.draw.circle(surface, color if controls.held("action") else off, (x + 34, y), 7)


class IntroScene(Scene):
    def __init__(self, app, game):
        super().__init__(app)
        self.game = game
        self.timer = INTRO_TIME

    def handle_event(self, event):
        if is_escape(event):
            self.app.back_to_lobby()

    def update(self, dt):
        self.timer -= dt
        if self.timer <= 0:
            self.app.change(PlayScene(self.app, self.game))

    def draw(self, surface):
        surface.fill(self.game.background)
        self.game.draw(surface)
        draw_overlay(surface)

        match = self.app.match
        draw_text(surface, f"Round {match.round} / {match.rounds}", 30, MUTED, center=(CENTER_X, 170))
        draw_text(surface, self.game.name, 80, TEXT, center=(CENTER_X, 240))
        draw_text_block(surface, self.game.instructions, 32, TEXT, CENTER_X, 300, SCREEN_W - 200)
        draw_text(surface, math.ceil(self.timer), 72, ACCENT, center=(CENTER_X, 460))
        draw_hud(surface, match.players)


class PlayScene(Scene):
    END_DELAY = 0.9

    def __init__(self, app, game):
        super().__init__(app)
        self.game = game
        self.end_timer = None

    def handle_event(self, event):
        if is_escape(event):
            self.app.back_to_lobby()

    def update(self, dt):
        if self.end_timer is None:
            self.game.step(dt)
            if self.game.finished:
                self.end_timer = self.END_DELAY
            return

        self.game.camera.update(dt)
        self.end_timer -= dt
        if self.end_timer <= 0:
            self.app.change(ResultScene(self.app, self.game))

    def draw(self, surface):
        surface.fill(self.game.background)
        self.game.draw(surface)
        draw_hud(
            surface,
            self.app.match.players,
            faded=self.game.dead,
            time_left=self.game.time_left,
            time_limit=self.game.time_limit,
        )


class ResultScene(Scene):
    def __init__(self, app, game):
        super().__init__(app)
        self.game = game
        self.losers = app.match.apply_losses(game)
        self.timer = RESULT_TIME

    def handle_event(self, event):
        if is_confirm(event):
            self.timer = 0

    def update(self, dt):
        if self.app.inputs.any_pressed("start"):
            self.timer = 0
        self.timer -= dt
        if self.timer <= 0:
            self.app.advance()

    def draw(self, surface):
        surface.fill(self.game.background)
        self.game.draw(surface)
        draw_overlay(surface, 200)
        title = "Ouch!" if self.losers else "Everyone survived!"
        draw_text(surface, title, 72, TEXT, center=(CENTER_X, 120))
        blink_on = int(self.timer * 6) % 2 == 0
        draw_roster(surface, self.app.match.players, CENTER_X, 190, self.losers, blink_on)


class GameOverScene(Scene):
    def handle_event(self, event):
        if is_confirm(event):
            self.app.back_to_lobby()
        elif is_escape(event):
            self.app.quit()

    def update(self, dt):
        if self.app.inputs.any_pressed("start"):
            self.app.back_to_lobby()

    def draw(self, surface):
        surface.fill(BACKGROUND)
        match = self.app.match
        title, subtitle = self._headline(match)
        draw_text(surface, title, 80, ACCENT, center=(CENTER_X, 100))
        draw_text(surface, subtitle, 30, MUTED, center=(CENTER_X, 155))
        draw_roster(surface, match.players, CENTER_X, 200)
        draw_text(surface, "ENTER / START: play again   ·   ESC: quit", 30, TEXT, center=(CENTER_X, SCREEN_H - 45))

    @staticmethod
    def _headline(match):
        winners = match.winners()
        rounds = f"{match.round} round{'s' if match.round != 1 else ''} played"
        if match.is_solo:
            return ("You made it!" if winners else "Game over"), rounds
        if not winners:
            return "Nobody survived!", rounds
        if len(winners) == 1:
            return f"{winners[0].name} wins!", rounds
        return "Draw: " + ", ".join(p.name for p in winners), rounds


class App:
    def __init__(self, game_types, rounds=DEFAULT_ROUNDS, layout="azerty", seed=None):
        pygame.init()
        pygame.display.set_caption("Party")
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.key.stop_text_input()
        pygame.event.set_blocked(IGNORED_EVENTS)

        self.clock = pygame.time.Clock()
        self.game_types = list(game_types)
        self.rounds = rounds
        self.rng = random.Random(seed)
        self.inputs = InputManager(layout)
        self.match = None
        self.scene = LobbyScene(self)
        self.running = True

    def change(self, scene):
        self.scene = scene

    def quit(self):
        self.running = False

    def start_match(self, devices):
        players = [
            Player(number, player_color(controls.color_index), controls)
            for number, controls in enumerate(devices, start=1)
        ]
        self.match = Match(players, self.game_types, self.rounds, self.rng)
        self.advance()

    def advance(self):
        if self.match.over:
            self.change(GameOverScene(self))
        else:
            self.change(IntroScene(self, self.match.next_game()))

    def back_to_lobby(self):
        joined = [p.input for p in self.match.players] if self.match else []
        self.match = None
        self.change(LobbyScene(self, joined))

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.quit()
        self.inputs.handle_event(event)
        self.scene.handle_event(event)

    def tick(self):
        self.inputs.update()
        self.scene.update(DT)

    def draw(self):
        self.scene.draw(self.screen)
        pygame.display.flip()

    def run(self):
        accumulator = 0.0
        while self.running:
            accumulator += min(self.clock.tick(FPS) / 1000, 0.1)
            for event in pygame.event.get():
                self.handle_event(event)
            while accumulator >= DT and self.running:
                self.tick()
                accumulator -= DT
            self.draw()
        pygame.quit()
