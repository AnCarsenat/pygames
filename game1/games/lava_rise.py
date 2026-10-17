import math

import pygame

from engine import SCREEN_H, SCREEN_W, Body, MiniGame, PlatformerController, World, draw_body, draw_world

FLOOR_Y = SCREEN_H - 30
ROW_GAP = 80
TOP_LIMIT = 120
COLUMNS = 3
PLATFORM_H = 14
MIN_WIDTH = 30
BOTTOM_MAX_WIDTH = 100
TOP_MAX_WIDTH = 55
REACH_SAFETY = 0.7
PLAYER_SIZE = 28

GRACE_TIME = 2.0
LAVA_HEADROOM = 40
LAVA_COLOR = (255, 96, 40)
LAVA_GLOW = (255, 180, 80)


def jump_reach(controller, rise):
    v, g = controller.jump_speed, controller.gravity
    disc = v * v - 2 * g * rise
    if disc < 0:
        return 0.0
    airtime = (v + math.sqrt(disc)) / g
    return controller.speed * airtime


def horizontal_gap(a, b):
    return max(0, max(a.left, b.left) - min(a.right, b.right))


class LavaRise(MiniGame):
    name = "Lava Rise"
    instructions = "Climb above the rising lava! UP jumps, DOWN drops through platforms."
    time_limit = 20
    background = (34, 24, 36)

    def setup(self):
        self.controllers = {p: PlatformerController() for p in self.players}
        reference = PlatformerController()
        self.max_gap = jump_reach(reference, ROW_GAP) * REACH_SAFETY + PLAYER_SIZE

        self.world = World(SCREEN_W, SCREEN_H)
        self.world.add_solid((0, FLOOR_Y, SCREEN_W, SCREEN_H - FLOOR_Y))
        top_row = self._build_platforms()

        self.lava_start = FLOOR_Y + 10
        self.lava_end = top_row + LAVA_HEADROOM
        self.lava_y = self.lava_start

        xs = self.spread(len(self.players), 80, SCREEN_W - 80)
        half = PLAYER_SIZE / 2
        self.bodies = {p: Body(x, FLOOR_Y - half, PLAYER_SIZE) for p, x in zip(self.players, xs)}

    def _build_platforms(self):
        rows = list(range(FLOOR_Y - ROW_GAP, TOP_LIMIT - 1, -ROW_GAP))
        below = [pygame.Rect(0, FLOOR_Y, SCREEN_W, 1)]
        for index, y in enumerate(rows):
            height_ratio = index / max(1, len(rows) - 1)
            max_width = round(BOTTOM_MAX_WIDTH + (TOP_MAX_WIDTH - BOTTOM_MAX_WIDTH) * height_ratio)
            row = [self._place_platform(column, y, max_width, below) for column in range(COLUMNS)]
            for rect in row:
                self.world.add_solid(rect, one_way=True)
            below = row
        return rows[-1]

    def _place_platform(self, column, y, max_width, below):
        column_w = SCREEN_W / COLUMNS
        left_bound = column * column_w + 12
        width = self.rng.randint(MIN_WIDTH, max_width)
        right_bound = (column + 1) * column_w - 12 - width

        for _ in range(30):
            rect = pygame.Rect(round(self.rng.uniform(left_bound, right_bound)), y, width, PLATFORM_H)
            if self._reachable(rect, below):
                return rect

        anchor = min(below, key=lambda r: abs(r.centerx - (left_bound + right_bound + width) / 2))
        x = min(max(anchor.centerx - width // 2, left_bound), right_bound)
        return pygame.Rect(round(x), y, width, PLATFORM_H)

    def _reachable(self, rect, below):
        return any(horizontal_gap(rect, other) <= self.max_gap for other in below)

    def update(self, dt):
        rise_time = self.time_limit - GRACE_TIME
        progress = min(1.0, max(0.0, self.elapsed - GRACE_TIME) / rise_time)
        self.lava_y = self.lava_start + (self.lava_end - self.lava_start) * progress

        for player in self.alive:
            body = self.bodies[player]
            self.controllers[player].update(body, player.input, self.world, dt)
            if body.bottom > self.lava_y + 6:
                self.kill(player)

    def on_kill(self, player):
        self.bodies[player].active = False
        self.camera.shake(6, 0.25)

    def draw(self, surface):
        draw_world(surface, self.camera, self.world)
        for player in self.players:
            body = self.bodies[player]
            if body.active:
                draw_body(surface, self.camera, body, player.color)
        self._draw_lava(surface)

    def _draw_lava(self, surface):
        top = self.lava_y - self.camera.offset.y
        if top > SCREEN_H + 10:
            return
        wave = [
            (x, top + math.sin(x / 40 + self.elapsed * 4) * 5)
            for x in range(0, SCREEN_W + 20, 20)
        ]
        pygame.draw.polygon(surface, LAVA_COLOR, wave + [(SCREEN_W, SCREEN_H), (0, SCREEN_H)])
        pygame.draw.lines(surface, LAVA_GLOW, False, wave, 4)
