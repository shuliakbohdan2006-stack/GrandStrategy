from __future__ import annotations

from core.country_data import PARTY_EFFECTS, clamp


def _ensure_alpha_indicators(self) -> None:
    self.unemployment = max(1.0, min(35.0, float(self.unemployment)))
    self.education = clamp(int(self.education), 1, 100)
    self.healthcare = clamp(int(self.healthcare), 1, 100)
    self.army_experience = clamp(int(self.army_experience), 0, 100)
    self.army_morale = clamp(int(self.army_morale), 0, 100)
    self.equipment_wear = clamp(int(self.equipment_wear), 0, 100)
    if self.gdp <= 0:
        self.gdp = max(40, int(self.structural_gdp_capacity() * 0.88))
    if self.military_spending <= 0:
        self.military_spending = max(5, int(self.army * 0.08))
    if self.tax_income <= 0:
        self.tax_income = max(5, int(self.gdp * 0.018))


def structural_gdp_capacity(self) -> int:
    output = self.resource_output()
    buildings = self.buildings
    resource_value = output["oil"] * 5 + output["food"] * 2 + output["metal"] * 4
    services = (self.education + self.healthcare) * 16
    industry = buildings.get("factory", 0) * 110 + buildings.get("farm", 0) * 22 + buildings.get("oil_field", 0) * 34 + buildings.get("mine", 0) * 32
    base = (
        self.population * 7.0
        + self.economy * 125
        + self.regional_economy() * 48
        + self.technology * 62
        + services
        + industry
        + resource_value
    )
    problem_drag = 1.0 - min(0.32, sum(self.internal_problems.values()) / 900)
    debt_drag = 1.0 - min(0.22, self.debt / 24000)
    return max(60, int(base * problem_drag * debt_drag))


def gdp_per_capita(self) -> int:
    return max(1, int((self.gdp * 1000) / max(1.0, self.population)))


def economic_efficiency(self) -> float:
    stability_factor = 0.70 + self.stability / 245
    services_factor = 0.82 + (self.education + self.healthcare) / 560
    labor_drag = 1.0 - min(0.32, self.unemployment / 92)
    inflation_drag = 1.0 - min(0.36, self.inflation / 88)
    corruption_drag = 1.0 - min(0.30, self.internal_problems.get("corruption", 0) / 230)
    sanction_drag = 1.0 - min(0.24, len(self.sanctioned_by) * 0.04)
    trade_bonus = 1.0 + min(0.14, len(self.trade_agreements) * 0.018)
    overheated = max(0, self.gdp - self.structural_gdp_capacity())
    overheat_drag = 1.0 - min(0.20, overheated / max(1, self.gdp) * 0.55)
    return max(0.34, stability_factor * services_factor * labor_drag * inflation_drag * corruption_drag * sanction_drag * trade_bonus * overheat_drag)


def research_soft_cap(self) -> int:
    return max(5, int(5 + self.education / 10 + self.economy / 5))


def research_multiplier(self) -> float:
    education_bonus = 0.76 + self.education / 145
    economy_bonus = 1.0 + min(0.16, self.economy / 95)
    debt_drag = 1.0 - min(0.25, self.debt / 18000)
    over_cap = max(0, self.technology - self.research_soft_cap())
    return max(0.45, education_bonus * economy_bonus * debt_drag / (1.0 + over_cap * 0.35))


def military_readiness(self) -> float:
    supply = self.supply_ratio()
    morale = 0.68 + self.army_morale / 190
    experience = 0.88 + self.army_experience / 260
    wear = 1.0 - min(0.36, self.equipment_wear / 190)
    treaty_bonus = 1.0 + min(0.14, len(self.military_agreements) * 0.025)
    return max(0.25, supply * morale * experience * wear * treaty_bonus)


def update_monthly_indicators(self, income: int, expenses: int, month: int | None = None) -> None:
    tax_rate = {"Low": 0.17, "Normal": 0.23, "High": 0.31}.get(self.laws["taxes"], 0.23)
    self.tax_income = max(1, int(income * tax_rate))
    self.military_spending = max(0, int(expenses * 0.62 + self.army * 0.025))

    capacity = self.structural_gdp_capacity()
    target_gdp = int(capacity * (0.88 + min(0.18, self.economic_efficiency() / 8)))
    delta = target_gdp - self.gdp
    max_growth = max(3, int(self.gdp * 0.003 + self.economy * 0.55))
    max_decline = max(8, int(self.gdp * 0.014))
    if delta >= 0:
        self.gdp += min(delta, max_growth)
    else:
        self.gdp -= min(-delta, max_decline)
    self.gdp = max(40, self.gdp)

    unemployment_delta = 0.0
    if self.last_month_balance > 40:
        unemployment_delta -= 0.10 + min(0.08, self.economy / 140)
    if self.last_month_balance < -40:
        unemployment_delta += 0.20
    if self.gdp > capacity * 1.08:
        unemployment_delta += 0.08
        self.inflation = min(100.0, self.inflation + 0.08)
    unemployment_delta -= min(0.10, self.buildings.get("factory", 0) * 0.010)
    unemployment_delta += min(0.24, self.internal_problems.get("protests", 0) / 470)
    unemployment_delta += min(0.14, self.inflation / 520)
    self.unemployment = max(1.0, min(35.0, self.unemployment + unemployment_delta))

    service_pressure = income - expenses
    is_quarter = month in {1, 4, 7, 10} if month is not None else True
    if service_pressure > 100 and self.debt < income * 16 and is_quarter:
        self.education = clamp(self.education + 1, 1, 100)
        if self.money > expenses * 4:
            self.healthcare = clamp(self.healthcare + 1, 1, 100)
    elif service_pressure < -90:
        self.education = clamp(self.education - 1, 1, 100)
        self.healthcare = clamp(self.healthcare - 1, 1, 100)

    if self.unemployment > 16:
        self.stability = clamp(self.stability - 1, 0, 100)
    if self.healthcare < 35 and self.resources.get("food", 0) < 18:
        self.stability = clamp(self.stability - 1, 0, 100)

    target_morale = int((self.stability * 0.45) + (self.supply_ratio() * 35) + 20)
    if self.wars:
        target_morale -= 5
        self.equipment_wear = clamp(self.equipment_wear + 1, 0, 100)
    else:
        self.equipment_wear = clamp(self.equipment_wear - 1, 0, 100)
    self.army_morale = clamp(int(self.army_morale * 0.80 + target_morale * 0.20), 0, 100)


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
    gdp_anchor = (self.gdp ** 0.5) * (2.2 + min(0.7, self.economy / 26))
    base = 18 + self.population * 0.095 + self.economy * 14 + regional_value + factory_value + self.technology * 10 + gdp_anchor
    influence_bonus = self.influence * 0.65
    vassal_bonus = len(self.vassals) * 22
    if self.vassal_of:
        vassal_bonus -= 18
    capacity = max(1, self.structural_gdp_capacity())
    capacity_drag = 1.0 - min(0.18, max(0, self.gdp - capacity) / max(1, self.gdp) * 0.65)
    return max(5, int((base + influence_bonus + vassal_bonus) * stability_factor * party_income * self.law_income_multiplier() * resource_factor * debt_drag * inflation_drag * corruption_drag * self.economic_efficiency() * capacity_drag))


def monthly_expenses(self) -> int:
    unit_cost = (
        self.units["infantry"] * 0.035
        + self.units["tanks"] * 1.6
        + self.units["artillery"] * 1.1
        + self.units["aircraft"] * 2.4
    )
    building_cost = self.buildings.get("factory", 0) * 9 + self.buildings.get("oil_field", 0) * 4 + self.buildings.get("mine", 0) * 4
    services_cost = (self.education + self.healthcare) * 0.38
    economy_maintenance = self.economy * 10 + self.regional_economy() * 2.8 + (self.gdp ** 0.5) * 0.95
    tech_maintenance = (self.technology ** 1.35) * 2.4
    reserve_overhead = max(0, self.money - max(900, self.gdp * 0.9)) * 0.08
    interest = int(self.debt * (0.006 + min(0.014, self.inflation / 6000)))
    return max(0, int(unit_cost + building_cost + services_cost + economy_maintenance + tech_maintenance + reserve_overhead + interest))


def national_power_score(self) -> int:
    economy_score = self.monthly_income() + self.regional_economy() * 9 + self.money // 12 + self.gdp // 18
    military_score = int(self.army * self.military_readiness() * 0.55)
    diplomatic_score = self.influence * 4 + len(self.allies) * 60 + len(self.vassals) * 85
    stability_score = self.stability * 4 + self.education + self.healthcare
    debt_penalty = self.debt // 18 + int(self.inflation * 4)
    problem_penalty = sum(self.internal_problems.values()) * 2
    return max(0, economy_score + military_score + diplomatic_score + stability_score - debt_penalty - problem_penalty)


def tech_cost(self) -> int:
    over_cap = max(0, self.technology - self.research_soft_cap())
    base = 220 + self.technology * 120 + self.technology * self.technology * 28
    discount = min(0.18, self.education / 650)
    over_cap_penalty = 1.0 + over_cap * 0.55
    debt_penalty = 1.0 + min(0.35, self.debt / 22000)
    return max(130, int(base * (1.0 - discount) * over_cap_penalty * debt_penalty))


def tech_resource_cost(self) -> dict[str, int]:
    return {"oil": 8 + self.technology * 2, "food": 0, "metal": 8 + self.technology * 2}


def attach_country_indicators(country_cls) -> None:
    country_cls._ensure_alpha_indicators = _ensure_alpha_indicators
    country_cls.structural_gdp_capacity = structural_gdp_capacity
    country_cls.gdp_per_capita = gdp_per_capita
    country_cls.economic_efficiency = economic_efficiency
    country_cls.research_soft_cap = research_soft_cap
    country_cls.research_multiplier = research_multiplier
    country_cls.military_readiness = military_readiness
    country_cls.update_monthly_indicators = update_monthly_indicators
    country_cls.monthly_income = monthly_income
    country_cls.monthly_expenses = monthly_expenses
    country_cls.national_power_score = national_power_score
    country_cls.tech_cost = tech_cost
    country_cls.tech_resource_cost = tech_resource_cost
