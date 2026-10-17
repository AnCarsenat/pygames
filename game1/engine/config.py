SCREEN_W = 960
SCREEN_H = 640
FPS = 60
DT = 1 / FPS

MAX_HP = 5
DEFAULT_ROUNDS = 10
INTRO_TIME = 2.5
RESULT_TIME = 2.5

BACKGROUND = (24, 26, 34)
TEXT = (235, 235, 240)
MUTED = (140, 145, 160)
ACCENT = (255, 210, 90)
DANGER = (255, 90, 90)

PLAYER_COLORS = [
    (235, 72, 72),
    (70, 140, 245),
    (80, 200, 110),
    (245, 200, 60),
    (180, 100, 230),
    (245, 140, 50),
    (60, 210, 210),
    (240, 110, 190),
]


def player_color(index):
    return PLAYER_COLORS[index % len(PLAYER_COLORS)]
