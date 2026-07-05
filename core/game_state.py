import random
from datetime import date, timedelta
from typing import Dict, List, Optional

from core.country_data import (
    BUILDING_COSTS,
    BUILDING_TYPES,
    LAW_OPTIONS,
    PARTIES,
    RESOURCES,
    UNIT_POWER,
    UNIT_TYPES,
    WEAPON_BATCHES,
    clamp,
)
from core.country_factory import create_initial_countries
from core.country_model import Country
from core.version import GAME_VERSION
from systems.armies import Army, create_initial_armies, sync_armies_to_countries, update_all_armies
from systems.events import LOVER_NAMES, SPOUSE_NAMES, maybe_add_child
from map.camera import MapCamera


MONTH_NAMES = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


from systems.economy import EconomyMixin
from systems.construction import ConstructionMixin
from systems.diplomacy import DiplomacyMixin
from systems.family import FamilyMixin
from systems.governance import GovernanceMixin
from systems.resources import ResourceMixin
from systems.save_state import SaveStateMixin
from systems.technology import TechnologyMixin
from systems.war import WarMixin
from systems.settings import DEFAULT_SETTINGS


class GameState(
    EconomyMixin,
    ConstructionMixin,
    DiplomacyMixin,
    FamilyMixin,
    GovernanceMixin,
    ResourceMixin,
    TechnologyMixin,
    WarMixin,
    SaveStateMixin,
):
    DAY_SECONDS = 0.45

    def __init__(self) -> None:
        self.countries: Dict[str, Country] = create_initial_countries()
        self.player_country_name: Optional[str] = None
        self.selected_target_name: Optional[str] = None
        self.current_tab = "Overview"
        self.date = date(2026, 1, 1)
        self.months_elapsed = 0
        self.speed = 0
        self.time_accumulator = 0.0
        self.active_wars: Dict[str, Dict[str, object]] = {}
        self.armies: List[Army] = []
        self.selected_army_id: Optional[str] = None
        self.camera = MapCamera()
        self.map_version = "natural-earth-110m"
        self.victory_goal: Optional[str] = None
        self.game_over = False
        self.game_over_reason = ""
        self.notifications: List[Dict[str, object]] = []
        self.settings: Dict[str, object] = {
            "sound": True,
            "autosave": False,
            "difficulty": "Normal",
        }
        self.settings.update(DEFAULT_SETTINGS)
        self.messages: List[str] = [
            "Choose a country on the map to begin.",
        ]
        self.armies = create_initial_armies(self.countries)
        self._seed_initial_wars()

    @property
    def player_country(self) -> Optional[Country]:
        if not self.player_country_name:
            return None
        return self.countries.get(self.player_country_name)

    @property
    def selected_target(self) -> Optional[Country]:
        if self.selected_target_name:
            return self.countries.get(self.selected_target_name)
        return None

    @property
    def current_year(self) -> int:
        return self.date.year

    @property
    def current_month_name(self) -> str:
        return MONTH_NAMES[self.date.month - 1]

    @property
    def calendar_label(self) -> str:
        return f"{self.current_month_name} {self.current_year} | Day {self.date.day}"

    def add_message(self, message: str) -> None:
        self.messages.append(message)
        self.messages = self.messages[-18:]

    def add_notification(self, title: str, body: str, pause: bool = True) -> None:
        self.notifications.append({"title": title, "body": body, "date": self.calendar_label})
        self.notifications = self.notifications[-5:]
        self.add_message(f"{title}: {body}")
        if pause:
            self.speed = 0

    def clear_notification(self) -> None:
        if self.notifications:
            self.notifications.pop(0)

    def sync_map_armies(self) -> None:
        self.armies = sync_armies_to_countries(self.armies, self.countries)

    def _seed_initial_wars(self) -> None:
        if "Russia" in self.countries and "Ukraine" in self.countries:
            self._start_war("Russia", "Ukraine", ai_initiated=True, silent=True)
            war = self.active_wars.get(self.war_id("Russia", "Ukraine"))
            if war:
                war["score"] = 12
                war["months"] = 3

    def choose_player_country(self, name: str) -> None:
        self.player_country_name = name
        self.selected_target_name = next((n for n in self.target_names() if n != name), None)
        self.speed = 1
        self.refresh_player_relations()
        country = self.countries[name]
        country.relation_to_player = 100
        if country.geo_polygons:
            self.camera.focus_lonlat(country.label_lon, country.label_lat, zoom=2.0)
        self.messages = [
            f"You now rule {country.name}. Capital: {country.capital}. Leader: {country.leader}.",
            f"v{GAME_VERSION}: GitHub preparation, stability fixes, lean saves, and army sync are active.",
        ]
        self.current_tab = "Overview"

    def refresh_player_relations(self) -> None:
        if not self.player_country_name:
            return
        for country in self.countries.values():
            if country.name == self.player_country_name:
                country.relation_to_player = 100
            else:
                country.relation_to_player = self.get_relation(country.name, self.player_country_name)

    def set_speed(self, speed: int) -> None:
        self.speed = speed
        self.add_message("Game paused." if speed == 0 else f"Speed set to x{speed}.")

    def tick(self, dt: float) -> None:
        self.camera.update(dt)
        update_all_armies(self.armies, dt * max(0, self.speed))
        if self.game_over or self.speed <= 0 or self.player_country_name is None:
            return
        self.time_accumulator += dt * self.speed
        while self.time_accumulator >= self.DAY_SECONDS:
            self.time_accumulator -= self.DAY_SECONDS
            self.advance_day()

    def advance_day(self) -> None:
        old_month = self.date.month
        self.date += timedelta(days=1)
        if self.date.month != old_month:
            self.process_month()

    def process_month(self) -> None:
        self.months_elapsed += 1
        for country in self.countries.values():
            produced = country.produce_resources()
            weapons = country.auto_produce_weapons()
            income = country.monthly_income()
            expenses = country.monthly_expenses()
            country.last_month_income = income
            country.last_month_expenses = expenses
            country.last_month_balance = income - expenses
            country.money += income - expenses
            if country.money < 0:
                deficit = abs(country.money)
                country.debt += deficit
                country.money = 0
                country.inflation = min(100.0, country.inflation + max(0.3, deficit / 700))
                country.stability = clamp(country.stability - 1, 0, 100)
            elif country.last_month_balance > 0:
                if country.debt > 0 and country.money > 300:
                    payment = min(country.debt, max(20, country.money // 12))
                    country.money -= payment
                    country.debt -= payment
                country.inflation = max(1.0, country.inflation - 0.12)

            if country.vassal_of and country.vassal_of in self.countries:
                tribute = min(country.money, max(5, int(income * 0.12)))
                country.money -= tribute
                self.countries[country.vassal_of].money += tribute

            drift = country.law_stability_drift()
            if drift > 0 and random.random() < 0.28:
                country.stability = clamp(country.stability + 1, 0, 100)
            elif drift < 0 and random.random() < 0.30:
                country.stability = clamp(country.stability - 1, 0, 100)

            if country.resources["food"] < 8 and random.random() < 0.30:
                country.stability = clamp(country.stability - 2, 0, 100)
                if country.name == self.player_country_name:
                    self.add_message("Resource warning: low food hurts stability.")

            if country.name == self.player_country_name and self.date.month in [1, 4, 7, 10]:
                self.add_message(
                    f"Quarter report: produced O{produced['oil']} F{produced['food']} M{produced['metal']}, weapons I{weapons['infantry']} T{weapons['tanks']} A{weapons['artillery']} Air{weapons['aircraft']}, balance {country.last_month_balance}."
                )

        self.process_active_wars()
        self.process_internal_problems()

        if self.date.month == 1:
            self.process_elections()

        from ai import run_monthly_ai
        from systems.events import apply_random_event, process_family_month

        run_monthly_ai(self)
        process_family_month(self)
        apply_random_event(self)
        self.sync_map_armies()
        self.refresh_player_relations()
        self.check_victory_and_game_over()
        if self.settings.get("autosave") and self.player_country_name and self.date.month in [1, 7]:
            try:
                from systems.save_load import save_game

                save_game(self)
                self.add_message("Autosave completed.")
            except Exception as exc:
                self.add_message(f"Autosave failed: {exc}")

    def country_names(self) -> List[str]:
        return list(self.countries.keys())

    def target_names(self) -> List[str]:
        priority = [name for name in self.countries if self.countries[name].is_core_country and name != self.player_country_name]
        if self.selected_target_name and self.selected_target_name not in priority and self.selected_target_name != self.player_country_name:
            priority.insert(0, self.selected_target_name)
        if len(priority) < 18:
            for name in self.countries:
                if name != self.player_country_name and name not in priority:
                    priority.append(name)
                if len(priority) >= 18:
                    break
        return priority[:18]

    def get_relation(self, a: str, b: str) -> int:
        if a == b:
            return 100
        return int(self.countries[a].relations.get(b, 0))

    def set_relation(self, a: str, b: str, value: int) -> None:
        value = clamp(value, -100, 100)
        if a == b:
            return
        self.countries[a].relations[b] = value
        self.countries[b].relations[a] = value
        self.refresh_player_relations()

    def add_relation_delta(self, a: str, b: str, delta: int) -> None:
        self.set_relation(a, b, self.get_relation(a, b) + delta)

    def make_alliance(self, a: str, b: str, announce: bool = True) -> bool:
        if a == b:
            return False
        self.countries[a].allies.add(b)
        self.countries[b].allies.add(a)
        if self.war_id(a, b) not in self.active_wars:
            self.countries[a].wars.discard(b)
            self.countries[b].wars.discard(a)
        self.set_relation(a, b, max(65, self.get_relation(a, b)))
        if announce:
            self.add_message(f"Alliance formed: {a} and {b}.")
        return True

    def break_alliance(self, a: str, b: str) -> None:
        self.countries[a].allies.discard(b)
        self.countries[b].allies.discard(a)

