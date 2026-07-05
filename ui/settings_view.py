from __future__ import annotations

import pygame

from localization import set_language, tr
from systems.settings import save_settings
from ui.layout import SCREEN_HEIGHT, SCREEN_WIDTH
from ui.theme import ACCENT, BG, MUTED, PANEL, TEXT, draw_soft_panel


class UISettingsMixin:
    def _draw_settings_screen(self, screen: pygame.Surface, state) -> None:
        if self.previous_mode == "pause":
            self._draw_game_screen(screen, state)
            self.buttons = []
            overlay = getattr(self, "_pause_overlay_surface", None)
            if overlay is None or overlay.get_size() != (SCREEN_WIDTH, SCREEN_HEIGHT):
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 145))
                self._pause_overlay_surface = overlay
            screen.blit(overlay, (0, 0))
        else:
            screen.fill(BG)
        rect = pygame.Rect(350, 92, 740, 650)
        draw_soft_panel(screen, rect, PANEL, radius=16)
        screen.blit(self.hero_font.render(tr("menu.settings"), True, TEXT), (rect.x + 44, rect.y + 36))
        self._add_button(pygame.Rect(rect.right - 174, rect.y + 44, 128, 36), tr("button.back"), lambda s: self._set_mode(self.previous_mode), icon="exit")

        y = rect.y + 132
        screen.blit(self.font.render(tr("settings.language"), True, ACCENT), (rect.x + 46, y))
        languages = [("en", tr("settings.english")), ("ru", tr("settings.russian")), ("de", tr("settings.german")), ("uk", tr("settings.ukrainian"))]
        x = rect.x + 46
        y += 34
        for code, label in languages:
            self._add_button(pygame.Rect(x, y, 146, 36), label, lambda s, c=code: self._set_language(c, s), active=self.settings.get("language") == code, icon="language")
            x += 154

        y += 72
        screen.blit(self.font.render(tr("settings.ui_scale"), True, ACCENT), (rect.x + 46, y))
        x = rect.x + 250
        for scale in [0.9, 1.0, 1.1, 1.2]:
            self._add_button(pygame.Rect(x, y - 6, 78, 34), f"{scale:.1f}x", lambda s, v=scale: self._set_ui_scale(v, s), active=abs(float(self.settings.get("ui_scale", 1.0)) - scale) < 0.01)
            x += 86

        toggles = [
            ("fullscreen", "settings.fullscreen"),
            ("sound", "settings.sound"),
            ("autosave", "settings.autosave"),
            ("tooltips", "settings.tooltips"),
            ("fps_counter", "settings.fps_counter"),
        ]
        y += 70
        for key, label_key in toggles:
            active = bool(self.settings.get(key, False))
            state_label = tr("settings.on") if active else tr("settings.off")
            label = f"{tr(label_key)}: {state_label}"
            icon_map = {
                "fullscreen": "settings",
                "sound": "technology",
                "autosave": "save",
                "tooltips": "language",
                "fps_counter": "statistics",
            }
            icon = icon_map.get(key, "settings")
            self._add_button(pygame.Rect(rect.x + 46, y, 230, 38), label, lambda s, k=key: self._toggle_setting(k, s), active=active, icon=icon)
            y += 52

        difficulty = str(self.settings.get("difficulty", "Normal"))
        self._add_button(
            pygame.Rect(rect.x + 46, y, 230, 38),
            f"{tr('settings.difficulty')}: {difficulty}",
            self._cycle_difficulty,
            tooltip=tr("tooltip.difficulty"),
            icon="stability",
        )

        mode_label = tr("settings.fullscreen") if self.settings.get("fullscreen") else tr("settings.windowed")
        screen.blit(self.small_font.render(f"{tr('settings.display')}: {mode_label}", True, MUTED), (rect.x + 46, rect.bottom - 80))

    def _set_language(self, language_code: str, state):
        self.settings["language"] = language_code
        set_language(language_code)
        self.continent_filter = tr("country_select.all_continents")
        state.settings["language"] = language_code
        save_settings(self.settings)
        return None

    def _set_ui_scale(self, scale: float, state):
        self.settings["ui_scale"] = scale
        state.settings["ui_scale"] = scale
        save_settings(self.settings)
        self._reload_fonts()
        return None

    def _toggle_setting(self, key: str, state):
        self.settings[key] = not bool(self.settings.get(key, False))
        state.settings[key] = self.settings[key]
        if key == "fullscreen":
            self.display_mode_changed = True
        save_settings(self.settings)
        return None

    def _cycle_difficulty(self, state):
        options = ["Easy", "Normal", "Hard"]
        current = str(self.settings.get("difficulty", "Normal"))
        next_value = options[(options.index(current) + 1) % len(options)] if current in options else "Normal"
        self.settings["difficulty"] = next_value
        state.settings["difficulty"] = next_value
        save_settings(self.settings)
        return None
