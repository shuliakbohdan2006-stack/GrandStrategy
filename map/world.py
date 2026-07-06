from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from core.country_data import clamp, province
from core.country_model import Country
from core.utils import stable_hash


WORLD_WIDTH = 4096
WORLD_HEIGHT = 2048
GEOJSON_PATH = Path(__file__).resolve().parent.parent / "data" / "ne_110m_admin_0_countries.geojson"

CORE_COUNTRIES = [
    "USA", "Canada", "Mexico", "Brazil", "Argentina", "UK", "France", "Germany",
    "Italy", "Spain", "Poland", "Ukraine", "Russia", "Turkey", "Egypt", "India",
    "China", "Japan", "South Korea", "Australia",
]

NAME_ALIASES = {
    "United States of America": "USA",
    "United Kingdom": "UK",
    "South Korea": "South Korea",
}

CAPITALS = {
    "USA": ("Washington, D.C.", -77.0369, 38.9072),
    "Canada": ("Ottawa", -75.6972, 45.4215),
    "Mexico": ("Mexico City", -99.1332, 19.4326),
    "Brazil": ("Brasilia", -47.8825, -15.7942),
    "Argentina": ("Buenos Aires", -58.3816, -34.6037),
    "UK": ("London", -0.1276, 51.5072),
    "France": ("Paris", 2.3522, 48.8566),
    "Germany": ("Berlin", 13.4050, 52.5200),
    "Italy": ("Rome", 12.4964, 41.9028),
    "Spain": ("Madrid", -3.7038, 40.4168),
    "Poland": ("Warsaw", 21.0122, 52.2297),
    "Ukraine": ("Kyiv", 30.5234, 50.4501),
    "Russia": ("Moscow", 37.6173, 55.7558),
    "Turkey": ("Ankara", 32.8597, 39.9334),
    "Egypt": ("Cairo", 31.2357, 30.0444),
    "India": ("New Delhi", 77.2090, 28.6139),
    "China": ("Beijing", 116.4074, 39.9042),
    "Japan": ("Tokyo", 139.6503, 35.6762),
    "South Korea": ("Seoul", 126.9780, 37.5665),
    "Australia": ("Canberra", 149.1300, -35.2809),
}

LEADERS = {
    "USA": "Donald J. Trump",
    "Canada": "Mark Carney",
    "Mexico": "Claudia Sheinbaum",
    "Brazil": "Luiz Inacio Lula da Silva",
    "Argentina": "Javier Milei",
    "UK": "Keir Starmer",
    "France": "Emmanuel Macron",
    "Germany": "Friedrich Merz",
    "Italy": "Giorgia Meloni",
    "Spain": "Pedro Sanchez",
    "Poland": "Donald Tusk",
    "Ukraine": "Volodymyr Zelenskyy",
    "Russia": "Vladimir Putin",
    "Turkey": "Recep Tayyip Erdogan",
    "Egypt": "Abdel Fattah el-Sisi",
    "India": "Narendra Modi",
    "China": "Xi Jinping",
    "Japan": "Sanae Takaichi",
    "South Korea": "Lee Jae-myung",
    "Australia": "Anthony Albanese",
}

AUTHORITARIAN = {"Russia", "China", "Egypt", "Iran", "North Korea", "Saudi Arabia", "Belarus"}

FLAG_COLORS = {
    "USA": [(59, 96, 165), (235, 235, 235), (184, 47, 54)],
    "Canada": [(210, 43, 52), (244, 244, 244), (210, 43, 52)],
    "Mexico": [(20, 126, 76), (242, 242, 242), (186, 55, 52)],
    "Brazil": [(42, 155, 86), (240, 205, 64), (43, 89, 167)],
    "Argentina": [(112, 176, 220), (245, 245, 245), (112, 176, 220)],
    "UK": [(35, 55, 130), (245, 245, 245), (190, 45, 60)],
    "France": [(35, 82, 156), (245, 245, 245), (198, 45, 55)],
    "Germany": [(30, 32, 35), (198, 45, 55), (226, 178, 62)],
    "Italy": [(42, 145, 84), (245, 245, 245), (198, 45, 55)],
    "Spain": [(196, 48, 54), (226, 178, 62), (196, 48, 54)],
    "Poland": [(244, 244, 244), (214, 54, 78), (214, 54, 78)],
    "Ukraine": [(68, 119, 205), (232, 199, 67), (232, 199, 67)],
    "Russia": [(244, 244, 244), (64, 90, 180), (190, 52, 60)],
    "Turkey": [(198, 42, 52), (198, 42, 52), (244, 244, 244)],
    "Egypt": [(196, 45, 52), (244, 244, 244), (32, 34, 38)],
    "India": [(232, 143, 55), (244, 244, 244), (60, 145, 82)],
    "China": [(204, 64, 56), (226, 178, 62), (204, 64, 56)],
    "Japan": [(244, 244, 244), (204, 64, 88), (244, 244, 244)],
    "South Korea": [(244, 244, 244), (74, 98, 176), (204, 64, 68)],
    "Australia": [(35, 63, 136), (244, 244, 244), (196, 45, 52)],
}


def create_world_countries(existing: Optional[Dict[str, Country]] = None) -> Dict[str, Country]:
    if not GEOJSON_PATH.exists():
        return existing or {}
    features = json.loads(GEOJSON_PATH.read_text(encoding="utf-8"))["features"]
    countries: Dict[str, Country] = {}
    for feature in features:
        props = dict(feature.get("properties", {}))
        name = canonical_name(props)
        polygons = extract_polygons(feature.get("geometry", {}))
        if not name or not polygons:
            continue
        legacy = (existing or {}).get(name)
        countries[name] = build_country_from_feature(name, props, polygons, legacy)

    if existing:
        for name, legacy in existing.items():
            if name not in countries:
                countries[name] = legacy

    initialize_relations(countries)
    ensure_default_diplomacy(countries)
    return countries


def ensure_world_metadata(countries: Dict[str, Country]) -> Dict[str, Country]:
    world = create_world_countries(countries)
    for name, country in countries.items():
        if name in world:
            fresh = world[name]
            country.iso_a3 = fresh.iso_a3
            country.iso_a2 = fresh.iso_a2
            country.continent = fresh.continent
            country.shape = fresh.shape
            country.geo_polygons = fresh.geo_polygons
            country.label_lon = fresh.label_lon
            country.label_lat = fresh.label_lat
            country.capital_lon = fresh.capital_lon
            country.capital_lat = fresh.capital_lat
            country.flag_colors = fresh.flag_colors
            country.is_core_country = fresh.is_core_country
    countries.update({name: country for name, country in world.items() if name not in countries})
    initialize_relations(countries)
    return countries

def canonical_name(props: Dict[str, object]) -> str:
    admin = str(props.get("ADMIN") or props.get("NAME") or "")
    return NAME_ALIASES.get(admin, admin)

def extract_polygons(geometry: Dict[str, object]) -> List[List[Tuple[float, float]]]:
    geom_type = geometry.get("type")
    coords = geometry.get("coordinates", [])
    rings: List[List[Tuple[float, float]]] = []
    if geom_type == "Polygon":
        for polygon in [coords]:
            add_exterior_ring(rings, polygon)
    elif geom_type == "MultiPolygon":
        for polygon in coords:  # type: ignore[assignment]
            add_exterior_ring(rings, polygon)
    return [ring for ring in rings if len(ring) >= 3]


def add_exterior_ring(rings: List[List[Tuple[float, float]]], polygon: object) -> None:
    if not polygon:
        return
    exterior = list(polygon[0])  # type: ignore[index]
    ring = [(float(point[0]), float(point[1])) for point in exterior]
    rings.append(ring)


def build_country_from_feature(name: str, props: Dict[str, object], polygons: List[List[Tuple[float, float]]], legacy: Optional[Country]) -> Country:
    pop = max(0.4, float(props.get("POP_EST") or 1_000_000) / 1_000_000)
    gdp = max(300.0, float(props.get("GDP_MD") or 300.0))
    economy = clamp(int(math.sqrt(gdp) / 38) + 2, 2, 12)
    money = clamp(int(260 + math.sqrt(gdp) * 11), 180, 1800)
    army = clamp(int(pop * 2.2 + math.sqrt(gdp) * 2.4), 45, 1850)
    tech = clamp(int(math.log10(gdp + 10) * 1.55), 2, 8)
    influence = clamp(int(math.sqrt(pop) * 4 + math.sqrt(gdp) / 12), 12, 75)
    label_lon, label_lat = polygon_centroid(largest_ring(polygons))
    capital, cap_lon, cap_lat = capital_for(name, label_lon, label_lat)
    resources = resource_profile(name, str(props.get("CONTINENT", "")), pop, gdp)
    if legacy:
        money, army, economy, tech = legacy.money, legacy.army, legacy.economy, legacy.technology
        influence, resources = legacy.influence, legacy.resources
    color = country_color(name, str(props.get("CONTINENT", "")))
    country = Country(
        name=name,
        capital=capital,
        population=round(pop, 1),
        money=money,
        army=army,
        stability=legacy.stability if legacy else default_stability(name),
        technology=tech,
        relation_to_player=legacy.relation_to_player if legacy else 0,
        leader=legacy.leader if legacy else LEADERS.get(name, f"{name} Council"),
        color=legacy.color if legacy else color,
        shape=legacy.shape if legacy else legacy_shape(polygons),
        iso_a3=str(props.get("ISO_A3") or props.get("ADM0_A3") or ""),
        iso_a2=str(props.get("ISO_A2") or ""),
        continent=str(props.get("CONTINENT", "")),
        geo_polygons=polygons,
        label_lon=label_lon,
        label_lat=label_lat,
        capital_lon=cap_lon,
        capital_lat=cap_lat,
        flag_colors=FLAG_COLORS.get(name, default_flag(color)),
        is_core_country=name in CORE_COUNTRIES,
        economy=economy,
        influence=influence,
        party=legacy.party if legacy else default_party(name),
        government_type=legacy.government_type if legacy else ("Authoritarian" if name in AUTHORITARIAN else "Democracy"),
        next_election_year=legacy.next_election_year if legacy else 2028 + (stable_hash(name) % 4),
        leader_pool=legacy.leader_pool if legacy else leader_pool(name),
        laws=legacy.laws if legacy else {},
        resources=resources,
        provinces=legacy.provinces if legacy else generated_provinces(name, pop, economy, resources, polygons),
    )
    country.recalculate_from_provinces()
    country.sync_army_from_units()
    return country


def initialize_relations(countries: Dict[str, Country]) -> None:
    names = list(countries)
    for country in countries.values():
        for name in names:
            if name != country.name:
                country.relations.setdefault(name, relation_baseline(country, countries[name]))


def ensure_default_diplomacy(countries: Dict[str, Country]) -> None:
    def rel(a: str, b: str, value: int) -> None:
        if a in countries and b in countries:
            countries[a].relations[b] = value
            countries[b].relations[a] = value

    for ally in ["Canada", "UK", "France", "Germany", "Italy", "Spain", "Poland", "Japan", "South Korea", "Australia"]:
        rel("USA", ally, 65)
        if "USA" in countries and ally in countries:
            countries["USA"].allies.add(ally)
            countries[ally].allies.add("USA")
    for pair in [("Germany", "France"), ("Germany", "Poland"), ("France", "UK"), ("Italy", "Germany"), ("Spain", "France")]:
        rel(pair[0], pair[1], 68)
        if pair[0] in countries and pair[1] in countries:
            countries[pair[0]].allies.add(pair[1])
            countries[pair[1]].allies.add(pair[0])
    for a, b, value in [
        ("Ukraine", "Russia", -88), ("USA", "Russia", -62), ("USA", "China", -36),
        ("China", "Japan", -42), ("China", "India", -28), ("India", "Pakistan", -64),
        ("Turkey", "Russia", -10), ("Brazil", "Argentina", 22),
    ]:
        rel(a, b, value)
    if "Ukraine" in countries and "Russia" in countries:
        countries["Ukraine"].wars.add("Russia")
        countries["Russia"].wars.add("Ukraine")


def relation_baseline(a: Country, b: Country) -> int:
    score = 0
    if a.continent and a.continent == b.continent:
        score += 8
    if a.government_type == b.government_type:
        score += 5
    score += clamp(int((a.stability + b.stability - 120) / 8), -8, 8)
    return clamp(score, -35, 45)


def lonlat_to_world(lon: float, lat: float) -> Tuple[float, float]:
    return (lon + 180.0) / 360.0 * WORLD_WIDTH, (90.0 - lat) / 180.0 * WORLD_HEIGHT


def world_to_lonlat(x: float, y: float) -> Tuple[float, float]:
    return x / WORLD_WIDTH * 360.0 - 180.0, 90.0 - y / WORLD_HEIGHT * 180.0


def point_in_country(country: Country, lon: float, lat: float) -> bool:
    return any(point_in_ring((lon, lat), ring) for ring in country.geo_polygons)


def point_in_ring(point: Tuple[float, float], ring: List[Tuple[float, float]]) -> bool:
    x, y = point
    inside = False
    j = len(ring) - 1
    for i, (xi, yi) in enumerate(ring):
        xj, yj = ring[j]
        if (yi > y) != (yj > y):
            denominator = yj - yi
            if abs(denominator) < 0.000001:
                j = i
                continue
            edge_x = (xj - xi) * (y - yi) / denominator + xi
            if x < edge_x:
                inside = not inside
        j = i
    return inside


def find_country_at(countries: Iterable[Country], lon: float, lat: float) -> Optional[Country]:
    matches = [country for country in countries if country.geo_polygons and point_in_country(country, lon, lat)]
    if not matches:
        return None
    return min(matches, key=lambda country: country_area(country.geo_polygons))


def country_area(polygons: List[List[Tuple[float, float]]]) -> float:
    return sum(abs(ring_area(ring)) for ring in polygons)


def ring_area(ring: List[Tuple[float, float]]) -> float:
    area = 0.0
    for index, (x1, y1) in enumerate(ring):
        x2, y2 = ring[(index + 1) % len(ring)]
        area += x1 * y2 - x2 * y1
    return area / 2.0


def largest_ring(polygons: List[List[Tuple[float, float]]]) -> List[Tuple[float, float]]:
    return max(polygons, key=lambda ring: abs(ring_area(ring)))


def polygon_centroid(ring: List[Tuple[float, float]]) -> Tuple[float, float]:
    if not ring:
        return 0.0, 0.0
    return sum(point[0] for point in ring) / len(ring), sum(point[1] for point in ring) / len(ring)


def legacy_shape(polygons: List[List[Tuple[float, float]]]) -> List[Tuple[int, int]]:
    ring = largest_ring(polygons)
    points = []
    for lon, lat in ring[:: max(1, len(ring) // 18)]:
        x, y = lonlat_to_world(lon, lat)
        points.append((int(x / WORLD_WIDTH * 820), int(y / WORLD_HEIGHT * 515)))
    return points[:24] or [(0, 0), (10, 0), (10, 10), (0, 10)]


def country_color(name: str, continent: str) -> Tuple[int, int, int]:
    palettes = {
        "North America": (73, 130, 190), "South America": (77, 161, 100),
        "Europe": (96, 150, 128), "Asia": (202, 92, 76),
        "Africa": (210, 153, 72), "Oceania": (136, 105, 176),
    }
    base = palettes.get(continent, (122, 142, 160))
    jitter = stable_hash(name) % 36 - 18
    return tuple(clamp(channel + jitter, 45, 220) for channel in base)


def default_flag(color: Tuple[int, int, int]) -> List[Tuple[int, int, int]]:
    return [(238, 238, 238), color, (32, 39, 46)]


def capital_for(name: str, lon: float, lat: float) -> Tuple[str, float, float]:
    if name in CAPITALS:
        capital, cap_lon, cap_lat = CAPITALS[name]
        return capital, cap_lon, cap_lat
    return f"{name} Capital", lon, lat


def default_party(name: str) -> str:
    if name in {"China", "Brazil"}:
        return "Socialist"
    if name in {"Russia", "Turkey", "India", "Poland"}:
        return "Nationalist"
    if name in {"USA", "UK", "Germany", "Italy"}:
        return "Conservative"
    return "Liberal"


def default_stability(name: str) -> int:
    return {"Ukraine": 58, "Russia": 62, "Egypt": 59, "Argentina": 61}.get(name, 66 + stable_hash(name) % 13)


def leader_pool(name: str) -> List[str]:
    leader = LEADERS.get(name, f"{name} Council")
    return [leader, f"{name} Reform Bloc", f"{name} National Cabinet"]


def resource_profile(name: str, continent: str, pop: float, gdp: float) -> Dict[str, int]:
    oil = 24 + int(pop % 20)
    food = 35 + int(math.sqrt(pop) * 8)
    metal = 28 + int(math.sqrt(gdp) / 18)
    if continent in {"North America", "South America", "Oceania"}:
        food += 20
    if continent in {"Asia", "Europe"}:
        metal += 14
    if name in {"USA", "Canada", "Russia", "Brazil", "Mexico", "China", "Australia", "Egypt"}:
        oil += 35
    if name in {"India", "China", "USA", "Brazil", "Argentina", "Ukraine", "France"}:
        food += 30
    if name in {"China", "Russia", "Australia", "Germany", "India", "Poland"}:
        metal += 28
    return {"oil": clamp(oil, 8, 160), "food": clamp(food, 20, 180), "metal": clamp(metal, 18, 160)}


def generated_provinces(name: str, pop: float, economy: int, resources: Dict[str, int], polygons: List[List[Tuple[float, float]]]) -> List[Dict[str, object]]:
    count = clamp(2 + int(pop // 85), 2, 6)
    labels = ["North", "South", "Central", "Coastal", "Interior", "Frontier"]
    provinces = []
    for index in range(count):
        factor = 1.0 / count
        provinces.append(
            province(
                f"{name} {labels[index]}",
                round(pop * factor, 1),
                max(2, int(economy * factor + 2)),
                max(1, resources["oil"] // (count * 5)),
                max(2, resources["food"] // (count * 5)),
                max(1, resources["metal"] // (count * 5)),
            )
        )
    return provinces
