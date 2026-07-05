from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import pygame

from map.world import WORLD_HEIGHT, WORLD_WIDTH, lonlat_to_world, world_to_lonlat


@dataclass
class MapCamera:
    center_x: float = WORLD_WIDTH / 2
    center_y: float = WORLD_HEIGHT / 2
    zoom: float = 0.22
    target_zoom: float = 0.22

    def update(self, dt: float) -> None:
        smoothing = min(1.0, max(0.0, dt * 10.0))
        self.zoom += (self.target_zoom - self.zoom) * smoothing
        self.clamp()

    def clamp(self) -> None:
        self.target_zoom = max(0.18, min(7.0, self.target_zoom))
        self.zoom = max(0.18, min(7.0, self.zoom))
        margin_x = WORLD_WIDTH * 0.58
        margin_y = WORLD_HEIGHT * 0.58
        self.center_x = max(-margin_x, min(WORLD_WIDTH + margin_x, self.center_x))
        self.center_y = max(-margin_y, min(WORLD_HEIGHT + margin_y, self.center_y))

    def pan_pixels(self, dx: float, dy: float) -> None:
        self.center_x -= dx / max(0.1, self.zoom)
        self.center_y -= dy / max(0.1, self.zoom)
        self.clamp()

    def zoom_at(self, amount: int, mouse_pos: Tuple[int, int], viewport: pygame.Rect) -> None:
        if amount == 0 or not viewport.collidepoint(mouse_pos):
            return
        before = self.screen_to_world(mouse_pos, viewport)
        self.target_zoom *= 1.22 ** amount
        self.clamp()
        old_zoom = self.zoom
        self.zoom = self.target_zoom
        after = self.screen_to_world(mouse_pos, viewport)
        self.center_x += before[0] - after[0]
        self.center_y += before[1] - after[1]
        self.zoom = old_zoom
        self.clamp()

    def screen_to_world(self, pos: Tuple[int, int], viewport: pygame.Rect) -> Tuple[float, float]:
        return (
            self.center_x + (pos[0] - viewport.centerx) / max(0.1, self.zoom),
            self.center_y + (pos[1] - viewport.centery) / max(0.1, self.zoom),
        )

    def world_to_screen(self, world_pos: Tuple[float, float], viewport: pygame.Rect) -> Tuple[int, int]:
        x = viewport.centerx + (world_pos[0] - self.center_x) * self.zoom
        y = viewport.centery + (world_pos[1] - self.center_y) * self.zoom
        return int(x), int(y)

    def lonlat_to_screen(self, lon: float, lat: float, viewport: pygame.Rect) -> Tuple[int, int]:
        return self.world_to_screen(lonlat_to_world(lon, lat), viewport)

    def screen_to_lonlat(self, pos: Tuple[int, int], viewport: pygame.Rect) -> Tuple[float, float]:
        return world_to_lonlat(*self.screen_to_world(pos, viewport))

    def focus_lonlat(self, lon: float, lat: float, zoom: float = 2.2) -> None:
        self.center_x, self.center_y = lonlat_to_world(lon, lat)
        self.target_zoom = max(self.target_zoom, zoom)
        self.clamp()

    def to_dict(self) -> Dict[str, float]:
        return {
            "center_x": self.center_x,
            "center_y": self.center_y,
            "zoom": self.zoom,
            "target_zoom": self.target_zoom,
        }

    @classmethod
    def from_dict(cls, data: object) -> "MapCamera":
        values = dict(data or {})
        return cls(
            center_x=float(values.get("center_x", WORLD_WIDTH / 2)),
            center_y=float(values.get("center_y", WORLD_HEIGHT / 2)),
            zoom=float(values.get("zoom", 0.22)),
            target_zoom=float(values.get("target_zoom", values.get("zoom", 0.22))),
        )
