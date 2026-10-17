import math

import pygame

from engine import (
    GROUP_PLAYER, GROUP_WORLD, SCREEN_H, SCREEN_W, Body, MiniGame, TopDownController,
    World, collide_bodies, draw_body, draw_world,
)

ARENA_TOP = 40
PASS_COOLDOWN = 0.5
BOMB_COLOR = (20, 20, 24)
SPARK_COLORS = ((255, 230, 120), (255, 120, 40))
EXPLOSION_COLOR = (255, 150, 50)


class HotPotato(MiniGame):
    name = "Hot Potato"
    instructions = "Touch someone to pass the bomb. Don't hold it when it blows!"
    min_players = 2
    time_limit = None
    background = (36, 28, 24)

    def setup(self):
        self.world = World(SCREEN_W, SCREEN_H)
        self.world.add_border(thickness=16, top=ARENA_TOP)
        self.runner = TopDownController(speed=235)
        self.carrier = TopDownController(speed=265)

        center = pygame.Vector2(SCREEN_W / 2, SCREEN_H / 2 + 20)
        self.bodies = {}
        for i, player in enumerate(self.players):
            pos = center + pygame.Vector2(190, 0).rotate_rad(2 * math.pi * i / len(self.players))
            self.bodies[player] = Body(pos.x, pos.y, 28, mask=GROUP_WORLD | GROUP_PLAYER)

        self.holder = self.rng.choice(self.players)
        self.fuse_total = self.rng.uniform(8, 13)
        self.fuse = self.fuse_total
        self.pass_cooldown = 0.0
        self.explosion = None

    def update(self, dt):
        self.fuse -= dt
        self.pass_cooldown = max(0.0, self.pass_cooldown - dt)

        for player in self.alive:
            controller = self.carrier if player is self.holder else self.runner
            controller.update(self.bodies[player], player.input, self.world, dt)

        self._try_pass()
        collide_bodies([self.bodies[p] for p in self.alive], restitution=0.6)

        if self.fuse <= 0:
            self.explosion = pygame.Vector2(self.bodies[self.holder].pos)
            self.camera.shake(12, 0.4)
            self.kill(self.holder)
            self.finish()

    def _try_pass(self):
        if self.pass_cooldown > 0:
            return
        holder_body = self.bodies[self.holder]
        for player in self.alive:
            if player is not self.holder and holder_body.touches(self.bodies[player], margin=4):
                self.holder = player
                self.pass_cooldown = PASS_COOLDOWN
                return

    def on_kill(self, player):
        self.bodies[player].active = False

    def draw(self, surface):
        draw_world(surface, self.camera, self.world)
        for player in self.players:
            body = self.bodies[player]
            if body.active:
                draw_body(surface, self.camera, body, player.color)

        if self.explosion is not None:
            pygame.draw.circle(surface, EXPLOSION_COLOR, self.camera.to_screen(self.explosion), 70)
        else:
            self._draw_bomb(surface)

    def _draw_bomb(self, surface):
        body = self.bodies[self.holder]
        pos = self.camera.to_screen((body.pos.x, body.top - 14))
        urgency = 1 - max(0.0, self.fuse) / self.fuse_total
        pulse = 1 + 0.15 * math.sin(self.elapsed * (6 + 30 * urgency))
        pygame.draw.circle(surface, BOMB_COLOR, pos, 11 * pulse)
        spark = SPARK_COLORS[int(self.elapsed * 20) % 2]
        pygame.draw.circle(surface, spark, pos + pygame.Vector2(6, -10), 4)
