from __future__ import annotations

from typing import Dict

from core.country_data import default_buildings, default_equipment, default_internal_problems, default_laws, default_units, province


def country_to_dict(self) -> Dict[str, object]:
    return {
        "name": self.name,
        "capital": self.capital,
        "population": self.population,
        "money": self.money,
        "army": self.army,
        "stability": self.stability,
        "technology": self.technology,
        "relation_to_player": self.relation_to_player,
        "leader": self.leader,
        "color": list(self.color),
        "iso_a3": self.iso_a3,
        "iso_a2": self.iso_a2,
        "continent": self.continent,
        "flag_colors": [list(color) for color in self.flag_colors],
        "is_core_country": self.is_core_country,
        "economy": self.economy,
        "influence": self.influence,
        "territory_points": self.territory_points,
        "party": self.party,
        "government_type": self.government_type,
        "next_election_year": self.next_election_year,
        "leader_pool": self.leader_pool,
        "laws": self.laws,
        "resources": self.resources,
        "provinces": self.provinces,
        "units": self.units,
        "buildings": self.buildings,
        "equipment": self.equipment,
        "debt": self.debt,
        "inflation": self.inflation,
        "last_month_income": self.last_month_income,
        "last_month_expenses": self.last_month_expenses,
        "last_month_balance": self.last_month_balance,
        "internal_problems": self.internal_problems,
        "vassal_of": self.vassal_of,
        "vassals": sorted(self.vassals),
        "allies": sorted(self.allies),
        "wars": sorted(self.wars),
        "relations": self.relations,
        "spouse": self.spouse,
        "lover": self.lover,
        "children": self.children,
    }


def country_from_dict(cls, data: Dict[str, object]):
    name = str(data["name"])
    country = cls(
        name=name,
        capital=str(data.get("capital", f"{name} Capital")),
        population=float(data.get("population", 1.0)),
        money=int(data.get("money", 300)),
        army=int(data.get("army", 0)),
        stability=int(data.get("stability", 65)),
        technology=int(data.get("technology", 4)),
        relation_to_player=int(data.get("relation_to_player", 0)),
        leader=str(data.get("leader", f"{name} Council")),
        color=tuple(data.get("color", (100, 130, 150))),  # type: ignore[arg-type]
        shape=[tuple(point) for point in data.get("shape", [(0, 0), (10, 0), (10, 10), (0, 10)])],  # type: ignore[arg-type]
        iso_a3=str(data.get("iso_a3", "")),
        iso_a2=str(data.get("iso_a2", "")),
        continent=str(data.get("continent", "")),
        geo_polygons=[
            [(float(point[0]), float(point[1])) for point in ring]
            for ring in data.get("geo_polygons", [])  # type: ignore[union-attr]
        ],
        label_lon=float(data.get("label_lon", 0.0)),
        label_lat=float(data.get("label_lat", 0.0)),
        capital_lon=float(data.get("capital_lon", data.get("label_lon", 0.0))),
        capital_lat=float(data.get("capital_lat", data.get("label_lat", 0.0))),
        flag_colors=[tuple(color) for color in data.get("flag_colors", [])],  # type: ignore[arg-type]
        is_core_country=bool(data.get("is_core_country", False)),
        economy=int(data.get("economy", 5)),
        influence=int(data.get("influence", 25)),
        territory_points=int(data.get("territory_points", 10)),
        party=str(data.get("party", "Conservative")),
        government_type=str(data.get("government_type", "Democracy")),
        next_election_year=int(data.get("next_election_year", 2030)),
        leader_pool=list(data.get("leader_pool", [data.get("leader", "Unknown")])),  # type: ignore[arg-type]
        laws=dict(data.get("laws", default_laws())),  # type: ignore[arg-type]
        resources=dict(data.get("resources", {"oil": 40, "food": 60, "metal": 45})),  # type: ignore[arg-type]
        provinces=list(data.get("provinces", [])),  # type: ignore[arg-type]
        units=dict(data.get("units", default_units())),  # type: ignore[arg-type]
        buildings=dict(data.get("buildings", default_buildings())),  # type: ignore[arg-type]
        equipment=dict(data.get("equipment", default_equipment())),  # type: ignore[arg-type]
        debt=int(data.get("debt", 0)),
        inflation=float(data.get("inflation", 2.0)),
        last_month_income=int(data.get("last_month_income", 0)),
        last_month_expenses=int(data.get("last_month_expenses", 0)),
        last_month_balance=int(data.get("last_month_balance", 0)),
        internal_problems=dict(data.get("internal_problems", default_internal_problems())),  # type: ignore[arg-type]
        vassal_of=data.get("vassal_of"),  # type: ignore[arg-type]
    )
    country.vassals = set(data.get("vassals", []))  # type: ignore[arg-type]
    country.allies = set(data.get("allies", []))  # type: ignore[arg-type]
    country.wars = set(data.get("wars", []))  # type: ignore[arg-type]
    country.relations = dict(data.get("relations", {}))  # type: ignore[arg-type]
    country.spouse = data.get("spouse")  # type: ignore[assignment]
    country.lover = data.get("lover")  # type: ignore[assignment]
    country.children = list(data.get("children", []))  # type: ignore[arg-type]
    country._ensure_laws()
    country._ensure_resources()
    country._ensure_units()
    country._ensure_buildings()
    country._ensure_equipment()
    country._ensure_internal_problems()
    if not country.provinces:
        country.provinces = [province(f"{country.name} Core", country.population, country.economy, 4, 8, 5)]
    country.sync_army_from_units()
    return country




def attach_country_serialization(country_cls) -> None:
    country_cls.to_dict = country_to_dict
    country_cls.from_dict = classmethod(country_from_dict)
