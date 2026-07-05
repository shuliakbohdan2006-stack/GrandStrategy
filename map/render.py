from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

import pygame

from core.country_model import Country
from map.camera import MapCamera
from map.world import WORLD_WIDTH, find_country_at, lonlat_to_world
from systems.armies import Army


ProjectedRing = Tuple[List[Tuple[float, float]], pygame.Rect]
_PROJECTED_CACHE: Dict[str, List[ProjectedRing]] = {}
_OCEAN_CACHE: Dict[Tuple[int, int], pygame.Surface] = {}

RIVERS = [
    [(-95, 47), (-92, 42), (-90, 35), (-89, 30)],
    [(-74, -4), (-62, -3), (-54, -2), (-49, -1)],
    [(31, 30), (31, 24), (32, 18), (31, 10)],
    [(8, 48), (14, 48), (20, 46), (29, 45)],
    [(90, 31), (101, 31), (112, 30), (121, 31)],
]


def draw_world_map(screen: pygame.Surface, state, rect: pygame.Rect, fonts: Dict[str, pygame.font.Font], choose_mode: bool = False) -> None:
    draw_ocean(screen, rect)
    old_clip = screen.get_clip()
    screen.set_clip(rect)
    draw_graticule(screen, state.camera, rect)
    draw_rivers(screen, state.camera, rect)

    for country in state.countries.values():
        draw_country(screen, state, country, rect, fonts)

    if not choose_mode:
        draw_fronts(screen, state, rect, fonts)
        draw_armies(screen, state.camera, state.armies, state.countries, rect, fonts)

    title = "Real world map - Natural Earth 110m"
    screen.blit(fonts["small"].render(title, True, (224, 235, 240)), (rect.x + 16, rect.y + 12))
    if choose_mode:
        hint = "Click real country borders to start. Mouse wheel zooms, drag the map to pan."
        screen.blit(fonts["tiny"].render(hint, True, (219, 226, 232)), (rect.x + 18, rect.bottom - 28))
    screen.set_clip(old_clip)
    pygame.draw.rect(screen, (11, 18, 24), rect, width=2, border_radius=8)


def draw_ocean(screen: pygame.Surface, rect: pygame.Rect) -> None:
    base = _OCEAN_CACHE.get(rect.size)
    if base is None:
        base = pygame.Surface(rect.size)
        for y in range(rect.height):
            t = y / max(1, rect.height)
            color = (13, 57 + int(20 * t), 75 + int(28 * t))
            pygame.draw.line(base, color, (0, y), (rect.width, y))
        _OCEAN_CACHE[rect.size] = base
    screen.blit(base, rect)
    pygame.draw.rect(screen, (19, 87, 107), rect, width=1, border_radius=8)


def draw_country(screen: pygame.Surface, state, country: Country, rect: pygame.Rect, fonts: Dict[str, pygame.font.Font]) -> None:
    rings = projected_rings(country)
    if not rings:
        return
    fill = country.color
    border = (28, 34, 39)
    width = 1
    if country.name == state.player_country_name:
        border, width = (246, 219, 103), 3
    elif country.name == state.selected_target_name:
        border, width = (244, 248, 252), 3
    elif state.player_country_name and state.get_war_between(state.player_country_name, country.name):
        border, width = (238, 93, 93), 3
    elif state.player_country_name and country.name in state.countries[state.player_country_name].allies:
        border, width = (94, 204, 135), 2
    elif country.vassal_of:
        border, width = (184, 124, 219), 2

    visible = False
    clip_rect = rect.inflate(30, 30)
    for ring, bbox in rings:
        if not world_bbox_visible(state.camera, bbox, rect, clip_rect):
            continue
        points = [state.camera.world_to_screen(point, rect) for point in ring]
        if not points:
            continue
        screen_bbox = pygame.Rect(min(p[0] for p in points), min(p[1] for p in points), 1, 1)
        screen_bbox.width = max(p[0] for p in points) - screen_bbox.x
        screen_bbox.height = max(p[1] for p in points) - screen_bbox.y
        if not screen_bbox.colliderect(clip_rect):
            continue
        if screen_bbox.width < 2 and screen_bbox.height < 2:
            continue
        visible = True
        pygame.draw.polygon(screen, fill, points)
        pygame.draw.polygon(screen, (12, 18, 23), points, width=max(1, width - 1))
        pygame.draw.polygon(screen, border, points, width=width)

    if visible:
        draw_country_labels(screen, state.camera, country, rect, fonts)


def draw_country_labels(screen: pygame.Surface, camera: MapCamera, country: Country, rect: pygame.Rect, fonts: Dict[str, pygame.font.Font]) -> None:
    sx, sy = camera.lonlat_to_screen(country.label_lon, country.label_lat, rect)
    if not rect.collidepoint((sx, sy)):
        return
    show_name = camera.zoom > 1.35 or (country.is_core_country and camera.zoom > 0.82)
    if show_name:
        text = fonts["tiny"].render(country.name, True, (245, 247, 249))
        label_rect = pygame.Rect(sx - text.get_width() // 2 - 5, sy - 10, text.get_width() + 10, 20)
        shadow = pygame.Surface(label_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 118), shadow.get_rect(), border_radius=5)
        screen.blit(shadow, (label_rect.x + 2, label_rect.y + 2))
        pygame.draw.rect(screen, (15, 21, 26), label_rect, border_radius=4)
        pygame.draw.rect(screen, (56, 71, 82), label_rect, width=1, border_radius=4)
        screen.blit(text, (label_rect.x + 5, label_rect.y + 3))
    if camera.zoom > 1.65:
        cx, cy = camera.lonlat_to_screen(country.capital_lon, country.capital_lat, rect)
        pygame.draw.circle(screen, (246, 225, 149), (cx, cy), 3)
        if camera.zoom > 2.45:
            screen.blit(fonts["tiny"].render(country.capital, True, (236, 232, 208)), (cx + 6, cy - 8))
    if camera.zoom > 2.15 and country.is_core_country:
        draw_map_icons(screen, camera, country, rect, fonts)
    if camera.zoom > 3.0 and country.provinces:
        draw_region_names(screen, camera, country, rect, fonts)


def draw_map_icons(screen: pygame.Surface, camera: MapCamera, country: Country, rect: pygame.Rect, fonts: Dict[str, pygame.font.Font]) -> None:
    x, y = camera.lonlat_to_screen(country.capital_lon, country.capital_lat, rect)
    icons = [("O", (74, 117, 174)), ("F", (89, 164, 93)), ("M", (169, 159, 139)), ("I", (194, 129, 58))]
    for index, (label, color) in enumerate(icons):
        px = x + 12 + index * 17
        py = y + 10
        pygame.draw.circle(screen, (11, 17, 22), (px, py), 9)
        pygame.draw.circle(screen, color, (px, py), 7)
        screen.blit(fonts["tiny"].render(label, True, (18, 22, 26)), (px - 4, py - 8))


def draw_region_names(screen: pygame.Surface, camera: MapCamera, country: Country, rect: pygame.Rect, fonts: Dict[str, pygame.font.Font]) -> None:
    for index, region in enumerate(country.provinces[:5]):
        offset = (index - 2) * 1.7
        sx, sy = camera.lonlat_to_screen(country.label_lon + offset, country.label_lat - offset * 0.4, rect)
        if rect.collidepoint((sx, sy)):
            screen.blit(fonts["tiny"].render(str(region.get("name", "Region")), True, (199, 208, 216)), (sx, sy))


def draw_graticule(screen: pygame.Surface, camera: MapCamera, rect: pygame.Rect) -> None:
    for lon in range(-180, 181, 30):
        top = camera.lonlat_to_screen(lon, 80, rect)
        bottom = camera.lonlat_to_screen(lon, -60, rect)
        pygame.draw.line(screen, (24, 92, 111), top, bottom, 1)
    for lat in range(-60, 81, 30):
        left = camera.lonlat_to_screen(-180, lat, rect)
        right = camera.lonlat_to_screen(180, lat, rect)
        pygame.draw.line(screen, (24, 92, 111), left, right, 1)


def draw_rivers(screen: pygame.Surface, camera: MapCamera, rect: pygame.Rect) -> None:
    for river in RIVERS:
        points = [camera.lonlat_to_screen(lon, lat, rect) for lon, lat in river]
        if any(rect.collidepoint(point) for point in points):
            pygame.draw.lines(screen, (85, 166, 198), False, points, 2)


def draw_fronts(screen: pygame.Surface, state, rect: pygame.Rect, fonts: Dict[str, pygame.font.Font]) -> None:
    for war in state.active_wars.values():
        for front in list(war.get("fronts", [])):
            lon = float(front.get("lon", 0.0))
            lat = float(front.get("lat", 0.0))
            x, y = state.camera.lonlat_to_screen(lon, lat, rect)
            if not rect.collidepoint((x, y)):
                continue
            pygame.draw.circle(screen, (255, 210, 90), (x, y), 7)
            pygame.draw.circle(screen, (238, 93, 93), (x, y), 12, 2)
            if state.camera.zoom > 1.2:
                label = f"{front.get('progress', 50)}%"
                screen.blit(fonts["tiny"].render(label, True, (255, 238, 188)), (x + 10, y - 10))


def draw_armies(screen: pygame.Surface, camera: MapCamera, armies: Iterable[Army], countries: Dict[str, Country], rect: pygame.Rect, fonts: Dict[str, pygame.font.Font]) -> None:
    for army in armies:
        country = countries.get(army.country_name)
        if not country:
            continue
        x, y = camera.lonlat_to_screen(army.lon, army.lat, rect)
        if not rect.inflate(20, 20).collidepoint((x, y)):
            continue
        if army.target_lon is not None and army.target_lat is not None:
            tx, ty = camera.lonlat_to_screen(army.target_lon, army.target_lat, rect)
            pygame.draw.line(screen, (230, 216, 127), (x, y), (tx, ty), 1)
        color = (226, 178, 74) if army.stance == "attack" else (83, 148, 205) if army.stance == "defend" else (190, 102, 102)
        pygame.draw.circle(screen, (15, 20, 24), (x, y), 12)
        pygame.draw.circle(screen, color, (x, y), 10)
        pygame.draw.circle(screen, country.color, (x, y), 6)
        if camera.zoom > 1.45:
            label = f"{army.size}"
            screen.blit(fonts["tiny"].render(label, True, (244, 247, 249)), (x + 12, y - 8))
        if camera.zoom > 2.25:
            screen.blit(fonts["tiny"].render(army.general, True, (226, 232, 238)), (x + 12, y + 7))


def country_at_screen_pos(state, pos: Tuple[int, int], rect: pygame.Rect):
    if not rect.collidepoint(pos):
        return None
    lon, lat = state.camera.screen_to_lonlat(pos, rect)
    return find_country_at(state.countries.values(), lon, lat)


def projected_rings(country: Country) -> List[ProjectedRing]:
    cache_key = f"{country.name}:{len(country.geo_polygons)}"
    if cache_key in _PROJECTED_CACHE:
        return _PROJECTED_CACHE[cache_key]
    projected: List[ProjectedRing] = []
    for ring in country.geo_polygons:
        points = [lonlat_to_world(lon, lat) for lon, lat in ring]
        if not points:
            continue
        xs = [point[0] for point in points]
        if max(xs) - min(xs) > WORLD_WIDTH / 2:
            points = [(x + WORLD_WIDTH if x < WORLD_WIDTH / 2 else x, y) for x, y in points]
        bbox = pygame.Rect(int(min(x for x, _ in points)), int(min(y for _, y in points)), 1, 1)
        bbox.width = int(max(x for x, _ in points) - bbox.x)
        bbox.height = int(max(y for _, y in points) - bbox.y)
        projected.append((points, bbox))
    _PROJECTED_CACHE[cache_key] = projected
    return projected


def world_bbox_visible(camera: MapCamera, bbox: pygame.Rect, viewport: pygame.Rect, clip_rect: pygame.Rect) -> bool:
    corners = [
        (bbox.left, bbox.top),
        (bbox.right, bbox.top),
        (bbox.right, bbox.bottom),
        (bbox.left, bbox.bottom),
    ]
    points = [camera.world_to_screen(point, viewport) for point in corners]
    screen_bbox = pygame.Rect(min(p[0] for p in points), min(p[1] for p in points), 1, 1)
    screen_bbox.width = max(p[0] for p in points) - screen_bbox.x
    screen_bbox.height = max(p[1] for p in points) - screen_bbox.y
    return screen_bbox.colliderect(clip_rect)
