import random

import pygame

from .config import SCREEN_H, SCREEN_W


class Camera:
    def __init__(self, width=SCREEN_W, height=SCREEN_H):
        self.size = pygame.Vector2(width, height)
        self.pos = pygame.Vector2()
        self.targets = []
        self.smoothing = 0.0
        self.bounds = None
        self._shake_strength = 0.0
        self._shake_duration = 0.0
        self._shake_time = 0.0
        self._shake_offset = pygame.Vector2()

    def fix(self, x=0, y=0):
        self.targets = []
        self.pos.update(x, y)

    def follow(self, *targets, smoothing=0.85, bounds=None):
        self.targets = list(targets)
        self.smoothing = smoothing
        self.bounds = bounds

    def shake(self, strength=8, duration=0.3):
        if self._shake_time > 0 and strength < self._current_shake():
            return
        self._shake_strength = strength
        self._shake_duration = duration
        self._shake_time = duration

    def update(self, dt):
        self._follow_targets(dt)
        self._update_shake(dt)

    @property
    def offset(self):
        return self.pos + self._shake_offset

    def to_screen(self, point):
        return pygame.Vector2(point) - self.offset

    def apply(self, rect):
        offset = self.offset
        return rect.move(-round(offset.x), -round(offset.y))

    def _follow_targets(self, dt):
        active = [t for t in self.targets if getattr(t, "active", True)]
        if not active:
            return
        center = sum((pygame.Vector2(t.pos) for t in active), pygame.Vector2()) / len(active)
        goal = center - self.size / 2
        blend = 1 - self.smoothing ** (dt * 60) if self.smoothing else 1
        self.pos += (goal - self.pos) * blend
        if self.bounds:
            width, height = self.bounds
            self.pos.x = max(0, min(width - self.size.x, self.pos.x))
            self.pos.y = max(0, min(height - self.size.y, self.pos.y))

    def _current_shake(self):
        if self._shake_duration <= 0:
            return 0.0
        return self._shake_strength * self._shake_time / self._shake_duration

    def _update_shake(self, dt):
        self._shake_time = max(0.0, self._shake_time - dt)
        amount = self._current_shake()
        self._shake_offset.update(random.uniform(-amount, amount), random.uniform(-amount, amount))
