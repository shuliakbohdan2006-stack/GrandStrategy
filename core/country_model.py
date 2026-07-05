from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from core.country_data import (
    BUILDING_COSTS, BUILDING_TYPES, LAW_EFFECTS, LAW_OPTIONS, PARTIES, PARTY_EFFECTS,
    RESOURCES, UNIT_POWER, UNIT_SUPPLY, UNIT_TYPES, WEAPON_BATCHES, clamp,
    default_buildings, default_equipment, default_internal_problems, default_laws,
    default_units, province,
)
@dataclass
class Country:
    name: str
    capital: str
    population: float
    money: int
    army: int
    stability: int
    technology: int
    relation_to_player: int
    leader: str
    color: Tuple[int, int, int]
    shape: List[Tuple[int, int]]
    iso_a3: str = ""
    iso_a2: str = ""
    continent: str = ""
    geo_polygons: List[List[Tuple[float, float]]] = field(default_factory=list)
    label_lon: float = 0.0
    label_lat: float = 0.0
    capital_lon: float = 0.0
    capital_lat: float = 0.0
    flag_colors: List[Tuple[int, int, int]] = field(default_factory=list)
    is_core_country: bool = False
    economy: int = 5
    influence: int = 25
    territory_points: int = 10
    party: str = "Conservative"
    government_type: str = "Democracy"
    next_election_year: int = 2030
    leader_pool: List[str] = field(default_factory=list)
    laws: Dict[str, str] = field(default_factory=default_laws)
    resources: Dict[str, int] = field(default_factory=lambda: {"oil": 40, "food": 60, "metal": 45})
    provinces: List[Dict[str, object]] = field(default_factory=list)
    units: Dict[str, int] = field(default_factory=default_units)
    buildings: Dict[str, int] = field(default_factory=default_buildings)
    equipment: Dict[str, int] = field(default_factory=default_equipment)
    debt: int = 0
    inflation: float = 2.0
    last_month_income: int = 0
    last_month_expenses: int = 0
    last_month_balance: int = 0
    internal_problems: Dict[str, int] = field(default_factory=default_internal_problems)
    vassal_of: Optional[str] = None
    vassals: Set[str] = field(default_factory=set)
    allies: Set[str] = field(default_factory=set)
    wars: Set[str] = field(default_factory=set)
    relations: Dict[str, int] = field(default_factory=dict)
    spouse: Optional[str] = None
    lover: Optional[str] = None
    children: List[Dict[str, object]] = field(default_factory=list)
    def __post_init__(self) -> None:
        if not self.leader_pool:
            self.leader_pool = [self.leader]
        if not self.flag_colors:
            self.flag_colors = [(230, 230, 230), self.color, (35, 41, 48)]
        self._ensure_laws()
        self._ensure_resources()
        self._ensure_units()
        self._ensure_buildings()
        self._ensure_equipment()
        self._ensure_internal_problems()
        if not self.provinces:
            self.provinces = [
                province(f"{self.name} Core", self.population, max(1, self.economy), 4, 8, 5),
            ]
        self.sync_army_from_units()
    def _ensure_laws(self) -> None:
        merged = default_laws()
        merged.update(self.laws)
        self.laws = merged
    def _ensure_resources(self) -> None:
        for resource_name in RESOURCES:
            self.resources.setdefault(resource_name, 0)
    def _ensure_units(self) -> None:
        merged = default_units()
        merged.update({name: int(value) for name, value in self.units.items()})
        if sum(merged.values()) == 0 and self.army > 0:
            merged["infantry"] = max(1, int(self.army * 0.72))
            merged["tanks"] = max(0, int(self.army * 0.025))
            merged["artillery"] = max(0, int(self.army * 0.035))
            merged["aircraft"] = max(0, int(self.army * 0.012))
        self.units = merged
    def _ensure_buildings(self) -> None:
        merged = default_buildings()
        merged.update({name: int(value) for name, value in self.buildings.items()})
        self.buildings = merged
    def _ensure_equipment(self) -> None:
        merged = default_equipment()
        merged.update({name: int(value) for name, value in self.equipment.items()})
        self.equipment = merged
    def _ensure_internal_problems(self) -> None:
        merged = default_internal_problems()
        merged.update({name: int(value) for name, value in self.internal_problems.items()})
        self.internal_problems = {name: clamp(value, 0, 100) for name, value in merged.items()}
    @property
    def is_democratic(self) -> bool:
        return self.government_type == "Democracy"
    def center(self) -> Tuple[int, int]:
        xs = [point[0] for point in self.shape]
        ys = [point[1] for point in self.shape]
        return sum(xs) // len(xs), sum(ys) // len(ys)
    def contains_point(self, point: Tuple[int, int]) -> bool:
        """Ray-casting point-in-polygon test for the simplified map."""
        x, y = point
        inside = False
        j = len(self.shape) - 1
        for i in range(len(self.shape)):
            xi, yi = self.shape[i]
            xj, yj = self.shape[j]
            intersects = (yi > y) != (yj > y)
            if intersects:
                x_on_edge = (xj - xi) * (y - yi) / max(1, yj - yi) + xi
                if x < x_on_edge:
                    inside = not inside
            j = i
        return inside
    def regional_economy(self) -> int:
        return sum(int(region.get("economy", 0)) for region in self.provinces)
    def resource_output(self) -> Dict[str, int]:
        output = {resource_name: 0 for resource_name in RESOURCES}
        for region in self.provinces:
            region_resources = dict(region.get("resources", {}))
            for resource_name in RESOURCES:
                output[resource_name] += int(region_resources.get(resource_name, 0))
        output["food"] += self.buildings.get("farm", 0) * 12
        output["oil"] += self.buildings.get("oil_field", 0) * 10
        output["metal"] += self.buildings.get("mine", 0) * 10
        return output
    def produce_resources(self) -> Dict[str, int]:
        output = self.resource_output()
        if self.laws["trade_policy"] == "Free Trade":
            output = {key: max(0, int(value * 0.92)) for key, value in output.items()}
            self.money += 18
        elif self.laws["trade_policy"] == "Protectionism":
            output = {key: int(value * 1.08) for key, value in output.items()}
        for resource_name, amount in output.items():
            self.resources[resource_name] = min(999, self.resources.get(resource_name, 0) + amount)
        return output
    def auto_produce_weapons(self) -> Dict[str, int]:
        factories = self.buildings.get("factory", 0)
        if factories <= 0:
            return default_equipment()
        produced = default_equipment()
        plans = [
            ("infantry", factories * 24, {"metal": factories * 4, "food": factories * 2, "oil": factories}),
            ("artillery", max(1, factories // 2), {"metal": factories * 5, "oil": factories * 2}),
            ("tanks", max(1, factories // 3), {"metal": factories * 6, "oil": factories * 4}),
            ("aircraft", max(0, factories // 4), {"metal": factories * 7, "oil": factories * 5}),
        ]
        for unit_type, amount, costs in plans:
            if amount <= 0:
                continue
            if self.has_resources(costs):
                self.spend_resources(costs)
                self.equipment[unit_type] += amount
                produced[unit_type] += amount
        return produced
    def law_income_multiplier(self) -> float:
        taxes = LAW_EFFECTS["taxes"][self.laws["taxes"]]["income"]
        censorship = LAW_EFFECTS["censorship"][self.laws["censorship"]]["income"]
        trade = LAW_EFFECTS["trade_policy"][self.laws["trade_policy"]]["income"]
        return float(taxes * censorship * trade)
    def law_stability_drift(self) -> int:
        return int(
            LAW_EFFECTS["taxes"][self.laws["taxes"]]["stability"]
            + LAW_EFFECTS["conscription"][self.laws["conscription"]]["stability"]
            + LAW_EFFECTS["censorship"][self.laws["censorship"]]["stability"]
            + LAW_EFFECTS["trade_policy"][self.laws["trade_policy"]]["stability"]
        )
    def law_recruit_multiplier(self) -> float:
        return float(LAW_EFFECTS["conscription"][self.laws["conscription"]]["recruit"])
    def law_war_multiplier(self) -> float:
        conscription = LAW_EFFECTS["conscription"][self.laws["conscription"]]["war"]
        trade = LAW_EFFECTS["trade_policy"][self.laws["trade_policy"]]["war"]
        return float(conscription * trade)
    def monthly_income(self) -> int:
        party_income = PARTY_EFFECTS.get(self.party, PARTY_EFFECTS["Conservative"])["income"]
        stability_factor = 0.45 + (self.stability / 180)
        regional_value = self.regional_economy() * 8
        resource_output = self.resource_output()
        resource_factor = 1.0 + min(
            0.38,
            (resource_output["oil"] * 1.1 + resource_output["food"] * 0.45 + resource_output["metal"] * 0.8) / 260,
        )
        factory_value = self.buildings.get("factory", 0) * 24
        debt_drag = 1.0 - min(0.25, self.debt / 15000)
        inflation_drag = 1.0 - min(0.35, self.inflation / 90)
        corruption_drag = 1.0 - min(0.30, self.internal_problems.get("corruption", 0) / 220)
        base = 18 + self.population * 0.095 + self.economy * 14 + regional_value + factory_value + self.technology * 10
        influence_bonus = self.influence * 0.65
        vassal_bonus = len(self.vassals) * 22
        if self.vassal_of:
            vassal_bonus -= 18
        return max(5, int((base + influence_bonus + vassal_bonus) * stability_factor * party_income * self.law_income_multiplier() * resource_factor * debt_drag * inflation_drag * corruption_drag))
    def monthly_expenses(self) -> int:
        unit_cost = (
            self.units["infantry"] * 0.035
            + self.units["tanks"] * 1.6
            + self.units["artillery"] * 1.1
            + self.units["aircraft"] * 2.4
        )
        building_cost = self.buildings.get("factory", 0) * 9 + self.buildings.get("oil_field", 0) * 4 + self.buildings.get("mine", 0) * 4
        interest = int(self.debt * (0.006 + min(0.014, self.inflation / 6000)))
        return max(0, int(unit_cost + building_cost + interest))
    def supply_need(self) -> Dict[str, int]:
        needs = {resource_name: 0.0 for resource_name in RESOURCES}
        for unit_type, count in self.units.items():
            for resource_name, amount in UNIT_SUPPLY[unit_type].items():
                needs[resource_name] += count * amount / 100
        return {resource_name: max(0, int(amount)) for resource_name, amount in needs.items()}
    def consume_supply(self, multiplier: float = 1.0) -> Dict[str, int]:
        needs = self.supply_need()
        consumed = {}
        for resource_name, amount in needs.items():
            spend = max(0, int(amount * multiplier))
            consumed[resource_name] = min(self.resources.get(resource_name, 0), spend)
            self.resources[resource_name] = max(0, self.resources.get(resource_name, 0) - spend)
        return consumed
    def supply_ratio(self) -> float:
        needs = self.supply_need()
        ratios = []
        for resource_name, amount in needs.items():
            if amount <= 0:
                ratios.append(1.0)
            else:
                ratios.append(min(1.0, self.resources.get(resource_name, 0) / amount))
        return max(0.25, min(ratios) if ratios else 1.0)
    def national_power_score(self) -> int:
        economy_score = self.monthly_income() + self.regional_economy() * 9 + self.money // 12
        military_score = int(self.army * self.supply_ratio() * 0.55)
        diplomatic_score = self.influence * 4 + len(self.allies) * 60 + len(self.vassals) * 85
        stability_score = self.stability * 4
        debt_penalty = self.debt // 18 + int(self.inflation * 4)
        problem_penalty = sum(self.internal_problems.values()) * 2
        return max(0, economy_score + military_score + diplomatic_score + stability_score - debt_penalty - problem_penalty)
    def sync_army_from_units(self) -> None:
        self.army = int(sum(self.units[unit_type] * UNIT_POWER[unit_type] for unit_type in UNIT_TYPES))
    def build_cost(self, building_type: str) -> Dict[str, int]:
        base = dict(BUILDING_COSTS[building_type])
        owned = self.buildings.get(building_type, 0)
        scale = 1 + owned * 0.13
        return {key: int(value * scale) for key, value in base.items()}
    def build_structure(self, building_type: str) -> bool:
        if building_type not in BUILDING_TYPES:
            return False
        cost = self.build_cost(building_type)
        money = cost.pop("money")
        if self.money < money or not self.has_resources(cost):
            return False
        self.money -= money
        self.spend_resources(cost)
        self.buildings[building_type] += 1
        if building_type == "factory":
            self.economy += 1
        elif self.provinces:
            target = max(self.provinces, key=lambda region: int(region.get("economy", 0)))
            resources = dict(target.get("resources", {}))
            if building_type == "farm":
                resources["food"] = int(resources.get("food", 0)) + 2
            elif building_type == "oil_field":
                resources["oil"] = int(resources.get("oil", 0)) + 2
            elif building_type == "mine":
                resources["metal"] = int(resources.get("metal", 0)) + 2
            target["resources"] = resources
        return True
    def produce_weapon_batch(self, unit_type: str) -> bool:
        if unit_type not in UNIT_TYPES:
            return False
        if unit_type != "infantry" and self.buildings.get("factory", 0) <= 0:
            return False
        cost = dict(WEAPON_BATCHES[unit_type])
        money = int(cost.pop("money"))
        amount = int(cost.pop("amount"))
        if self.money < money or not self.has_resources(cost):
            return False
        self.money -= money
        self.spend_resources(cost)
        self.equipment[unit_type] += amount
        self.units[unit_type] += amount
        self.sync_army_from_units()
        return True
    def invest_cost(self) -> int:
        return 100 + self.economy * 32
    def invest_resource_cost(self) -> Dict[str, int]:
        return {"oil": 0, "food": 0, "metal": 8 + self.economy}
    def recruit_cost(self) -> int:
        return 70 + self.army // 19
    def recruit_resource_cost(self) -> Dict[str, int]:
        return {"oil": 2 + self.technology // 2, "food": 8 + self.army // 280, "metal": 10 + self.army // 230}
    def tech_cost(self) -> int:
        return 170 + self.technology * 90
    def tech_resource_cost(self) -> Dict[str, int]:
        return {"oil": 8 + self.technology, "food": 0, "metal": 8 + self.technology}
    def has_resources(self, costs: Dict[str, int]) -> bool:
        return all(self.resources.get(resource_name, 0) >= amount for resource_name, amount in costs.items())
    def spend_resources(self, costs: Dict[str, int]) -> None:
        for resource_name, amount in costs.items():
            self.resources[resource_name] = max(0, self.resources.get(resource_name, 0) - amount)
    def resource_shortage_text(self, costs: Dict[str, int]) -> str:
        missing = []
        for resource_name, amount in costs.items():
            have = self.resources.get(resource_name, 0)
            if have < amount:
                missing.append(f"{resource_name} {have}/{amount}")
        return ", ".join(missing) if missing else "none"
    def invest_in_economy(self) -> bool:
        cost = self.invest_cost()
        resource_cost = self.invest_resource_cost()
        if self.money < cost or not self.has_resources(resource_cost):
            return False
        self.money -= cost
        self.spend_resources(resource_cost)
        self.economy += 1
        if self.provinces:
            best_region = max(self.provinces, key=lambda region: int(region.get("economy", 0)))
            best_region["economy"] = int(best_region.get("economy", 0)) + 1
        self.stability = clamp(self.stability + 1, 0, 100)
        return True
    def recruit_soldiers(self) -> bool:
        cost = self.recruit_cost()
        resource_cost = self.recruit_resource_cost()
        if self.money < cost or not self.has_resources(resource_cost):
            return False
        party_army = PARTY_EFFECTS.get(self.party, PARTY_EFFECTS["Conservative"])["army"]
        amount = int((20 + self.technology * 4 + self.population * 0.04) * party_army * self.law_recruit_multiplier())
        if self.resources.get("food", 0) < 18:
            amount = int(amount * 0.75)
        self.money -= cost
        self.spend_resources(resource_cost)
        self.units["infantry"] += max(8, amount)
        self.sync_army_from_units()
        self.stability = clamp(self.stability - 1, 0, 100)
        return True
    def research_technology(self) -> bool:
        cost = self.tech_cost()
        resource_cost = self.tech_resource_cost()
        if self.money < cost or not self.has_resources(resource_cost):
            return False
        self.money -= cost
        self.spend_resources(resource_cost)
        self.technology += 1
        self.stability = clamp(self.stability + 1, 0, 100)
        return True
    def change_party(self, party: str) -> bool:
        if party not in PARTIES or party == self.party:
            return False
        effect = PARTY_EFFECTS[party]
        self.party = party
        self.stability = clamp(self.stability + effect["stability"] - 3, 0, 100)
        self.economy = max(1, self.economy + effect["economy"])
        if party == "Nationalist":
            self.units["infantry"] += 25
        elif party == "Conservative":
            self.units["infantry"] += 8
        elif party == "Liberal":
            self.money += 35
        elif party == "Socialist":
            self.money = max(0, self.money - 25)
        self.sync_army_from_units()
        return True
    def change_law(self, category: str, value: str) -> bool:
        if category not in LAW_OPTIONS or value not in LAW_OPTIONS[category]:
            return False
        if self.laws.get(category) == value:
            return False
        self.laws[category] = value
        self.stability = clamp(self.stability - 2 + int(LAW_EFFECTS[category][value].get("stability", 0)), 0, 100)
        return True
    def recalculate_from_provinces(self) -> None:
        if not self.provinces:
            self.population = max(1, self.population)
            self.territory_points = max(1, self.territory_points)
            return
        self.population = round(sum(float(region.get("population", 0)) for region in self.provinces), 1)
        self.territory_points = max(1, len(self.provinces) * 3 + self.regional_economy())
from core.country_serialization import attach_country_serialization
attach_country_serialization(Country)
