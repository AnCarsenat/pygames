from .physics import approach, approach_vector


class TopDownController:
    def __init__(self, speed=240, acceleration=2400, friction=2000):
        self.speed = speed
        self.acceleration = acceleration
        self.friction = friction

    def update(self, body, controls, world, dt):
        target = controls.direction() * self.speed
        rate = self.acceleration if target.length_squared() else self.friction
        body.vel = approach_vector(body.vel, target, rate * dt)
        world.move(body, dt)


class PlatformerController:
    def __init__(
        self,
        speed=250,
        acceleration=2600,
        air_control=0.6,
        jump_speed=560,
        gravity=1600,
        max_fall=950,
        coyote_time=0.1,
        jump_buffer=0.12,
        jump_cut=0.45,
        drop_time=0.25,
        jump_action="up",
    ):
        self.speed = speed
        self.acceleration = acceleration
        self.air_control = air_control
        self.jump_speed = jump_speed
        self.gravity = gravity
        self.max_fall = max_fall
        self.coyote_time = coyote_time
        self.jump_buffer = jump_buffer
        self.jump_cut = jump_cut
        self.drop_time = drop_time
        self.jump_action = jump_action
        self._coyote = 0.0
        self._buffer = 0.0

    def update(self, body, controls, world, dt):
        self._run(body, controls, dt)
        self._jump(body, controls, dt)
        body.vel.y = min(body.vel.y + self.gravity * dt, self.max_fall)
        world.move(body, dt)

    def _run(self, body, controls, dt):
        control = 1 if body.grounded else self.air_control
        target = controls.axis_x * self.speed
        body.vel.x = approach(body.vel.x, target, self.acceleration * control * dt)

    def _jump(self, body, controls, dt):
        self._coyote = self.coyote_time if body.grounded else max(0.0, self._coyote - dt)
        if controls.pressed(self.jump_action):
            self._buffer = self.jump_buffer
        else:
            self._buffer = max(0.0, self._buffer - dt)

        body.drop_through = max(0.0, body.drop_through - dt)
        if controls.pressed("down") and body.grounded:
            body.drop_through = self.drop_time

        if self._buffer > 0 and self._coyote > 0:
            body.vel.y = -self.jump_speed
            self._buffer = self._coyote = 0.0

        if controls.released(self.jump_action) and body.vel.y < 0:
            body.vel.y *= self.jump_cut
