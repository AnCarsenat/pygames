import pygame

from engine import SCREEN_H, SCREEN_W, MiniGame, dim, draw_text

REACTION_WINDOW = 1.5
SOLO_LIMIT = 0.45
GO_BACKGROUND = (30, 80, 44)
WAIT_COLOR = (255, 210, 90)
GO_COLOR = (140, 255, 160)


class QuickDraw(MiniGame):
    name = "Quick Draw"
    instructions = "Press ACTION as soon as you see GO! Too early or slowest loses."
    time_limit = None
    last_one_standing = False

    def setup(self):
        self.go_at = self.rng.uniform(1.5, 4.5)
        self.reactions = {}
        self.verdicts = {}

    @property
    def started(self):
        return self.elapsed >= self.go_at

    def update(self, dt):
        for player in self.alive:
            if player.input.pressed("action") and player not in self.reactions:
                if self.started:
                    self.reactions[player] = self.elapsed - self.go_at
                else:
                    self._lose(player, "TOO EARLY")

        if not self.alive:
            self.finish()
            return

        if self.started:
            waiting = [p for p in self.alive if p not in self.reactions]
            if not waiting or self.elapsed - self.go_at >= REACTION_WINDOW:
                self._judge()

    def _judge(self):
        for player in self.alive:
            if player not in self.reactions:
                self._lose(player, "TOO SLOW")

        shooters = self.alive
        if len(self.players) == 1:
            if shooters and self.reactions[shooters[0]] > SOLO_LIMIT:
                self._lose(shooters[0], "TOO SLOW")
        elif not self.dead and len(shooters) > 1:
            self._lose(max(shooters, key=self.reactions.get), "SLOWEST")
        self.finish()

    def _lose(self, player, verdict):
        self.verdicts[player] = verdict
        self.kill(player)

    def draw(self, surface):
        if self.started:
            surface.fill(GO_BACKGROUND)
            draw_text(surface, "GO!", 160, GO_COLOR, center=(SCREEN_W / 2, 200))
        else:
            draw_text(surface, "WAIT...", 120, WAIT_COLOR, center=(SCREEN_W / 2, 200))

        xs = self.spread(len(self.players), 160, SCREEN_W - 160)
        for player, x in zip(self.players, xs):
            self._draw_player(surface, player, x)

    def _draw_player(self, surface, player, x):
        rect = pygame.Rect(0, 0, 70, 110)
        rect.midbottom = (x, SCREEN_H - 150)
        color = player.color if self.is_alive(player) else dim(player.color)
        pygame.draw.rect(surface, color, rect, border_radius=14)
        draw_text(surface, player.name, 34, (255, 255, 255), center=rect.center)

        if player in self.verdicts:
            label = self.verdicts[player]
        elif player in self.reactions:
            label = f"{self.reactions[player] * 1000:.0f} ms"
        else:
            label = ""
        draw_text(surface, label, 32, (255, 255, 255), midtop=(x, rect.bottom + 16))
