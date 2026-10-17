from dataclasses import dataclass

import pygame

from engine import SCREEN_H, SCREEN_W, Body, MiniGame, TopDownController, World, draw_body, draw_world

ARENA_TOP = 40
WARNING_COLOR = (220, 60, 60)
BLAST_COLOR = (255, 170, 60)
BLAST_TIME = 0.3


@dataclass
class Meteor:
    pos: pygame.Vector2
    radius: float
    fuse: float
    age: float = 0.0

    @property
    def progress(self):
        return min(1.0, self.age / self.fuse)


@dataclass
class Blast:
    pos: pygame.Vector2
    radius: float
    age: float = 0.0


class MeteorShower(MiniGame):
    name = "Meteor Shower"
    instructions = "Stay out of the red circles before the meteors land!"
    time_limit = 20
    background = (20, 24, 40)

    def setup(self):
        self.world = World(SCREEN_W, SCREEN_H)
        self.world.add_border(thickness=16, top=ARENA_TOP)
        self.controller = TopDownController(speed=260)

        xs = self.spread(len(self.players), 200, SCREEN_W - 200)
        self.bodies = {p: Body(x, SCREEN_H / 2, 26) for p, x in zip(self.players, xs)}
        self.meteors = []
        self.blasts = []
        self.spawn_timer = 0.6

    def update(self, dt):
        for player in self.alive:
            self.controller.update(self.bodies[player], player.input, self.world, dt)

        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self._spawn()
            progress = self.elapsed / self.time_limit
            self.spawn_timer = 0.55 - 0.35 * progress

        for meteor in list(self.meteors):
            meteor.age += dt
            if meteor.age >= meteor.fuse:
                self.meteors.remove(meteor)
                self._explode(meteor)

        for blast in self.blasts:
            blast.age += dt
        self.blasts = [b for b in self.blasts if b.age < BLAST_TIME]

    def _spawn(self):
        alive = self.alive
        if alive and self.rng.random() < 0.4:
            target = pygame.Vector2(self.bodies[self.rng.choice(alive)].pos)
        else:
            target = pygame.Vector2(
                self.rng.uniform(40, SCREEN_W - 40),
                self.rng.uniform(ARENA_TOP + 40, SCREEN_H - 40),
            )
        self.meteors.append(Meteor(target, self.rng.uniform(40, 70), self.rng.uniform(0.9, 1.3)))

    def _explode(self, meteor):
        self.blasts.append(Blast(meteor.pos, meteor.radius))
        self.camera.shake(5, 0.15)
        for player in self.alive:
            body = self.bodies[player]
            if body.pos.distance_to(meteor.pos) < meteor.radius + body.half * 0.5:
                self.kill(player)

    def on_kill(self, player):
        self.bodies[player].active = False

    def draw(self, surface):
        draw_world(surface, self.camera, self.world)
        for meteor in self.meteors:
            center = self.camera.to_screen(meteor.pos)
            pygame.draw.circle(surface, (90, 30, 40), center, meteor.radius * meteor.progress)
            pygame.draw.circle(surface, WARNING_COLOR, center, meteor.radius, 3)
        for player in self.players:
            body = self.bodies[player]
            if body.active:
                draw_body(surface, self.camera, body, player.color)
        for blast in self.blasts:
            fade = 1 - blast.age / BLAST_TIME
            center = self.camera.to_screen(blast.pos)
            pygame.draw.circle(surface, BLAST_COLOR, center, blast.radius * (0.6 + 0.4 * fade))
