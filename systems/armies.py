from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

from core.utils import stable_hash


GENERALS = [
    "Adams", "Volkov", "Keller", "Dubois", "Tanaka", "Rao", "Silva", "Yildiz",
    "Nowak", "Miller", "Chen", "Sato", "Morgan", "Costa", "Singh", "Hart",
]


@dataclass
class Army:
    army_id: str
    country_name: str
    lon: float
    lat: float
    size: int
    unit_type: str = "mixed"
    general: str = "General Staff"
    supply: int = 100
    morale: int = 72
    target_lon: Optional[float] = None
    target_lat: Optional[float] = None
    stance: str = "defend"

    def to_dict(self) -> Dict[str, object]:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Army":
        return cls(
            army_id=str(data["army_id"]),
            country_name=str(data["country_name"]),
            lon=float(data["lon"]),
            lat=float(data["lat"]),
            size=int(data["size"]),
            unit_type=str(data.get("unit_type", "mixed")),
            general=str(data.get("general", "General Staff")),
            supply=int(data.get("supply", 100)),
            morale=int(data.get("morale", 72)),
            target_lon=None if data.get("target_lon") is None else float(data.get("target_lon")),
            target_lat=None if data.get("target_lat") is None else float(data.get("target_lat")),
            stance=str(data.get("stance", "defend")),
        )

    def set_target(self, lon: float, lat: float, stance: str = "attack") -> None:
        self.target_lon = lon
        self.target_lat = lat
        self.stance = stance

    def clear_target(self) -> None:
        self.target_lon = None
        self.target_lat = None
        self.stance = "defend"

    def update(self, dt: float) -> None:
        if self.target_lon is None or self.target_lat is None:
            self.morale = min(100, self.morale + 1 if random.random() < 0.02 else self.morale)
            return
        dx = self.target_lon - self.lon
        dy = self.target_lat - self.lat
        distance = math.hypot(dx, dy)
        if distance < 0.12:
            self.lon = self.target_lon
            self.lat = self.target_lat
            if self.stance == "retreat":
                self.clear_target()
            return
        speed = {"attack": 2.2, "defend": 1.1, "retreat": 3.0}.get(self.stance, 1.7)
        step = min(distance, speed * dt)
        self.lon += dx / distance * step
        self.lat += dy / distance * step
        if self.stance == "attack":
            self.supply = max(0, self.supply - (1 if random.random() < 0.04 else 0))
            self.morale = max(15, self.morale - (1 if self.supply < 35 and random.random() < 0.05 else 0))


def create_initial_armies(countries: Dict[str, object]) -> List[Army]:
    armies: List[Army] = []
    for country in countries.values():
        army_strength = int(getattr(country, "army", 0))
        count = desired_army_count(army_strength)
        for index in range(count):
            armies.append(make_army(country, index, count, army_strength))
    return armies


def desired_army_count(army_strength: int) -> int:
    if army_strength < 80:
        return 0
    if army_strength > 1200:
        return 3
    if army_strength > 550:
        return 2
    return 1


def make_army(country: object, index: int, count: int, army_strength: int) -> Army:
    offset = (index - (count - 1) / 2) * 2.2
    name = getattr(country, "name", "Unknown")
    return Army(
        army_id=f"{getattr(country, 'iso_a3', name) or name}-{index + 1}",
        country_name=name,
        lon=float(getattr(country, "capital_lon", getattr(country, "label_lon", 0.0))) + offset,
        lat=float(getattr(country, "capital_lat", getattr(country, "label_lat", 0.0))) + offset * 0.35,
        size=max(40, army_strength // max(1, count)),
        unit_type=dominant_unit(country),
        general=f"Gen. {GENERALS[stable_hash(name + str(index)) % len(GENERALS)]}",
        morale=68 + stable_hash(name) % 20,
    )


def sync_armies_to_countries(armies: List[Army], countries: Dict[str, object]) -> List[Army]:
    """Keep map army markers aligned with each country's unit-derived strength."""
    synced: List[Army] = []
    by_country = {name: armies_for(armies, name) for name in countries}
    for country in countries.values():
        name = getattr(country, "name", "")
        if hasattr(country, "sync_army_from_units"):
            country.sync_army_from_units()
        army_strength = int(getattr(country, "army", 0))
        desired = desired_army_count(army_strength)
        existing = by_country.get(name, [])[:desired]
        while len(existing) < desired:
            existing.append(make_army(country, len(existing), desired, army_strength))
        if desired:
            size = max(1, army_strength // desired)
            for index, army in enumerate(existing):
                army.size = size if index < desired - 1 else max(1, army_strength - size * (desired - 1))
                army.unit_type = dominant_unit(country)
                synced.append(army)
    return synced


def dominant_unit(country: object) -> str:
    units = dict(getattr(country, "units", {}))
    if not units:
        return "mixed"
    return max(units, key=lambda key: units.get(key, 0))


def armies_for(armies: Iterable[Army], country_name: str) -> List[Army]:
    return [army for army in armies if army.country_name == country_name]


def order_attack(armies: Iterable[Army], attacker: object, defender: object) -> None:
    defender_lon = float(getattr(defender, "capital_lon", getattr(defender, "label_lon", 0.0)))
    defender_lat = float(getattr(defender, "capital_lat", getattr(defender, "label_lat", 0.0)))
    for index, army in enumerate(armies_for(armies, getattr(attacker, "name", ""))):
        army.set_target(defender_lon + index * 1.8, defender_lat - index * 0.8, "attack")


def order_defense(armies: Iterable[Army], country: object) -> None:
    lon = float(getattr(country, "capital_lon", getattr(country, "label_lon", 0.0)))
    lat = float(getattr(country, "capital_lat", getattr(country, "label_lat", 0.0)))
    for index, army in enumerate(armies_for(armies, getattr(country, "name", ""))):
        army.set_target(lon + index * 1.2, lat + index * 0.8, "defend")


def order_retreat(armies: Iterable[Army], country: object) -> None:
    lon = float(getattr(country, "capital_lon", getattr(country, "label_lon", 0.0)))
    lat = float(getattr(country, "capital_lat", getattr(country, "label_lat", 0.0)))
    for army in armies_for(armies, getattr(country, "name", "")):
        army.set_target(lon, lat, "retreat")


def update_all_armies(armies: Iterable[Army], dt: float) -> None:
    for army in armies:
        army.update(dt)


def average_morale(armies: Iterable[Army], country_name: str) -> int:
    country_armies = armies_for(armies, country_name)
    if not country_armies:
        return 50
    return int(sum(army.morale for army in country_armies) / len(country_armies))


def average_supply(armies: Iterable[Army], country_name: str) -> int:
    country_armies = armies_for(armies, country_name)
    if not country_armies:
        return 50
    return int(sum(army.supply for army in country_armies) / len(country_armies))
