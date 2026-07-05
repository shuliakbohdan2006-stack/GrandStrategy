from __future__ import annotations

from typing import List, Optional, Tuple

import pygame

from core.game_state import GameState
from map.render import country_at_screen_pos as real_country_at_screen_pos
from ui.layout import MAP_RECT, VIRTUAL_MAP_HEIGHT, VIRTUAL_MAP_WIDTH


def virtual_to_screen(x: int, y: int) -> Tuple[int, int]:
    sx = MAP_RECT.width / VIRTUAL_MAP_WIDTH
    sy = MAP_RECT.height / VIRTUAL_MAP_HEIGHT
    return MAP_RECT.x + int(x * sx), MAP_RECT.y + int(y * sy)


def screen_to_virtual(x: int, y: int) -> Tuple[int, int]:
    sx = MAP_RECT.width / VIRTUAL_MAP_WIDTH
    sy = MAP_RECT.height / VIRTUAL_MAP_HEIGHT
    return int((x - MAP_RECT.x) / sx), int((y - MAP_RECT.y) / sy)


def draw_flag(
    surface: pygame.Surface,
    rect: pygame.Rect,
    colors: List[Tuple[int, int, int]],
    image: Optional[pygame.Surface] = None,
) -> None:
    if image is not None:
        flag = image if image.get_size() == rect.size else pygame.transform.smoothscale(image, rect.size)
        surface.blit(flag, rect)
        pygame.draw.rect(surface, (15, 21, 26), rect, width=1)
        return
    stripe_colors = colors or [(230, 230, 230), (90, 120, 160), (35, 40, 48)]
    stripe_w = max(1, rect.width // len(stripe_colors))
    for index, color in enumerate(stripe_colors):
        stripe = pygame.Rect(rect.x + index * stripe_w, rect.y, stripe_w + 1, rect.height)
        pygame.draw.rect(surface, color, stripe)
    pygame.draw.rect(surface, (15, 21, 26), rect, width=1)


def draw_panel(surface: pygame.Surface, rect: pygame.Rect, color: Tuple[int, int, int]) -> None:
    shadow = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 55), shadow.get_rect(), border_radius=9)
    surface.blit(shadow, (rect.x + 4, rect.y + 5))
    pygame.draw.rect(surface, color, rect, border_radius=9)
    pygame.draw.rect(surface, (49, 64, 78), rect, width=1, border_radius=9)


def draw_text(surface: pygame.Surface, text: str, pos: Tuple[int, int], font: pygame.font.Font, color: Tuple[int, int, int]) -> None:
    rendered = font.render(text, True, color)
    surface.blit(rendered, pos)


def draw_fitted_text(
    surface: pygame.Surface,
    text: str,
    rect: pygame.Rect,
    font: pygame.font.Font,
    color: Tuple[int, int, int],
    align: str = "center",
) -> None:
    max_width = max(10, rect.width - 10)
    shown = text
    while font.size(shown)[0] > max_width and len(shown) > 4:
        shown = shown[:-4] + "..."
    rendered = font.render(shown, True, color)
    if align == "left":
        x = rect.x + 5
    else:
        x = rect.centerx - rendered.get_width() // 2
    y = rect.centery - rendered.get_height() // 2
    surface.blit(rendered, (x, y))


def draw_wrapped_text(surface: pygame.Surface, text: str, rect: pygame.Rect, font: pygame.font.Font, color: Tuple[int, int, int]) -> None:
    words = text.split()
    line = ""
    y = rect.y
    for word in words:
        test = f"{line} {word}".strip()
        if font.size(test)[0] <= rect.width:
            line = test
        else:
            draw_text(surface, line, (rect.x, y), font, color)
            y += font.get_linesize()
            line = word
            if y > rect.bottom - font.get_linesize():
                break
    if line and y <= rect.bottom - font.get_linesize() + 3:
        draw_text(surface, line, (rect.x, y), font, color)


def country_at_screen_pos(state: GameState, pos: Tuple[int, int]):
    return real_country_at_screen_pos(state, pos, MAP_RECT)


