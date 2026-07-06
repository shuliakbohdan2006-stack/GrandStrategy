from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from core.country_data import RESOURCES, UNIT_TYPES, clamp


@dataclass(frozen=True)
class EventOption:
    label: str
    description: str
    effects: Dict[str, int]


@dataclass(frozen=True)
class EventTemplate:
    event_id: str
    category: str
    title: str
    description: str
    choices: Tuple[EventOption, EventOption]
    min_stability: int = 0
    max_stability: int = 100
    min_technology: int = 0
    max_debt_ratio: Optional[float] = None
    war_required: bool = False
    peace_required: bool = False

    def can_trigger(self, country, game_state) -> bool:
        if country.stability < self.min_stability or country.stability > self.max_stability:
            return False
        if country.technology < self.min_technology:
            return False
        if self.war_required and not country.wars:
            return False
        if self.peace_required and country.wars:
            return False
        if self.max_debt_ratio is not None:
            if country.debt > country.monthly_income() * self.max_debt_ratio:
                return False
        return True


CATEGORY_OPTIONS = {
    "Economy": (
        ("Stimulus", "Inject reserves and protect demand."),
        ("Austerity", "Cut spending and accept slower growth."),
    ),
    "Politics": (
        ("Negotiate", "Build a compromise with political actors."),
        ("Purge", "Force through a hard political reset."),
    ),
    "War": (
        ("Reinforce", "Commit supplies and rotate battered units."),
        ("Escalate", "Push commanders to accept higher operational risk."),
    ),
    "Science": (
        ("Fund labs", "Increase grants for long-term research capacity."),
        ("Commercialize", "Turn discoveries into immediate economic value."),
    ),
    "Society": (
        ("Social package", "Spend on public confidence and services."),
        ("Local autonomy", "Let regional groups absorb pressure."),
    ),
    "Natural Disaster": (
        ("Emergency relief", "Move money and supplies into disaster response."),
        ("Rebuild later", "Delay recovery and preserve the treasury."),
    ),
    "Epidemic": (
        ("Public health drive", "Prioritize clinics, guidance and prevention."),
        ("Targeted quarantine", "Restrict hotspots and protect the budget."),
    ),
    "Terrorism": (
        ("Intelligence sweep", "Invest in careful security work."),
        ("Security crackdown", "Use forceful measures with political risk."),
    ),
    "Corruption": (
        ("Independent inquiry", "Expose the network and restore trust."),
        ("Quiet settlement", "Recover some funds while tolerating opacity."),
    ),
    "Sport": (
        ("Grassroots funding", "Use sport to raise morale and social cohesion."),
        ("Prestige bid", "Spend for international prestige."),
    ),
    "Culture": (
        ("Public grants", "Support creators and public institutions."),
        ("Export campaign", "Turn culture into diplomatic influence."),
    ),
    "Migration": (
        ("Integration plan", "Absorb migration through services and work permits."),
        ("Border controls", "Reduce pressure while risking unrest."),
    ),
    "Energy": (
        ("Strategic reserve", "Protect fuel and grid stability."),
        ("Market expansion", "Boost output and accept price volatility."),
    ),
}


def _category_specs() -> Sequence[Dict[str, object]]:
    return [
        {
            "category": "Economy",
            "themes": ["Bank liquidity", "Consumer confidence", "Export surge", "Housing bubble", "Port strike", "Startup boom", "Currency pressure", "Budget audit"],
            "good": {"money": 90, "gdp": 120, "stability": 1},
            "hard": {"money": -55, "inflation": 1, "unemployment": 1},
        },
        {
            "category": "Politics",
            "themes": ["Cabinet dispute", "Regional governors", "Parliament vote", "Civil service reform", "Anti-corruption drive", "Opposition rally", "Coalition talks", "Constitution debate"],
            "good": {"stability": 4, "corruption": -3, "influence": 1},
            "hard": {"stability": -4, "government_crisis": 4},
        },
        {
            "category": "War",
            "themes": ["Veteran initiative", "Logistics command", "Field hospital", "Officer academy", "Ammunition shortage", "Air doctrine", "Signals corps", "War bonds"],
            "good": {"army_morale": 4, "army_experience": 3, "equipment_wear": -2},
            "hard": {"money": -45, "metal": -8, "equipment_wear": 4},
            "war_required": True,
        },
        {
            "category": "Science",
            "themes": ["University grants", "Patent race", "Research campus", "AI laboratory", "Satellite program", "Clean energy lab", "Medical trial", "Engineering prize"],
            "good": {"technology": 1, "education": 2, "gdp": 70},
            "hard": {"money": -80, "education": 1},
            "min_technology": 2,
        },
        {
            "category": "Society",
            "themes": ["Housing program", "Labor reform", "Youth movement", "Public health week", "Education campaign", "Urban renewal", "Rural grants", "Media debate"],
            "good": {"stability": 3, "healthcare": 1, "education": 1},
            "hard": {"money": -45, "protests": -2},
        },
        {
            "category": "Natural Disaster",
            "themes": ["Flood season", "Earthquake response", "Wildfire front", "Storm damage", "Drought relief", "Cold snap", "Landslide recovery", "Heatwave grid stress"],
            "good": {"money": -65, "stability": 1, "healthcare": 1},
            "hard": {"money": -110, "food": -12, "stability": -3},
        },
        {
            "category": "Epidemic",
            "themes": ["Hospital surge", "Vaccine campaign", "Border screening", "Medical supply chain", "Public guidance", "Research consortium", "School closures", "Emergency clinics"],
            "good": {"healthcare": 2, "stability": 1},
            "hard": {"money": -70, "stability": -3, "unemployment": 1},
        },
        {
            "category": "Terrorism",
            "themes": ["Security alert", "Railway plot", "Cyber cell", "Embassy threat", "Border raid", "Intelligence leak", "Emergency policing", "Radical network"],
            "good": {"stability": 1, "army_morale": 2, "protests": -1},
            "hard": {"stability": -5, "government_crisis": 2},
        },
        {
            "category": "Corruption",
            "themes": ["Procurement scandal", "Court investigation", "Tax fraud ring", "Police bribery", "Oligarch trial", "Customs leak", "Party donations", "Public contracts"],
            "good": {"corruption": -5, "stability": 1},
            "hard": {"corruption": 5, "money": 35, "stability": -2},
        },
        {
            "category": "Sport",
            "themes": ["Continental games", "World cup bid", "Olympic medal", "Stadium program", "Youth league", "National derby", "Sports diplomacy", "Athlete scandal"],
            "good": {"stability": 2, "influence": 1},
            "hard": {"money": -40, "stability": 1},
            "peace_required": True,
        },
        {
            "category": "Culture",
            "themes": ["Film festival", "Museum opening", "Heritage grants", "Music export", "Language program", "National holiday", "Publisher boom", "Cultural boycott"],
            "good": {"stability": 2, "influence": 2},
            "hard": {"money": -35, "education": 1},
            "peace_required": True,
        },
        {
            "category": "Migration",
            "themes": ["Worker visas", "Refugee corridor", "Brain drain", "Diaspora bonds", "Border labor", "Urban inflow", "Rural depopulation", "Return program"],
            "good": {"gdp": 80, "unemployment": -1, "stability": 1},
            "hard": {"stability": -2, "protests": 3, "population": 1},
        },
        {
            "category": "Energy",
            "themes": ["Oil discovery", "Grid upgrade", "Fuel shortage", "Pipeline talks", "Solar tender", "Mine expansion", "Refinery fire", "Strategic reserve"],
            "good": {"oil": 16, "metal": 8, "gdp": 80},
            "hard": {"oil": -18, "inflation": 1, "money": -45},
        },
    ]


def _scaled(base: Dict[str, int], index: int) -> Dict[str, int]:
    scale = 1 + (index % 4) * 0.18
    return {key: int(value * scale) for key, value in base.items()}


def build_event_catalog() -> List[EventTemplate]:
    catalog: List[EventTemplate] = []
    for spec in _category_specs():
        category = str(spec["category"])
        themes = list(spec["themes"])  # type: ignore[arg-type]
        for index, theme in enumerate(themes):
            event_id = f"{category.lower().replace(' ', '_')}_{index + 1:02d}"
            good = _scaled(dict(spec["good"]), index)  # type: ignore[arg-type]
            hard = _scaled(dict(spec["hard"]), index)  # type: ignore[arg-type]
            title = f"{theme}"
            description = (
                f"{theme} forces the government to choose between short-term pressure "
                f"and long-term national capacity."
            )
            option_a, option_b = CATEGORY_OPTIONS[category]
            catalog.append(
                EventTemplate(
                    event_id=event_id,
                    category=category,
                    title=title,
                    description=description,
                    choices=(
                        EventOption(option_a[0], option_a[1], good),
                        EventOption(option_b[0], option_b[1], hard),
                    ),
                    min_stability=0 if index % 3 else 35,
                    max_stability=100 if index % 4 else 82,
                    min_technology=int(spec.get("min_technology", 0)),
                    max_debt_ratio=28.0 if index % 5 == 0 else None,
                    war_required=bool(spec.get("war_required", False)) and index % 2 == 0,
                    peace_required=bool(spec.get("peace_required", False)) and index % 2 == 0,
                )
            )
    return catalog


EVENT_CATALOG = build_event_catalog()


def available_events(country, game_state) -> List[EventTemplate]:
    return [event for event in EVENT_CATALOG if event.can_trigger(country, game_state)]


def choose_event_option(event: EventTemplate, country) -> EventOption:
    if country.stability < 45 or country.debt > country.monthly_income() * 20:
        return event.choices[0]
    if country.party in {"Liberal", "Conservative"} and event.category in {"Economy", "Science", "Energy"}:
        return event.choices[1] if random.random() < 0.42 else event.choices[0]
    if country.party == "Nationalist" and event.category in {"War", "Terrorism"}:
        return event.choices[1] if random.random() < 0.50 else event.choices[0]
    return random.choice(event.choices)


def apply_effects(country, effects: Dict[str, int]) -> None:
    for key, value in effects.items():
        if key == "money":
            country.money = max(0, country.money + value)
        elif key == "stability":
            country.stability = clamp(country.stability + value, 0, 100)
        elif key == "technology":
            country.technology = max(0, country.technology + value)
        elif key == "influence":
            country.influence = max(0, country.influence + value)
        elif key == "gdp":
            country.gdp = max(1, country.gdp + value)
        elif key == "population":
            country.population = max(1.0, country.population + value)
        elif key == "unemployment":
            country.unemployment = max(1.0, min(35.0, country.unemployment + value))
        elif key == "education":
            country.education = clamp(country.education + value, 1, 100)
        elif key == "healthcare":
            country.healthcare = clamp(country.healthcare + value, 1, 100)
        elif key == "inflation":
            country.inflation = max(1.0, min(100.0, country.inflation + value))
        elif key == "debt":
            country.debt = max(0, country.debt + value)
        elif key == "army_morale":
            country.army_morale = clamp(country.army_morale + value, 0, 100)
        elif key == "army_experience":
            country.army_experience = clamp(country.army_experience + value, 0, 100)
        elif key == "equipment_wear":
            country.equipment_wear = clamp(country.equipment_wear + value, 0, 100)
        elif key in country.internal_problems:
            country.internal_problems[key] = clamp(country.internal_problems[key] + value, 0, 100)
        elif key in RESOURCES:
            country.resources[key] = max(0, min(999, country.resources.get(key, 0) + value))
        elif key in UNIT_TYPES:
            country.units[key] = max(0, country.units.get(key, 0) + value)
            country.sync_army_from_units()


def summarize_effects(effects: Dict[str, int]) -> str:
    parts = []
    for key, value in effects.items():
        sign = "+" if value >= 0 else ""
        parts.append(f"{key} {sign}{value}")
    return ", ".join(parts)
