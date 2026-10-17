import math

import pygame

from engine import (
    GROUP_PLAYER, GROUP_WORLD, SCREEN_H, SCREEN_W, Body, MiniGame, TopDownController,
    World, collide_bodies, draw_body,
)

RING_FILL = (58, 70, 58)
RING_EDGE = (220, 210, 170)
DASH_SPEED = 650
DASH_COOLDOWN = 0.9


class SumoRing(MiniGame):
    name = "Sumo Ring"
    instructions = "Push everyone out of the shrinking ring. ACTION dashes."
    min_players = 2
    time_limit = 30
    background = (26, 30, 26)

    def setup(self):
        self.world = World(SCREEN_W, SCREEN_H, contain_x=False)
        self.controller = TopDownController(speed=230, acceleration=1300, friction=700)
        self.center = pygame.Vector2(SCREEN_W / 2, SCREEN_H / 2 + 20)
        self.start_radius = 250
        self.end_radius = 110
        self.radius = self.start_radius

        self.bodies = {}
        self.facing = {}
        self.cooldown = {}
        for i, player in enumerate(self.players):
            angle = 2 * math.pi * i / len(self.players)
            pos = self.center + pygame.Vector2(140, 0).rotate_rad(angle)
            self.bodies[player] = Body(pos.x, pos.y, 34, mask=GROUP_WORLD | GROUP_PLAYER)
            self.facing[player] = (self.center - pos).normalize()
            self.cooldown[player] = 0.0

    def update(self, dt):
        progress = min(1.0, self.elapsed / self.time_limit)
        self.radius = self.start_radius + (self.end_radius - self.start_radius) * progress

        for player in self.alive:
            self._move(player, dt)

        collide_bodies([self.bodies[p] for p in self.alive], restitution=0.9)

        for player in self.alive:
            if self.bodies[player].pos.distance_to(self.center) > self.radius:
                self.kill(player)

    def _move(self, player, dt):
        body = self.bodies[player]
        direction = player.input.direction()
        if direction.length_squared():
            self.facing[player] = direction

        self.controller.update(body, player.input, self.world, dt)

        self.cooldown[player] = max(0.0, self.cooldown[player] - dt)
        if player.input.pressed("action") and self.cooldown[player] == 0:
            body.vel = self.facing[player] * DASH_SPEED
            self.cooldown[player] = DASH_COOLDOWN

    def on_kill(self, player):
        self.bodies[player].active = False
        self.camera.shake(8, 0.25)

    def draw(self, surface):
        center = self.camera.to_screen(self.center)
        pygame.draw.circle(surface, RING_FILL, center, self.radius)
        pygame.draw.circle(surface, RING_EDGE, center, self.radius, 4)
        for player in self.players:
            body = self.bodies[player]
            if not body.active:
                continue
            ready = self.cooldown[player] == 0
            draw_body(surface, self.camera, body, player.color, outline=RING_EDGE if ready else None)
