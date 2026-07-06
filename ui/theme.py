from __future__ import annotations

from typing import Tuple

import pygame


BG = (18, 23, 30)
PANEL = (29, 38, 48)
PANEL_SOFT = (35, 47, 59)
PANEL_DARK = (20, 27, 34)
TEXT = (235, 240, 245)
MUTED = (160, 174, 187)
ACCENT = (222, 174, 72)
ACCENT_BLUE = (77, 128, 178)
GOOD = (94, 190, 127)
BAD = (226, 92, 88)

CATEGORY_COLORS = {
    "War": (226, 92, 88),
    "Economy": (92, 168, 116),
    "Politics": (188, 138, 216),
    "Family": (218, 148, 180),
    "Technology": (87, 158, 214),
    "Diplomacy": (222, 174, 72),
    "Science": (92, 172, 210),
    "Society": (126, 196, 150),
    "Disaster": (218, 128, 68),
    "Epidemic": (106, 190, 164),
    "Terrorism": (214, 78, 82),
    "Corruption": (190, 126, 80),
    "Sport": (102, 180, 118),
    "Culture": (210, 132, 196),
    "Migration": (128, 166, 220),
    "Energy": (230, 190, 76),
}

_SHADOW_CACHE: dict[Tuple[int, int, int], pygame.Surface] = {}


def blend(a: Tuple[int, int, int], b: Tuple[int, int, int], amount: float) -> Tuple[int, int, int]:
    return tuple(int(a[i] + (b[i] - a[i]) * amount) for i in range(3))


def draw_soft_panel(surface: pygame.Surface, rect: pygame.Rect, color=PANEL, radius: int = 10, border=(48, 62, 75)) -> None:
    shadow = pygame.Rect(rect.x + 4, rect.y + 5, rect.width, rect.height)
    cache_key = (shadow.width, shadow.height, radius)
    shadow_surface = _SHADOW_CACHE.get(cache_key)
    if shadow_surface is None:
        shadow_surface = pygame.Surface((shadow.width, shadow.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, (0, 0, 0, 60), shadow_surface.get_rect(), border_radius=radius)
        _SHADOW_CACHE[cache_key] = shadow_surface
    surface.blit(shadow_surface, shadow.topleft)
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    pygame.draw.rect(surface, border, rect, width=1, border_radius=radius)


def category_for(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ["war", "front", "peace", "army", "battle"]):
        return "War"
    if any(word in lowered for word in ["economy", "trade", "debt", "money", "resource", "inflation"]):
        return "Economy"
    if any(word in lowered for word in ["election", "law", "party", "crisis", "protest"]):
        return "Politics"
    if any(word in lowered for word in ["family", "spouse", "heir", "lover", "divorce"]):
        return "Family"
    if any(word in lowered for word in ["technology", "research", "breakthrough"]):
        return "Technology"
    if any(word in lowered for word in ["science", "laboratory", "university", "patent"]):
        return "Science"
    if any(word in lowered for word in ["society", "housing", "labor", "public health"]):
        return "Society"
    if any(word in lowered for word in ["disaster", "flood", "earthquake", "wildfire", "drought", "storm"]):
        return "Disaster"
    if any(word in lowered for word in ["epidemic", "vaccine", "hospital", "clinic"]):
        return "Epidemic"
    if any(word in lowered for word in ["terror", "security alert", "border raid"]):
        return "Terrorism"
    if any(word in lowered for word in ["corruption", "bribery", "fraud", "procurement"]):
        return "Corruption"
    if any(word in lowered for word in ["sport", "stadium", "olympic"]):
        return "Sport"
    if any(word in lowered for word in ["culture", "museum", "festival", "heritage"]):
        return "Culture"
    if any(word in lowered for word in ["migration", "refugee", "visa", "diaspora"]):
        return "Migration"
    if any(word in lowered for word in ["energy", "oil", "grid", "pipeline", "refinery"]):
        return "Energy"
    if any(word in lowered for word in ["diplomacy", "relation", "alliance", "spy", "sanction", "ultimatum", "guarantee"]):
        return "Diplomacy"
    return "General"
