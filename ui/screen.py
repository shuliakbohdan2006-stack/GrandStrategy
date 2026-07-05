from __future__ import annotations

from typing import Callable, List, Optional, Tuple

import pygame

from assets import AssetManager
from core.game_state import GameState
from localization import set_language, tr
from systems.settings import load_settings
from ui.country_select import UICountrySelectMixin
from ui.game_view import UIGameViewMixin
from ui.helpers import country_at_screen_pos, draw_fitted_text, draw_text, draw_wrapped_text
from ui.layout import MAP_RECT, SCREEN_HEIGHT, SCREEN_WIDTH
from ui.menu import UIMenuMixin
from ui.settings_view import UISettingsMixin
from ui.tabs import UITabsMixin
from ui.theme import ACCENT, ACCENT_BLUE, TEXT, blend


class Button:
    def __init__(
        self,
        rect: pygame.Rect,
        label: str,
        action: Callable[[GameState], Optional[GameState]],
        active: bool = False,
        enabled: bool = True,
        tooltip: str = "",
        icon: str = "",
    ) -> None:
        self.rect = rect
        self.label = label
        self.action = action
        self.active = active
        self.enabled = enabled
        self.tooltip = tooltip or label
        self.icon = icon

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, assets: AssetManager) -> None:
        if self.label == "":
            if self.enabled and self.rect.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(surface, (255, 255, 255), self.rect, width=1, border_radius=7)
            return
        hover = self.enabled and self.rect.collidepoint(pygame.mouse.get_pos())
        pressed = hover and pygame.mouse.get_pressed(num_buttons=3)[0]
        if not self.enabled:
            bg = (47, 55, 65)
            fg = (122, 135, 148)
        elif self.active:
            bg = ACCENT if not hover else blend(ACCENT, (255, 236, 150), 0.18)
            fg = (21, 24, 28)
        else:
            bg = ACCENT_BLUE if not hover else blend(ACCENT_BLUE, (125, 178, 224), 0.25)
            fg = TEXT
        if pressed:
            bg = blend(bg, (0, 0, 0), 0.18)
        pygame.draw.rect(surface, bg, self.rect, border_radius=8)
        pygame.draw.rect(surface, (14, 20, 27), self.rect, width=1, border_radius=8)
        label_rect = self.rect.copy()
        if self.icon:
            icon = assets.get_icon(self.icon, (18, 18))
            icon_x = self.rect.x + 12
            icon_y = self.rect.centery - 9
            surface.blit(icon, (icon_x, icon_y))
            label_rect.x += 26
            label_rect.width -= 28
        draw_fitted_text(surface, self.label, label_rect, font, fg)




class UI(UIMenuMixin, UICountrySelectMixin, UISettingsMixin, UIGameViewMixin, UITabsMixin):
    def __init__(self) -> None:
        pygame.font.init()
        self.assets = AssetManager()
        self.settings = load_settings()
        set_language(str(self.settings.get("language", "en")))
        self.mode = "main_menu"
        self.previous_mode = "main_menu"
        self.mode_started_at = pygame.time.get_ticks()
        self.exit_requested = False
        self.display_mode_changed = False
        self.current_fps = 0.0
        self.country_search = ""
        self.search_active = False
        self.search_rect = pygame.Rect(0, 0, 0, 0)
        self.country_sort = "Population"
        self.country_scroll = 0
        self.continent_filter = tr("country_select.all_continents")
        self.selected_country_name = "USA"
        self._reload_fonts()
        self.buttons: List[Button] = []
        self.notification_signature = ""
        self.dragging_map = False
        self.mouse_down_pos: Optional[Tuple[int, int]] = None
        self.last_mouse_pos: Optional[Tuple[int, int]] = None
        self.map_drag_distance = 0

    def _reload_fonts(self) -> None:
        scale = float(self.settings.get("ui_scale", 1.0))
        self.font = self.assets.get_font(max(14, int(18 * scale)))
        self.small_font = self.assets.get_font(max(12, int(15 * scale)))
        self.tiny_font = self.assets.get_font(max(10, int(13 * scale)))
        self.title_font = self.assets.get_font(max(20, int(28 * scale)), bold=True)
        self.hero_font = self.assets.get_font(max(40, int(64 * scale)), bold=True)

    def _set_mode(self, mode: str):
        self.mode = mode
        self.mode_started_at = pygame.time.get_ticks()
        return None

    def _open_settings(self, previous_mode: str):
        self.previous_mode = previous_mode
        return self._set_mode("settings")

    def _request_exit(self):
        self.exit_requested = True
        return None

    def draw(self, screen: pygame.Surface, state: GameState) -> None:
        self.buttons = []
        if self.mode == "main_menu":
            self._draw_main_menu(screen, state)
        elif self.mode == "country_select":
            self._draw_country_select(screen, state)
        elif self.mode == "settings":
            self._draw_settings_screen(screen, state)
        elif self.mode == "credits":
            self._draw_credits(screen, state)
        elif self.mode == "pause":
            self._draw_pause_menu(screen, state)
        else:
            self._draw_game_screen(screen, state)
        if bool(self.settings.get("fps_counter", False)):
            draw_text(screen, f"FPS {self.current_fps:.0f}", (12, 8), self.tiny_font, ACCENT)
        self._play_new_notification(state)
        self._draw_buttons(screen)
        self._draw_tooltip(screen)

    def handle_click(self, pos: Tuple[int, int], state: GameState) -> Optional[GameState]:
        for button in reversed(self.buttons):
            if button.enabled and button.rect.collidepoint(pos):
                self._play_button_sound(button)
                return button.action(state)

        if self.mode == "country_select":
            self.search_active = self.search_rect.collidepoint(pos)
            return None

        if self.mode == "game" and MAP_RECT.collidepoint(pos):
            country = country_at_screen_pos(state, pos)
            if country and country.name != state.player_country_name:
                state.selected_target_name = country.name
                state.add_message(f"Selected target: {country.name}.")
            elif country:
                state.add_message(f"Selected your country: {country.name}.")
        return None

    def handle_mouse_down(self, pos: Tuple[int, int], button: int, state: GameState) -> Optional[GameState]:
        if button == 1:
            self.mouse_down_pos = pos
            self.last_mouse_pos = pos
            self.map_drag_distance = 0
            self.dragging_map = self.mode == "game" and MAP_RECT.collidepoint(pos) and not any(btn.rect.collidepoint(pos) for btn in self.buttons)
            return None
        if button in [2, 3] and self.mode == "game" and MAP_RECT.collidepoint(pos):
            self.dragging_map = True
            self.last_mouse_pos = pos
        return None

    def handle_mouse_motion(self, pos: Tuple[int, int], state: GameState) -> None:
        if not self.dragging_map or not self.last_mouse_pos:
            return
        dx = pos[0] - self.last_mouse_pos[0]
        dy = pos[1] - self.last_mouse_pos[1]
        if dx or dy:
            state.camera.pan_pixels(dx, dy)
            self.map_drag_distance += abs(dx) + abs(dy)
        self.last_mouse_pos = pos

    def handle_mouse_up(self, pos: Tuple[int, int], button: int, state: GameState) -> Optional[GameState]:
        if button != 1:
            self.dragging_map = False
            self.last_mouse_pos = None
            return None
        was_dragging = self.dragging_map and self.map_drag_distance > 6
        self.dragging_map = False
        self.last_mouse_pos = None
        if was_dragging:
            return None
        return self.handle_click(pos, state)

    def handle_mouse_wheel(self, pos: Tuple[int, int], amount: int, state: GameState) -> None:
        if self.mode == "country_select":
            self.country_scroll = max(0, self.country_scroll - amount * 2)
        elif self.mode == "game":
            state.camera.zoom_at(amount, pos, MAP_RECT)

    def handle_key_down(self, event: pygame.event.Event, state: GameState) -> Optional[GameState]:
        if event.key == pygame.K_ESCAPE:
            if self.mode == "game":
                return self._set_mode("pause")
            if self.mode == "pause":
                return self._set_mode("game")
            if self.mode in ["settings", "credits"]:
                return self._set_mode(self.previous_mode if self.mode == "settings" else "main_menu")
            return None
        if self.mode == "country_select" and self.search_active:
            if event.key == pygame.K_BACKSPACE:
                self.country_search = self.country_search[:-1]
                self.country_scroll = 0
            elif event.key == pygame.K_RETURN:
                self.search_active = False
        return None

    def handle_text_input(self, text: str, state: GameState) -> Optional[GameState]:
        if self.mode == "country_select" and self.search_active:
            filtered = "".join(char for char in text if char.isprintable())
            if filtered:
                self.country_search += filtered
                self.country_scroll = 0
        return None

    def should_tick_game(self) -> bool:
        return self.mode == "game"

    def consume_display_mode_changed(self) -> bool:
        changed = self.display_mode_changed
        self.display_mode_changed = False
        return changed

    def _draw_tooltip(self, screen: pygame.Surface) -> None:
        if not bool(self.settings.get("tooltips", True)):
            return
        mouse_pos = pygame.mouse.get_pos()
        hovered = next((button for button in reversed(self.buttons) if button.enabled and button.rect.collidepoint(mouse_pos)), None)
        if not hovered or not hovered.tooltip:
            return
        text = hovered.tooltip
        width = min(360, max(150, self.small_font.size(text)[0] + 22))
        height = 44 if self.small_font.size(text)[0] <= width - 22 else 62
        x = min(mouse_pos[0] + 16, SCREEN_WIDTH - width - 8)
        y = min(mouse_pos[1] + 18, SCREEN_HEIGHT - height - 8)
        rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, (19, 24, 29), rect, border_radius=5)
        pygame.draw.rect(screen, (105, 126, 145), rect, width=1, border_radius=5)
        draw_wrapped_text(screen, text, pygame.Rect(rect.x + 10, rect.y + 9, rect.width - 20, rect.height - 14), self.tiny_font, (230, 235, 240))

    def _draw_wrapped_on_screen(
        self,
        screen: pygame.Surface,
        text: str,
        rect: pygame.Rect,
        font: pygame.font.Font,
        color: tuple[int, int, int],
    ) -> None:
        draw_wrapped_text(screen, text, rect, font, color)

    def _add_button(
        self,
        rect: pygame.Rect,
        label: str,
        action: Callable[[GameState], Optional[GameState]],
        active: bool = False,
        enabled: bool = True,
        tooltip: str = "",
        icon: str = "",
    ) -> None:
        button = Button(rect, label, action, active, enabled, tooltip, icon)
        self.buttons.append(button)

    def _draw_buttons(self, screen: pygame.Surface) -> None:
        for button in self.buttons:
            button.draw(screen, self.small_font, self.assets)

    def _play_button_sound(self, button: Button) -> None:
        if "declare" in button.label.lower() or button.icon == "war":
            self.assets.play("war", bool(self.settings.get("sound", True)))
        else:
            self.assets.play("button", bool(self.settings.get("sound", True)))

    def _play_new_notification(self, state: GameState) -> None:
        if not state.notifications:
            self.notification_signature = ""
            return
        note = state.notifications[0]
        signature = f"{note.get('title')}:{note.get('body')}:{note.get('date')}"
        if signature == self.notification_signature:
            return
        self.notification_signature = signature
        title = str(note.get("title", "")).lower()
        sound = "war" if "war" in title else "popup"
        self.assets.play(sound, bool(self.settings.get("sound", True)), volume=0.5)


