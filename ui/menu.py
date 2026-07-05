from __future__ import annotations

import math

import pygame

from core.game_state import GameState
from core.version import GAME_VERSION
from localization import tr
from systems.save_load import load_game
from systems.settings import apply_settings_to_state
from ui.layout import SCREEN_HEIGHT, SCREEN_WIDTH
from ui.theme import ACCENT, BG, MUTED, PANEL, TEXT, draw_soft_panel


class UIMenuMixin:
    def _draw_menu_background(self, screen: pygame.Surface) -> None:
        background = self.assets.get_image_scaled("menu_background.png", (SCREEN_WIDTH, SCREEN_HEIGHT))
        if background:
            screen.blit(background, (0, 0))
        else:
            screen.fill(BG)
        elapsed = pygame.time.get_ticks() / 1000
        glow = getattr(self, "_menu_glow_surface", None)
        if glow is None or glow.get_size() != (SCREEN_WIDTH, SCREEN_HEIGHT):
            glow = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            self._menu_glow_surface = glow
        glow.fill((0, 0, 0, 0))
        pulse = 34 + int(18 * math.sin(elapsed * 0.9))
        pygame.draw.circle(glow, (222, 174, 72, pulse), (1060, 250), 260)
        pygame.draw.circle(glow, (76, 139, 194, 28), (290, 620), 340)
        screen.blit(glow, (0, 0))

    def _draw_main_menu(self, screen: pygame.Surface, state: GameState) -> None:
        self._draw_menu_background(screen)
        alpha = min(255, int((pygame.time.get_ticks() - self.mode_started_at) / 800 * 255))
        title_surface = self.hero_font.render(tr("app.title"), True, TEXT)
        subtitle_surface = self.font.render(tr("app.subtitle"), True, MUTED)
        title_surface.set_alpha(alpha)
        subtitle_surface.set_alpha(alpha)
        screen.blit(title_surface, (110, 118))
        screen.blit(subtitle_surface, (116, 190))

        panel = pygame.Rect(104, 260, 320, 360)
        draw_soft_panel(screen, panel, PANEL, radius=14)
        items = [
            (tr("menu.new_game"), lambda s: self._new_game(), "victory"),
            (tr("menu.load_game"), lambda s: self._load_game_from_menu(s), "load"),
            (tr("menu.settings"), lambda s: self._open_settings("main_menu"), "settings"),
            (tr("menu.credits"), lambda s: self._set_mode("credits"), "language"),
            (tr("menu.exit"), lambda s: self._request_exit(), "exit"),
        ]
        y = panel.y + 34
        for label, action, icon in items:
            self._add_button(pygame.Rect(panel.x + 34, y, 252, 42), label, action, tooltip=label, icon=icon)
            y += 58

        info = pygame.Rect(520, 260, 720, 248)
        draw_soft_panel(screen, info, (24, 34, 45), radius=16)
        draw_text = self.font.render(f"{tr('menu.version')} {GAME_VERSION}", True, ACCENT)
        screen.blit(draw_text, (info.x + 28, info.y + 28))
        copy = [
            tr("menu.feature_1"),
            tr("menu.feature_2"),
            tr("menu.feature_3"),
        ]
        for i, line in enumerate(copy):
            screen.blit(self.small_font.render(line, True, MUTED), (info.x + 28, info.y + 76 + i * 28))

    def _draw_pause_menu(self, screen: pygame.Surface, state: GameState) -> None:
        self._draw_game_screen(screen, state)
        self.buttons = []
        overlay = getattr(self, "_pause_overlay_surface", None)
        if overlay is None or overlay.get_size() != (SCREEN_WIDTH, SCREEN_HEIGHT):
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 145))
            self._pause_overlay_surface = overlay
        screen.blit(overlay, (0, 0))
        rect = pygame.Rect(518, 142, 404, 520)
        draw_soft_panel(screen, rect, PANEL, radius=16)
        screen.blit(self.title_font.render("ESC", True, ACCENT), (rect.x + 38, rect.y + 32))
        items = [
            (tr("menu.resume"), lambda s: self._set_mode("game"), "victory"),
            (tr("button.save"), self._save_from_menu, "save"),
            (tr("button.load"), self._load_game_from_menu, "load"),
            (tr("menu.settings"), lambda s: self._open_settings("pause"), "settings"),
            (tr("menu.main_menu"), lambda s: self._set_mode("main_menu"), "menu"),
            (tr("menu.exit"), lambda s: self._request_exit(), "exit"),
        ]
        y = rect.y + 94
        for label, action, icon in items:
            self._add_button(pygame.Rect(rect.x + 52, y, 300, 42), label, action, tooltip=label, icon=icon)
            y += 61

    def _draw_credits(self, screen: pygame.Surface, state: GameState) -> None:
        self._draw_menu_background(screen)
        rect = pygame.Rect(360, 170, 720, 380)
        draw_soft_panel(screen, rect, PANEL, radius=16)
        screen.blit(self.hero_font.render(tr("menu.credits"), True, TEXT), (rect.x + 40, rect.y + 40))
        screen.blit(self.font.render(tr("menu.credits_text"), True, MUTED), (rect.x + 44, rect.y + 140))
        screen.blit(self.small_font.render(tr("menu.data_credit"), True, MUTED), (rect.x + 44, rect.y + 178))
        self._add_button(pygame.Rect(rect.x + 44, rect.bottom - 82, 180, 42), tr("button.back"), lambda s: self._set_mode("main_menu"))

    def _new_game(self):
        new_state = GameState()
        apply_settings_to_state(new_state, self.settings)
        self.country_search = ""
        self.country_scroll = 0
        self.selected_country_name = "USA" if "USA" in new_state.countries else next(iter(new_state.countries))
        self._set_mode("country_select")
        return new_state

    def _load_game_from_menu(self, state: GameState):
        try:
            loaded = load_game()
        except Exception as exc:
            self.assets.play("error", bool(self.settings.get("sound", True)))
            state.add_message(f"{tr('status.load_failed')}: {exc}")
            return None
        apply_settings_to_state(loaded, self.settings)
        self._set_mode("game")
        self.assets.play("load", bool(self.settings.get("sound", True)))
        loaded.add_message(tr("status.loaded"))
        return loaded

    def _save_from_menu(self, state: GameState):
        from systems.save_load import save_game

        save_game(state)
        self.assets.play("save", bool(self.settings.get("sound", True)))
        state.add_message(tr("status.saved"))
        if self.mode != "pause":
            self._set_mode("game")
        return None
