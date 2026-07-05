from __future__ import annotations

from typing import Dict, List, Tuple

from core.country_model import Country
from core.country_data import province


def rect_poly(x: int, y: int, w: int, h: int) -> List[Tuple[int, int]]:
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def create_initial_countries() -> Dict[str, Country]:
    countries = {
        "USA": Country(
            "USA", "Washington, D.C.", 334, 1500, 1350, 72, 7, 0,
            "Donald J. Trump", (66, 120, 190), [(35, 185), (65, 170), (125, 172), (175, 190), (195, 230), (160, 257), (90, 255), (45, 235)],
            economy=10, influence=65, territory_points=22, party="Conservative",
            government_type="Democracy", next_election_year=2028,
            leader_pool=["Donald J. Trump", "Alex Morgan", "Patricia Hale", "Samuel Reed"],
            resources={"oil": 80, "food": 90, "metal": 70},
            provinces=[
                province("Pacific Coast", 53, 8, 12, 14, 8),
                province("Great Plains", 61, 6, 8, 24, 10),
                province("East Coast", 92, 9, 6, 16, 8),
                province("Texas Gulf", 47, 7, 20, 10, 12),
                province("Midwest", 81, 7, 5, 20, 18),
            ],
        ),
        "Germany": Country(
            "Germany", "Berlin", 84, 850, 310, 80, 7, 0,
            "Friedrich Merz", (80, 155, 105), [(390, 210), (430, 200), (465, 218), (458, 257), (410, 262), (392, 240)],
            economy=9, influence=40, territory_points=8, party="Conservative",
            government_type="Democracy", next_election_year=2029,
            leader_pool=["Friedrich Merz", "Klara Weiss", "Jonas Keller", "Marta Vogel"],
            resources={"oil": 28, "food": 52, "metal": 65},
            provinces=[
                province("Bavaria", 13, 7, 1, 8, 12),
                province("Rhine", 18, 8, 2, 7, 18),
                province("Prussia", 22, 7, 1, 10, 12),
                province("Saxony", 31, 6, 1, 8, 14),
            ],
        ),
        "France": Country(
            "France", "Paris", 68, 780, 290, 70, 7, 0,
            "Emmanuel Macron", (50, 110, 180), [(355, 270), (402, 255), (445, 278), (435, 330), (382, 330), (352, 305)],
            economy=8, influence=38, territory_points=9, party="Liberal",
            government_type="Democracy", next_election_year=2027,
            leader_pool=["Emmanuel Macron", "Claire Dubois", "Henri Marchand", "Luc Martin"],
            resources={"oil": 24, "food": 68, "metal": 42},
            provinces=[
                province("Ile-de-France", 12, 8, 1, 6, 5),
                province("Normandy", 8, 5, 2, 14, 6),
                province("Provence", 12, 6, 2, 10, 4),
                province("Aquitaine", 36, 6, 1, 16, 7),
            ],
        ),
        "Ukraine": Country(
            "Ukraine", "Kyiv", 37, 420, 520, 58, 5, 0,
            "Volodymyr Zelenskyy", (220, 190, 70), [(488, 220), (565, 215), (590, 238), (575, 273), (505, 272), (488, 250)],
            economy=5, influence=27, territory_points=9, party="Liberal",
            government_type="Democracy", next_election_year=2029,
            leader_pool=["Volodymyr Zelenskyy", "Oksana Levchenko", "Danylo Kovalenko"],
            resources={"oil": 20, "food": 74, "metal": 52},
            provinces=[
                province("Kyiv", 8, 5, 1, 10, 5),
                province("Dnipro", 12, 5, 3, 12, 18),
                province("Black Sea Coast", 9, 4, 4, 14, 6),
                province("Galicia", 8, 4, 1, 12, 5),
            ],
        ),
        "Russia": Country(
            "Russia", "Moscow", 144, 1050, 1250, 62, 6, 0,
            "Vladimir Putin", (175, 75, 75), [(575, 105), (650, 75), (780, 80), (810, 130), (792, 200), (620, 205), (570, 165)],
            economy=8, influence=56, territory_points=28, party="Nationalist",
            government_type="Authoritarian", next_election_year=2030,
            leader_pool=["Vladimir Putin", "Sergei Volkov", "Nikolai Sokolov"],
            resources={"oil": 130, "food": 62, "metal": 100},
            provinces=[
                province("Moscow", 22, 7, 3, 8, 8),
                province("Volga", 25, 6, 18, 16, 18),
                province("Ural", 16, 6, 20, 8, 30),
                province("Siberia", 28, 5, 38, 8, 28),
                province("Far East", 12, 4, 18, 4, 12),
                province("South Russia", 41, 6, 14, 18, 10),
            ],
        ),
        "China": Country(
            "China", "Beijing", 1410, 1650, 1650, 76, 8, 0,
            "Xi Jinping", (205, 75, 65), [(675, 280), (730, 250), (815, 280), (805, 365), (740, 385), (680, 350)],
            economy=11, influence=64, territory_points=24, party="Socialist",
            government_type="Authoritarian", next_election_year=2031,
            leader_pool=["Xi Jinping", "Li Wei", "Chen Rong"],
            resources={"oil": 75, "food": 130, "metal": 140},
            provinces=[
                province("North China", 210, 9, 10, 26, 22),
                province("Yangtze Delta", 260, 11, 8, 24, 28),
                province("South Coast", 190, 10, 6, 18, 20),
                province("Sichuan", 150, 8, 6, 20, 18),
                province("Xinjiang", 70, 6, 18, 8, 18),
                province("Central China", 530, 9, 8, 28, 34),
            ],
        ),
        "Japan": Country(
            "Japan", "Tokyo", 125, 920, 260, 78, 8, 0,
            "Shigeru Ishiba", (200, 105, 145), [(770, 285), (805, 305), (800, 380), (770, 365), (760, 315)],
            economy=9, influence=35, territory_points=7, party="Liberal",
            government_type="Democracy", next_election_year=2028,
            leader_pool=["Shigeru Ishiba", "Aiko Tanaka", "Ren Sato"],
            resources={"oil": 18, "food": 48, "metal": 38},
            provinces=[
                province("Kanto", 44, 9, 1, 8, 8),
                province("Kansai", 23, 8, 1, 8, 8),
                province("Hokkaido", 5, 4, 1, 12, 6),
                province("Kyushu", 53, 7, 1, 10, 8),
            ],
        ),
        "Brazil": Country(
            "Brazil", "Brasilia", 216, 720, 360, 66, 5, 0,
            "Luiz Inacio Lula da Silva", (70, 160, 95), [(230, 365), (285, 340), (360, 380), (372, 455), (320, 500), (250, 470), (215, 420)],
            economy=7, influence=34, territory_points=18, party="Socialist",
            government_type="Democracy", next_election_year=2026,
            leader_pool=["Luiz Inacio Lula da Silva", "Marina Costa", "Rafael Alves"],
            resources={"oil": 55, "food": 110, "metal": 50},
            provinces=[
                province("Amazonas", 18, 4, 8, 18, 12),
                province("Sao Paulo", 46, 8, 4, 18, 14),
                province("Minas Gerais", 22, 6, 3, 12, 18),
                province("Northeast", 55, 5, 5, 28, 6),
                province("South Brazil", 75, 6, 5, 26, 8),
            ],
        ),
        "India": Country(
            "India", "New Delhi", 1430, 1180, 1450, 68, 6, 0,
            "Narendra Modi", (235, 145, 70), [(590, 360), (650, 340), (710, 388), (690, 455), (632, 470), (585, 420)],
            economy=9, influence=48, territory_points=20, party="Nationalist",
            government_type="Democracy", next_election_year=2029,
            leader_pool=["Narendra Modi", "Arjun Mehta", "Priya Rao"],
            resources={"oil": 45, "food": 140, "metal": 85},
            provinces=[
                province("Delhi Plain", 210, 8, 5, 28, 14),
                province("Mumbai Coast", 150, 8, 6, 18, 14),
                province("Bengal", 260, 7, 4, 32, 10),
                province("Deccan", 330, 7, 5, 30, 22),
                province("South India", 480, 8, 4, 34, 16),
            ],
        ),
        "Turkey": Country(
            "Turkey", "Ankara", 86, 640, 450, 61, 5, 0,
            "Recep Tayyip Erdogan", (80, 145, 160), [(506, 306), (570, 296), (608, 325), (590, 360), (525, 360), (498, 332)],
            economy=6, influence=31, territory_points=10, party="Nationalist",
            government_type="Democracy", next_election_year=2028,
            leader_pool=["Recep Tayyip Erdogan", "Kemal Yildiz", "Aylin Kaya"],
            resources={"oil": 32, "food": 64, "metal": 46},
            provinces=[
                province("Anatolia", 36, 5, 3, 18, 10),
                province("Marmara", 25, 6, 2, 10, 8),
                province("Aegean", 14, 5, 1, 12, 6),
                province("Eastern Turkey", 11, 4, 5, 8, 12),
            ],
        ),
    }

    try:
        from map.world import create_world_countries

        world_countries = create_world_countries(countries)
        if world_countries:
            return world_countries
    except Exception:
        pass

    for country in countries.values():
        country.recalculate_from_provinces()
        for other in countries.values():
            if country.name != other.name:
                country.relations[other.name] = 0

    def rel(a: str, b: str, value: int) -> None:
        countries[a].relations[b] = value
        countries[b].relations[a] = value

    rel("USA", "Germany", 62)
    rel("USA", "France", 55)
    rel("USA", "Japan", 66)
    rel("USA", "Ukraine", 62)
    rel("USA", "China", -32)
    rel("USA", "Russia", -58)
    rel("Germany", "France", 72)
    rel("Germany", "Ukraine", 56)
    rel("France", "Ukraine", 50)
    rel("Ukraine", "Russia", -82)
    rel("Russia", "China", 48)
    rel("Russia", "India", 22)
    rel("China", "Japan", -38)
    rel("China", "India", -24)
    rel("India", "USA", 28)
    rel("Turkey", "Germany", 12)
    rel("Turkey", "Russia", -8)
    rel("Brazil", "France", 22)
    rel("Brazil", "USA", 12)

    for a, b in [("USA", "Germany"), ("USA", "Japan"), ("Germany", "France")]:
        countries[a].allies.add(b)
        countries[b].allies.add(a)

    countries["Ukraine"].wars.add("Russia")
    countries["Russia"].wars.add("Ukraine")
    return countries
