from .camera import Camera
from .config import BACKGROUND


class MiniGame:
    name = "Mini-game"
    instructions = ""
    min_players = 1
    max_players = None
    time_limit = 20.0
    last_one_standing = True
    background = BACKGROUND

    def __init__(self, players, rng):
        self.players = list(players)
        self.rng = rng
        self.camera = Camera()
        self.elapsed = 0.0
        self.dead = []
        self.finished = False
        self.setup()

    @classmethod
    def supports(cls, player_count):
        if player_count < cls.min_players:
            return False
        return cls.max_players is None or player_count <= cls.max_players

    @property
    def alive(self):
        return [p for p in self.players if p not in self.dead]

    @property
    def time_left(self):
        if self.time_limit is None:
            return None
        return max(0.0, self.time_limit - self.elapsed)

    def is_alive(self, player):
        return player not in self.dead

    def kill(self, player):
        if player in self.players and player not in self.dead:
            self.dead.append(player)
            self.on_kill(player)

    def finish(self):
        self.finished = True

    def step(self, dt):
        if self.finished:
            return
        self.elapsed += dt
        self.update(dt)
        self.camera.update(dt)

        if not self.finished and self.time_limit is not None and self.elapsed >= self.time_limit:
            self.on_timeout()
            self.finish()

        survivors_needed = 1 if len(self.players) > 1 else 0
        if self.last_one_standing and len(self.alive) <= survivors_needed:
            self.finish()

    @staticmethod
    def spread(count, start, end):
        if count == 1:
            return [(start + end) / 2]
        step = (end - start) / (count - 1)
        return [start + i * step for i in range(count)]

    def setup(self):
        pass

    def update(self, dt):
        pass

    def draw(self, surface):
        pass

    def on_kill(self, player):
        pass

    def on_timeout(self):
        pass
