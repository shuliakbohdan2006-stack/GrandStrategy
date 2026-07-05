from __future__ import annotations

import pygame

from localization import tr
from ui.helpers import draw_flag, draw_fitted_text
from ui.layout import SCREEN_HEIGHT, SCREEN_WIDTH
from ui.theme import ACCENT, BG, MUTED, PANEL, PANEL_DARK, TEXT, draw_soft_panel


class UICountrySelectMixin:
    def _draw_country_select(self, screen: pygame.Surface, state) -> None:
        screen.fill(BG)
        draw_soft_panel(screen, pygame.Rect(28, 28, SCREEN_WIDTH - 56, SCREEN_HEIGHT - 56), (22, 31, 40), radius=16)
        screen.blit(self.title_font.render(tr("country_select.title"), True, TEXT), (58, 54))
        self._add_button(pygame.Rect(1232, 52, 142, 36), tr("button.back"), lambda s: self._set_mode("main_menu"), icon="exit")

        search_rect = pygame.Rect(58, 112, 340, 38)
        pygame.draw.rect(screen, (16, 22, 29), search_rect, border_radius=8)
        pygame.draw.rect(screen, ACCENT if self.search_active else (60, 73, 87), search_rect, width=1, border_radius=8)
        placeholder = tr("country_select.search")
        shown = self.country_search or placeholder
        color = TEXT if self.country_search else MUTED
        screen.blit(self.font.render(shown, True, color), (search_rect.x + 14, search_rect.y + 8))
        self.search_rect = search_rect

        continents = self._country_continents(state)
        self._add_button(pygame.Rect(420, 112, 220, 38), f"{tr('country_select.continent')}: {self.continent_filter}", lambda s: self._cycle_continent(continents))
        sort_labels = [
            ("Population", tr("sort.population")),
            ("Economy", tr("sort.economy")),
            ("Military", tr("sort.military")),
            ("Technology", tr("sort.technology")),
            ("Stability", tr("sort.stability")),
        ]
        x = 662
        for key, label in sort_labels:
            self._add_button(pygame.Rect(x, 112, 128, 38), label, lambda s, k=key: self._set_country_sort(k), active=self.country_sort == key)
            x += 136

        list_rect = pygame.Rect(58, 178, 620, 600)
        draw_soft_panel(screen, list_rect, PANEL_DARK, radius=12)
        countries = self._filtered_countries(state)
        visible_names = {country.name for country in countries}
        if countries and self.selected_country_name not in visible_names:
            self.selected_country_name = countries[0].name
        visible = countries[self.country_scroll:self.country_scroll + 18]
        y = list_rect.y + 18
        for country in visible:
            active = country.name == self.selected_country_name
            row = pygame.Rect(list_rect.x + 16, y, list_rect.width - 32, 28)
            if active:
                pygame.draw.rect(screen, (77, 103, 135), row, border_radius=7)
            draw_flag(screen, pygame.Rect(row.x + 8, row.y + 5, 34, 18), country.flag_colors, self.assets.get_flag(country, (34, 18)))
            screen.blit(self.small_font.render(country.name, True, TEXT), (row.x + 52, row.y + 5))
            stat = f"{country.population:.1f}M | {tr('tabs.economy')} {country.economy} | {tr('tabs.army')} {country.army} | {tr('sort.technology')} {country.technology}"
            screen.blit(self.tiny_font.render(stat, True, MUTED), (row.x + 235, row.y + 7))
            self._add_button(row, "", lambda s, n=country.name: self._select_country(n), active=active, tooltip=country.name)
            y += 32

        selected = state.countries.get(self.selected_country_name) or (countries[0] if countries else None)
        if selected:
            self._draw_country_card(screen, state, selected)

    def _draw_country_card(self, screen: pygame.Surface, state, country) -> None:
        rect = pygame.Rect(720, 178, 632, 600)
        draw_soft_panel(screen, rect, PANEL, radius=14)
        draw_flag(screen, pygame.Rect(rect.x + 34, rect.y + 36, 82, 48), country.flag_colors, self.assets.get_flag(country, (82, 48)))
        screen.blit(self.title_font.render(country.name, True, TEXT), (rect.x + 134, rect.y + 34))
        screen.blit(self.small_font.render(country.continent or "World", True, ACCENT), (rect.x + 138, rect.y + 70))
        lines = [
            ("population", f"{tr('sort.population')}: {country.population:.1f}M"),
            ("economy", f"{tr('tabs.economy')}: {country.economy} | {tr('country_card.regional')} {country.regional_economy()}"),
            ("army", f"{tr('tabs.army')}: {country.army}"),
            ("technology", f"{tr('sort.technology')}: {country.technology}"),
            ("stability", f"{tr('sort.stability')}: {country.stability}"),
            ("government", f"{tr('country_card.capital')}: {country.capital}"),
            ("politics", f"{tr('country_card.leader')}: {country.leader}"),
            ("oil", f"{tr('country_card.resources')}: O{country.resources['oil']} F{country.resources['food']} M{country.resources['metal']}"),
        ]
        y = rect.y + 120
        for icon_name, line in lines:
            screen.blit(self.assets.get_icon(icon_name, (18, 18)), (rect.x + 38, y + 3))
            screen.blit(self.font.render(line, True, TEXT), (rect.x + 64, y))
            y += 32
        description = tr("country_select.description")
        self._draw_wrapped_on_screen(screen, description, pygame.Rect(rect.x + 38, y + 12, rect.width - 76, 90), self.small_font, MUTED)
        self._add_button(
            pygame.Rect(rect.x + 38, rect.bottom - 78, rect.width - 76, 46),
            tr("country_select.start"),
            lambda s, n=country.name: self._start_selected_country(s, n),
            active=True,
            icon="victory",
        )

    def _filtered_countries(self, state):
        query = self.country_search.lower().strip()
        countries = list(state.countries.values())
        if query:
            countries = [country for country in countries if query in country.name.lower()]
        if self.continent_filter != tr("country_select.all_continents"):
            countries = [country for country in countries if country.continent == self.continent_filter]
        sorters = {
            "Population": lambda c: c.population,
            "Economy": lambda c: c.economy + c.regional_economy(),
            "Military": lambda c: c.army,
            "Technology": lambda c: c.technology,
            "Stability": lambda c: c.stability,
        }
        countries.sort(key=sorters.get(self.country_sort, sorters["Population"]), reverse=True)
        return countries

    def _country_continents(self, state):
        return [tr("country_select.all_continents")] + sorted({country.continent for country in state.countries.values() if country.continent})

    def _cycle_continent(self, continents):
        try:
            index = continents.index(self.continent_filter)
        except ValueError:
            index = 0
        self.continent_filter = continents[(index + 1) % len(continents)]
        self.country_scroll = 0
        return None

    def _set_country_sort(self, sort_key: str):
        self.country_sort = sort_key
        self.country_scroll = 0
        return None

    def _select_country(self, name: str):
        self.selected_country_name = name
        return None

    def _start_selected_country(self, state, name: str):
        state.choose_player_country(name)
        self._set_mode("game")
        return None
