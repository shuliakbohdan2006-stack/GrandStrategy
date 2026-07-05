from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Tuple

import pygame


ASSET_ROOT = Path(__file__).resolve().parent
ICON_DIR = ASSET_ROOT / "icons"
FLAG_DIR = ASSET_ROOT / "flags"
FONT_DIR = ASSET_ROOT / "fonts"
IMAGE_DIR = ASSET_ROOT / "images"
SOUND_DIR = ASSET_ROOT / "sounds"


class AssetManager:
    """Centralized cached access to project visual and audio assets."""

    def __init__(self) -> None:
        self.icon_cache: Dict[Tuple[str, Tuple[int, int]], pygame.Surface] = {}
        self.flag_cache: Dict[Tuple[str, Tuple[int, int]], pygame.Surface] = {}
        self.image_cache: Dict[str, pygame.Surface] = {}
        self.scaled_image_cache: Dict[Tuple[str, Tuple[int, int]], pygame.Surface] = {}
        self.sound_cache: Dict[str, Optional[pygame.mixer.Sound]] = {}
        self.font_cache: Dict[Tuple[int, bool], pygame.font.Font] = {}
        self.audio_available = self._init_audio()

    def _init_audio(self) -> bool:
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            return True
        except pygame.error:
            return False

    def get_font(self, size: int, bold: bool = False) -> pygame.font.Font:
        key = (size, bold)
        if key in self.font_cache:
            return self.font_cache[key]
        candidates = [
            FONT_DIR / ("NotoSans-Bold.ttf" if bold else "NotoSans-Regular.ttf"),
            FONT_DIR / ("Inter-Bold.ttf" if bold else "Inter-Regular.ttf"),
        ]
        for path in candidates:
            if path.exists():
                font = pygame.font.Font(str(path), size)
                self.font_cache[key] = font
                return font
        font = pygame.font.SysFont("segoeui", size, bold=bold)
        self.font_cache[key] = font
        return font

    def get_icon(self, name: str, size: Tuple[int, int] = (22, 22)) -> pygame.Surface:
        key = (name, size)
        if key in self.icon_cache:
            return self.icon_cache[key]
        path = ICON_DIR / f"{name}.png"
        if path.exists():
            icon = self._load_alpha(path)
        else:
            icon = self._placeholder_icon(name)
        if icon.get_size() != size:
            icon = pygame.transform.smoothscale(icon, size)
        self.icon_cache[key] = icon
        return icon

    def get_flag(self, country, size: Tuple[int, int] = (54, 34)) -> pygame.Surface:
        iso = str(getattr(country, "iso_a2", "") or getattr(country, "iso_a3", "") or country.name).lower()
        key = (f"{country.name}:{iso}", size)
        if key in self.flag_cache:
            return self.flag_cache[key]
        candidates = [
            FLAG_DIR / f"{iso}.png",
            FLAG_DIR / f"{country.name.lower().replace(' ', '_')}.png",
        ]
        surface: Optional[pygame.Surface] = None
        for path in candidates:
            if path.exists():
                surface = self._load_alpha(path)
                break
        if surface is None:
            surface = self._placeholder_flag(country.flag_colors, size)
        if surface.get_size() != size:
            surface = pygame.transform.smoothscale(surface, size)
        self.flag_cache[key] = surface
        return surface

    def get_image(self, name: str) -> Optional[pygame.Surface]:
        if name in self.image_cache:
            return self.image_cache[name]
        path = IMAGE_DIR / name
        if not path.exists():
            return None
        image = pygame.image.load(str(path))
        if pygame.display.get_init() and pygame.display.get_surface():
            image = image.convert()
        self.image_cache[name] = image
        return image

    def get_image_scaled(self, name: str, size: Tuple[int, int]) -> Optional[pygame.Surface]:
        key = (name, size)
        if key in self.scaled_image_cache:
            return self.scaled_image_cache[key]
        image = self.get_image(name)
        if image is None:
            return None
        scaled = image if image.get_size() == size else pygame.transform.smoothscale(image, size)
        self.scaled_image_cache[key] = scaled
        return scaled

    def get_sound(self, name: str) -> Optional[pygame.mixer.Sound]:
        if name in self.sound_cache:
            return self.sound_cache[name]
        if not self.audio_available:
            self.sound_cache[name] = None
            return None
        path = SOUND_DIR / f"{name}.wav"
        if not path.exists():
            self.sound_cache[name] = None
            return None
        try:
            sound = pygame.mixer.Sound(str(path))
        except pygame.error:
            sound = None
        self.sound_cache[name] = sound
        return sound

    def play(self, name: str, enabled: bool = True, volume: float = 0.55) -> None:
        if not enabled:
            return
        sound = self.get_sound(name)
        if sound:
            sound.set_volume(volume)
            sound.play()

    def _placeholder_icon(self, name: str) -> pygame.Surface:
        surface = pygame.Surface((64, 64), pygame.SRCALPHA)
        pygame.draw.rect(surface, (50, 67, 82), surface.get_rect(), border_radius=16)
        pygame.draw.rect(surface, (232, 180, 72), surface.get_rect().inflate(-8, -8), width=3, border_radius=12)
        letter = name[:1].upper() if name else "?"
        font = pygame.font.SysFont("segoeui", 34, bold=True)
        text = font.render(letter, True, (238, 242, 246))
        surface.blit(text, text.get_rect(center=surface.get_rect().center))
        return surface

    def _load_alpha(self, path: Path) -> pygame.Surface:
        surface = pygame.image.load(str(path))
        if pygame.display.get_init() and pygame.display.get_surface():
            return surface.convert_alpha()
        if surface.get_bitsize() not in (24, 32):
            normalized = pygame.Surface(surface.get_size(), pygame.SRCALPHA, 32)
            normalized.blit(surface, (0, 0))
            return normalized
        return surface

    def _placeholder_flag(self, colors, size: Tuple[int, int]) -> pygame.Surface:
        surface = pygame.Surface(size, pygame.SRCALPHA)
        palette = list(colors or [(230, 230, 230), (82, 126, 172), (38, 45, 54)])
        stripe_w = max(1, size[0] // len(palette))
        for index, color in enumerate(palette):
            rect = pygame.Rect(index * stripe_w, 0, stripe_w + 2, size[1])
            pygame.draw.rect(surface, color, rect)
        pygame.draw.rect(surface, (13, 18, 24), surface.get_rect(), width=1)
        return surface
