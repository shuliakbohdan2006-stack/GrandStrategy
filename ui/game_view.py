from __future__ import annotations

from typing import Optional

import pygame

from core.game_state import GameState
from localization import tr
from map.render import draw_world_map
from ui.actions import (
    dismiss_notification_action,
    select_target_action,
    set_speed_action,
)
from ui.helpers import draw_flag, draw_panel, draw_text, draw_wrapped_text
from ui.layout import ACTION_RECT, DETAIL_RECT, LEFT_PANEL_WIDTH, MAP_RECT, MESSAGE_RECT, SCREEN_HEIGHT, SCREEN_WIDTH
from ui.theme import ACCENT, BG, CATEGORY_COLORS, PANEL, PANEL_DARK, category_for, draw_soft_panel


class UIGameViewMixin:
    def _draw_game_screen(self, screen: pygame.Surface, state: GameState) -> None:
        screen.fill(BG)
        self._draw_top_bar(screen, state)
        self._draw_left_panel(screen, state)
        self._draw_map(screen, state)
        self._draw_detail_panel(screen, state)
        self._draw_tab_panel(screen, state)
        self._draw_messages(screen, state)
        self._draw_alert(screen, state)
        self._draw_game_over(screen, state)

    def _draw_top_bar(self, screen: pygame.Surface, state: GameState) -> None:
        pygame.draw.rect(screen, PANEL_DARK, pygame.Rect(0, 0, SCREEN_WIDTH, 60))
        draw_text(screen, f"{tr('game.calendar')}: {state.calendar_label}", (205, 19), self.font, (235, 239, 244))
        player = state.player_country
        if player:
            draw_text(screen, f"{tr('game.ruling')}: {player.name}", (500, 19), self.font, (235, 239, 244))

        x = 680
        for label, speed in [(tr("game.speed.pause"), 0), ("x1", 1), ("x2", 2), ("x5", 5)]:
            rect = pygame.Rect(x, 16, 68, 32)
            self._add_button(rect, label, lambda s, sp=speed: set_speed_action(s, sp), active=state.speed == speed, tooltip=f"{tr('tooltip.speed')} {label}", icon="technology" if speed else "")
            x += 78

        self._add_button(pygame.Rect(1110, 16, 90, 32), tr("menu.menu"), lambda s: self._set_mode("pause"), tooltip=tr("tooltip.menu"), icon="menu")
        self._add_button(pygame.Rect(1210, 16, 92, 32), tr("button.save"), self._save_from_menu, tooltip=tr("tooltip.save"), icon="save")
        self._add_button(pygame.Rect(1312, 16, 92, 32), tr("button.load"), self._load_game_from_menu, tooltip=tr("tooltip.load"), icon="load")

    def _draw_left_panel(self, screen: pygame.Surface, state: GameState) -> None:
        pygame.draw.rect(screen, PANEL_DARK, pygame.Rect(0, 60, LEFT_PANEL_WIDTH, SCREEN_HEIGHT - 60))
        draw_text(screen, tr("game.council"), (18, 84), self.title_font, (238, 241, 244))
        tabs = ["Overview", "Economy", "Army", "Production", "Construction", "Trade", "Diplomacy", "Politics", "Laws", "Family", "War", "Technology", "Statistics", "Settings"]
        tab_icons = {
            "Overview": "victory",
            "Economy": "economy",
            "Army": "army",
            "Production": "factory",
            "Construction": "construction",
            "Trade": "trade",
            "Diplomacy": "diplomacy",
            "Politics": "politics",
            "Laws": "government",
            "Family": "family",
            "War": "war",
            "Technology": "technology",
            "Statistics": "statistics",
            "Settings": "settings",
        }
        y = 118
        for tab in tabs:
            rect = pygame.Rect(16, y, 158, 28)
            label = tr(f"tabs.{tab.lower()}")
            self._add_button(rect, label, lambda s, t=tab: self._open_settings("game") if t == "Settings" else self._switch_tab(s, t), active=state.current_tab == tab, tooltip=f"{tr('tooltip.open')} {label}", icon=tab_icons.get(tab, "menu"))
            y += 32

        player = state.player_country
        if player:
            y = 588
            draw_text(screen, tr("game.state"), (18, y), self.font, (237, 240, 244))
            lines = [
                f"{tr('country_card.money')}: {player.money}",
                f"{tr('country_card.debt')}: {player.debt}",
                f"{tr('country_card.inflation')}: {player.inflation:.1f}%",
                f"{tr('country_card.army')}: {player.army}",
                f"{tr('country_card.stability')}: {player.stability}",
                f"{tr('country_card.technology')}: {player.technology}",
                f"{tr('country_card.resources')}:",
                f"{player.resources['oil']} / {player.resources['food']} / {player.resources['metal']}",
            ]
            for line in lines:
                y += 21
                draw_text(screen, line, (18, y), self.small_font, (181, 193, 202))

    def _switch_tab(self, state: GameState, tab: str) -> Optional[GameState]:
        state.current_tab = tab
        return None

    def _draw_map(self, screen: pygame.Surface, state: GameState, choose_mode: bool = False) -> None:
        draw_world_map(
            screen,
            state,
            MAP_RECT,
            {"title": self.title_font, "small": self.small_font, "tiny": self.tiny_font},
            choose_mode=choose_mode,
        )

    def _draw_detail_panel(self, screen: pygame.Surface, state: GameState) -> None:
        draw_panel(screen, DETAIL_RECT, (38, 48, 55))
        country = state.selected_target or state.player_country
        if not country:
            return
        draw_text(screen, country.name, (DETAIL_RECT.x + 16, DETAIL_RECT.y + 12), self.title_font, (238, 241, 244))
        draw_flag(screen, pygame.Rect(DETAIL_RECT.right - 82, DETAIL_RECT.y + 17, 54, 30), country.flag_colors, self.assets.get_flag(country, (54, 30)))
        government_line = f"Government: {country.government_type}"
        if country.is_democratic:
            government_line += f" | Election {country.next_election_year}"
        laws_line = f"Laws: {country.laws['taxes']} tax, {country.laws['conscription']} draft, {country.laws['trade_policy']}"
        lines = [
            f"Capital: {country.capital}",
            f"Leader: {country.leader}",
            government_line,
            f"Population: {country.population:.1f}M",
            f"Money: {country.money} | Army: {country.army}",
            f"Debt: {country.debt} | Inflation: {country.inflation:.1f}%",
            f"Stability: {country.stability} | Tech: {country.technology}",
            laws_line,
            f"Resources: O{country.resources['oil']} F{country.resources['food']} M{country.resources['metal']}",
            f"Output: O{country.resource_output()['oil']} F{country.resource_output()['food']} M{country.resource_output()['metal']}",
            f"Units: I{country.units['infantry']} T{country.units['tanks']} A{country.units['artillery']} Air{country.units['aircraft']}",
            f"Buildings: F{country.buildings['factory']} Farm{country.buildings['farm']} Oil{country.buildings['oil_field']} Mine{country.buildings['mine']}",
            f"Regions: {len(country.provinces)} | Influence: {country.influence}",
        ]
        if country.vassal_of:
            lines.append(f"Vassal of: {country.vassal_of}")
        if country.name != state.player_country_name:
            lines.append(f"Relation to you: {country.relation_to_player}")
        y = DETAIL_RECT.y + 50
        for line in lines[:11]:
            draw_text(screen, line, (DETAIL_RECT.x + 16, y), self.tiny_font, (197, 207, 216))
            y += 18

        region_names = ", ".join(str(region["name"]) for region in country.provinces[:4])
        if len(country.provinces) > 4:
            region_names += f", +{len(country.provinces) - 4}"
        draw_wrapped_text(
            screen,
            f"Regions: {region_names}",
            pygame.Rect(DETAIL_RECT.x + 16, DETAIL_RECT.bottom - 47, DETAIL_RECT.width - 32, 38),
            self.tiny_font,
            (171, 181, 190),
        )

    def _draw_target_list(self, screen: pygame.Surface, state: GameState, rect: pygame.Rect) -> None:
        names = state.target_names()
        columns = 4 if len(names) > 9 else 3 if len(names) > 6 else 2
        row_height = 24
        max_buttons = max(columns, columns * max(1, rect.height // row_height))
        names = names[:max_buttons]
        col_w = rect.width // columns
        for i, name in enumerate(names):
            x = rect.x + (i % columns) * col_w
            y = rect.y + (i // columns) * row_height
            button_rect = pygame.Rect(x, y, col_w - 6, 21)
            self._add_button(button_rect, name, lambda s, n=name: select_target_action(s, n), active=name == state.selected_target_name)

    def _draw_messages(self, screen: pygame.Surface, state: GameState) -> None:
        draw_soft_panel(screen, MESSAGE_RECT, PANEL, radius=10)
        draw_text(screen, tr("game.messages"), (MESSAGE_RECT.x + 18, MESSAGE_RECT.y + 14), self.font, (238, 241, 244))
        y = MESSAGE_RECT.y + 44
        for message in state.messages[-9:]:
            category = category_for(message)
            color = CATEGORY_COLORS.get(category, ACCENT)
            pygame.draw.rect(screen, color, pygame.Rect(MESSAGE_RECT.x + 18, y + 2, 7, 32), border_radius=3)
            draw_text(screen, tr(f"category.{category.lower()}"), (MESSAGE_RECT.x + 32, y), self.tiny_font, color)
            draw_wrapped_text(screen, message, pygame.Rect(MESSAGE_RECT.x + 32, y + 15, MESSAGE_RECT.width - 50, 30), self.tiny_font, (191, 203, 212))
            y += 43

    def _draw_alert(self, screen: pygame.Surface, state: GameState) -> None:
        if not state.notifications:
            return
        note = state.notifications[0]
        shade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 74))
        screen.blit(shade, (0, 0))
        rect = pygame.Rect(410, 184, 620, 188)
        pygame.draw.rect(screen, (72, 52, 35), rect, border_radius=8)
        pygame.draw.rect(screen, (226, 178, 78), rect, width=2, border_radius=8)
        title = str(note.get("title", tr("notification.important_event")))
        body = str(note.get("body", ""))
        date = str(note.get("date", state.calendar_label))
        draw_text(screen, title, (rect.x + 22, rect.y + 18), self.title_font, (255, 228, 153))
        draw_text(screen, date, (rect.right - 150, rect.y + 25), self.small_font, (231, 215, 182))
        draw_wrapped_text(screen, body, pygame.Rect(rect.x + 22, rect.y + 64, rect.width - 44, 72), self.small_font, (248, 241, 226))
        self._add_button(
            pygame.Rect(rect.right - 138, rect.bottom - 48, 112, 32),
            tr("button.dismiss"),
            dismiss_notification_action,
            tooltip=tr("tooltip.dismiss"),
        )

    def _draw_game_over(self, screen: pygame.Surface, state: GameState) -> None:
        if not state.game_over:
            return
        shade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 150))
        screen.blit(shade, (0, 0))
        rect = pygame.Rect(400, 410, 640, 168)
        victory = state.game_over_reason.lower().startswith("victory")
        color = (61, 96, 64) if victory else (99, 50, 48)
        border = (126, 218, 124) if victory else (238, 101, 91)
        pygame.draw.rect(screen, color, rect, border_radius=8)
        pygame.draw.rect(screen, border, rect, width=2, border_radius=8)
        title = tr("game.victory") if victory else tr("game.game_over")
        draw_text(screen, title, (rect.x + 26, rect.y + 22), self.title_font, (246, 247, 238))
        draw_wrapped_text(
            screen,
            state.game_over_reason or "Your state can no longer continue.",
            pygame.Rect(rect.x + 26, rect.y + 70, rect.width - 52, 70),
            self.small_font,
            (236, 239, 230),
        )
