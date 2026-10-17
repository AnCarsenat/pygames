import math

import pygame

GROUP_PLAYER = 1
GROUP_WORLD = 2
GROUP_HAZARD = 4


def approach(value, target, max_delta):
    if value < target:
        return min(value + max_delta, target)
    return max(value - max_delta, target)


def approach_vector(vector, target, max_delta):
    delta = target - vector
    distance = delta.length()
    if distance <= max_delta:
        return pygame.Vector2(target)
    return vector + delta * (max_delta / distance)


class Collider:
    def __init__(self, rect, group=GROUP_WORLD, mask=GROUP_PLAYER, one_way=False):
        self.rect = pygame.Rect(rect)
        self.group = group
        self.mask = mask
        self.one_way = one_way

    def accepts(self, body):
        return bool(self.mask & body.group and body.mask & self.group)


class Slope:
    def __init__(self, x1, y1, x2, y2, max_angle=45):
        self.a = (x1, y1)
        self.b = (x2, y2)
        angle = math.degrees(math.atan2(abs(y2 - y1), abs(x2 - x1)))
        self.walkable = angle <= max_angle

    def height_at(self, x):
        (x1, y1), (x2, y2) = self.a, self.b
        if not min(x1, x2) <= x <= max(x1, x2):
            return None
        if x1 == x2:
            return min(y1, y2)
        return y1 + (x - x1) / (x2 - x1) * (y2 - y1)


class Body:
    def __init__(self, x, y, size, group=GROUP_PLAYER, mask=GROUP_WORLD):
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2()
        self.size = size
        self.group = group
        self.mask = mask
        self.grounded = False
        self.drop_through = 0.0
        self.active = True

    @property
    def half(self):
        return self.size / 2

    @property
    def left(self):
        return self.pos.x - self.half

    @property
    def right(self):
        return self.pos.x + self.half

    @property
    def top(self):
        return self.pos.y - self.half

    @property
    def bottom(self):
        return self.pos.y + self.half

    @property
    def rect(self):
        return pygame.Rect(round(self.left), round(self.top), self.size, self.size)

    def overlaps_rect(self, rect):
        return (
            self.left < rect.right and self.right > rect.left
            and self.top < rect.bottom and self.bottom > rect.top
        )

    def touches(self, other, margin=0.0):
        return self.pos.distance_to(other.pos) < self.half + other.half + margin


class World:
    def __init__(self, width, height, contain_x=True, contain_y=False):
        self.width = width
        self.height = height
        self.contain_x = contain_x
        self.contain_y = contain_y
        self.solids = []
        self.slopes = []

    def add_solid(self, rect, one_way=False, group=GROUP_WORLD, mask=GROUP_PLAYER):
        collider = Collider(rect, group, mask, one_way)
        self.solids.append(collider)
        return collider

    def add_border(self, thickness=16, top=0):
        w, h, t = self.width, self.height, thickness
        for rect in (
            (0, top, w, t),
            (0, h - t, w, t),
            (0, top, t, h - top),
            (w - t, top, t, h - top),
        ):
            self.add_solid(rect)

    def add_slope(self, x1, y1, x2, y2, max_angle=45):
        slope = Slope(x1, y1, x2, y2, max_angle)
        self.slopes.append(slope)
        return slope

    def is_below(self, body, margin=0):
        return body.top > self.height + margin

    def move(self, body, dt):
        was_grounded = body.grounded
        body.grounded = False

        dx = body.vel.x * dt
        self._move_x(body, dx)

        old_bottom = body.bottom
        self._move_y(body, body.vel.y * dt)

        if body.vel.y >= 0 and body.drop_through <= 0:
            self._land_on_slopes(body, old_bottom, abs(dx), was_grounded)

        self._contain(body)

    def _overlapping(self, body):
        for collider in self.solids:
            if collider.accepts(body) and body.overlaps_rect(collider.rect):
                yield collider

    def _move_x(self, body, dx):
        if not dx:
            return
        body.pos.x += dx
        for collider in self._overlapping(body):
            if collider.one_way:
                continue
            if dx > 0:
                body.pos.x = collider.rect.left - body.half
            else:
                body.pos.x = collider.rect.right + body.half
            body.vel.x = 0

    def _move_y(self, body, dy):
        if not dy:
            return
        old_bottom = body.bottom
        body.pos.y += dy
        for collider in self._overlapping(body):
            if collider.one_way and not self._lands_on(body, collider, dy, old_bottom):
                continue
            if dy > 0:
                body.pos.y = collider.rect.top - body.half
                body.grounded = True
            else:
                body.pos.y = collider.rect.bottom + body.half
            body.vel.y = 0

    @staticmethod
    def _lands_on(body, collider, dy, old_bottom):
        return dy > 0 and body.drop_through <= 0 and old_bottom <= collider.rect.top + 0.5

    def _land_on_slopes(self, body, old_bottom, step, was_grounded):
        reach = step + 2
        for slope in self.slopes:
            if not slope.walkable:
                continue
            surface = slope.height_at(body.pos.x)
            if surface is None:
                continue
            crossed = old_bottom <= surface + reach and body.bottom >= surface
            stuck = was_grounded and 0 <= surface - body.bottom <= reach
            if crossed or stuck:
                body.pos.y = surface - body.half
                body.vel.y = 0
                body.grounded = True
                return

    def _contain(self, body):
        if self.contain_x:
            if body.left < 0:
                body.pos.x = body.half
                body.vel.x = max(body.vel.x, 0)
            elif body.right > self.width:
                body.pos.x = self.width - body.half
                body.vel.x = min(body.vel.x, 0)
        if self.contain_y:
            if body.top < 0:
                body.pos.y = body.half
                body.vel.y = max(body.vel.y, 0)
            elif body.bottom > self.height:
                body.pos.y = self.height - body.half
                body.vel.y = min(body.vel.y, 0)


def collide_bodies(bodies, restitution=1.0):
    active = [b for b in bodies if b.active]
    for i, a in enumerate(active):
        for b in active[i + 1:]:
            if not (a.mask & b.group and b.mask & a.group):
                continue
            offset = b.pos - a.pos
            distance = offset.length()
            min_distance = a.half + b.half
            if distance >= min_distance:
                continue

            normal = offset / distance if distance else pygame.Vector2(1, 0)
            push = normal * (min_distance - distance) / 2
            a.pos -= push
            b.pos += push

            closing = (b.vel - a.vel).dot(normal)
            if closing < 0:
                impulse = normal * (-(1 + restitution) * closing / 2)
                a.vel -= impulse
                b.vel += impulse
