from __future__ import annotations

from typing import Dict


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


PARTIES = ["Conservative", "Liberal", "Socialist", "Nationalist"]
RESOURCES = ["oil", "food", "metal"]
UNIT_TYPES = ["infantry", "tanks", "artillery", "aircraft"]
BUILDING_TYPES = ["factory", "farm", "oil_field", "mine"]

UNIT_POWER = {
    "infantry": 1.0,
    "tanks": 9.0,
    "artillery": 6.0,
    "aircraft": 14.0,
}

UNIT_SUPPLY = {
    "infantry": {"food": 1.0, "metal": 0.15, "oil": 0.05},
    "tanks": {"food": 0.4, "metal": 1.3, "oil": 1.8},
    "artillery": {"food": 0.35, "metal": 1.5, "oil": 0.6},
    "aircraft": {"food": 0.25, "metal": 1.0, "oil": 2.4},
}

BUILDING_COSTS = {
    "factory": {"money": 360, "oil": 10, "food": 0, "metal": 48},
    "farm": {"money": 180, "oil": 0, "food": 0, "metal": 16},
    "oil_field": {"money": 240, "oil": 0, "food": 0, "metal": 24},
    "mine": {"money": 230, "oil": 6, "food": 0, "metal": 12},
}

WEAPON_BATCHES = {
    "infantry": {"money": 95, "oil": 2, "food": 10, "metal": 12, "amount": 120},
    "tanks": {"money": 180, "oil": 18, "food": 3, "metal": 30, "amount": 12},
    "artillery": {"money": 150, "oil": 8, "food": 2, "metal": 28, "amount": 10},
    "aircraft": {"money": 260, "oil": 24, "food": 2, "metal": 34, "amount": 5},
}

PARTY_EFFECTS = {
    "Conservative": {"income": 1.00, "army": 1.08, "stability": 5, "economy": 0},
    "Liberal": {"income": 1.12, "army": 0.95, "stability": -2, "economy": 1},
    "Socialist": {"income": 0.96, "army": 1.00, "stability": 6, "economy": 1},
    "Nationalist": {"income": 1.02, "army": 1.18, "stability": -5, "economy": 0},
}

LAW_OPTIONS = {
    "taxes": ["Low", "Normal", "High"],
    "conscription": ["Volunteer", "Limited", "Mandatory"],
    "censorship": ["Free Press", "Regulated", "State Media"],
    "trade_policy": ["Free Trade", "Balanced", "Protectionism"],
}

LAW_EFFECTS = {
    "taxes": {
        "Low": {"income": 0.86, "stability": 3},
        "Normal": {"income": 1.00, "stability": 0},
        "High": {"income": 1.20, "stability": -4},
    },
    "conscription": {
        "Volunteer": {"recruit": 0.78, "war": 0.94, "stability": 2},
        "Limited": {"recruit": 1.00, "war": 1.00, "stability": 0},
        "Mandatory": {"recruit": 1.35, "war": 1.10, "stability": -5},
    },
    "censorship": {
        "Free Press": {"income": 1.03, "stability": -1},
        "Regulated": {"income": 1.00, "stability": 1},
        "State Media": {"income": 0.96, "stability": 4},
    },
    "trade_policy": {
        "Free Trade": {"income": 1.13, "war": 0.95, "stability": -1},
        "Balanced": {"income": 1.00, "war": 1.00, "stability": 0},
        "Protectionism": {"income": 0.95, "war": 1.07, "stability": 2},
    },
}


def default_laws() -> Dict[str, str]:
    return {
        "taxes": "Normal",
        "conscription": "Limited",
        "censorship": "Regulated",
        "trade_policy": "Balanced",
    }


def default_units() -> Dict[str, int]:
    return {"infantry": 0, "tanks": 0, "artillery": 0, "aircraft": 0}


def default_buildings() -> Dict[str, int]:
    return {"factory": 1, "farm": 1, "oil_field": 1, "mine": 1}


def default_equipment() -> Dict[str, int]:
    return {"infantry": 0, "tanks": 0, "artillery": 0, "aircraft": 0}


def default_internal_problems() -> Dict[str, int]:
    return {"protests": 0, "corruption": 12, "separatism": 0, "government_crisis": 0}


def province(name: str, population: float, economy: int, oil: int, food: int, metal: int) -> Dict[str, object]:
    return {
        "name": name,
        "population": population,
        "economy": economy,
        "resources": {"oil": oil, "food": food, "metal": metal},
    }


