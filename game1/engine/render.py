from functools import lru_cache

import pygame

from .config import MAX_HP, SCREEN_H, SCREEN_W, TEXT

SOLID_COLOR = (90, 96, 112)
PLATFORM_COLOR = (160, 168, 188)
SLOPE_COLOR = (90, 170, 230)
STEEP_COLOR = (220, 90, 90)
HEART_COLOR = (235, 70, 90)
HEART_EMPTY = (70, 60, 72)
HUD_HEIGHT = 36


@lru_cache(maxsize=None)
def font(size):
    return pygame.font.Font(None, size)


def dim(color, factor=0.35):
    return tuple(int(c * factor) for c in color)


def draw_text(surface, text, size, color=TEXT, **anchor):
    image = font(size).render(str(text), True, color)
    rect = image.get_rect(**anchor)
    surface.blit(image, rect)
    return rect


def draw_text_block(surface, text, size, color, center_x, top, max_width, line_gap=4):
    lines, current = [], ""
    for word in text.split():
        trial = f"{current} {word}".strip()
        if not current or font(size).size(trial)[0] <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)

    y = top
    for line in lines:
        y = draw_text(surface, line, size, color, midtop=(center_x, y)).bottom + line_gap
    return y


def draw_overlay(surface, alpha=170):
    shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    shade.fill((0, 0, 0, alpha))
    surface.blit(shade, (0, 0))


def draw_world(surface, camera, world):
    for collider in world.solids:
        rect = camera.apply(collider.rect)
        if collider.one_way:
            pygame.draw.rect(surface, PLATFORM_COLOR, rect, border_radius=4)
        else:
            pygame.draw.rect(surface, SOLID_COLOR, rect)
    for slope in world.slopes:
        color = SLOPE_COLOR if slope.walkable else STEEP_COLOR
        pygame.draw.line(surface, color, camera.to_screen(slope.a), camera.to_screen(slope.b), 4)


def draw_body(surface, camera, body, color, outline=None):
    rect = camera.apply(body.rect)
    radius = max(2, body.size // 5)
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    if outline:
        pygame.draw.rect(surface, outline, rect.inflate(6, 6), 3, border_radius=radius + 2)

    look = pygame.Vector2(body.vel.x, body.vel.y)
    if look.length_squared() > 1:
        look.scale_to_length(body.size * 0.12)
    eye_y = rect.top + rect.height * 0.38 + look.y
    for side in (-1, 1):
        eye = (rect.centerx + side * rect.width * 0.2 + look.x, eye_y)
        pygame.draw.circle(surface, (255, 255, 255), eye, max(2, body.size * 0.12))


def draw_heart(surface, center, size, color):
    x, y = center
    r = size / 4
    pygame.draw.circle(surface, color, (x - r, y - r / 2), r)
    pygame.draw.circle(surface, color, (x + r, y - r / 2), r)
    pygame.draw.polygon(surface, color, [(x - 2 * r, y - r / 4), (x + 2 * r, y - r / 4), (x, y + 1.75 * r)])


def draw_hearts(surface, hp, left, center_y, size, spacing, lost=0):
    for i in range(MAX_HP):
        if i < hp:
            color = HEART_COLOR
        elif i < hp + lost:
            color = TEXT
        else:
            color = HEART_EMPTY
        draw_heart(surface, (left + size / 2 + i * spacing, center_y), size, color)


def draw_hud(surface, players, faded=(), time_left=None, time_limit=None):
    bar = pygame.Surface((SCREEN_W, HUD_HEIGHT), pygame.SRCALPHA)
    bar.fill((0, 0, 0, 140))
    surface.blit(bar, (0, 0))

    slot_w = min(150, (SCREEN_W - 12) / max(1, len(players)))
    spacing = min(15, (slot_w - 62) / MAX_HP)
    x = 12
    for player in players:
        out = player.eliminated or player in faded
        color = dim(player.color) if out else player.color
        pygame.draw.rect(surface, color, (x, 9, 18, 18), border_radius=4)
        draw_text(surface, player.name, 22, dim(TEXT, 0.6) if out else TEXT, midleft=(x + 24, 18))
        draw_hearts(surface, player.hp, x + 52, 19, spacing * 0.8, spacing)
        x += slot_w

    if time_left is not None and time_limit:
        width = SCREEN_W * time_left / time_limit
        pygame.draw.rect(surface, TEXT, (0, HUD_HEIGHT - 3, width, 3))


def draw_roster(surface, players, center_x, top, lost=(), blink_on=True, bottom=SCREEN_H - 80):
    row_h = min(56, (bottom - top) / max(1, len(players)))
    box = min(36, row_h - 8)
    for i, player in enumerate(players):
        middle = top + i * row_h + box / 2
        color = dim(player.color) if player.eliminated else player.color
        pygame.draw.rect(surface, color, (center_x - 220, middle - box / 2, box, box), border_radius=8)
        draw_text(surface, player.name, 34, TEXT, midleft=(center_x - 170, middle))
        flash = 1 if player in lost and blink_on else 0
        draw_hearts(surface, player.hp, center_x - 100, middle + 2, min(24, box * 0.7), 30, lost=flash)
        if player.eliminated:
            draw_text(surface, "OUT", 30, HEART_COLOR, midleft=(center_x + 70, middle))
        elif player in lost:
            draw_text(surface, "-1", 30, HEART_COLOR, midleft=(center_x + 70, middle))
