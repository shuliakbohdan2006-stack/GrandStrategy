from __future__ import annotations

from core.country_data import BUILDING_TYPES, RESOURCES, UNIT_TYPES, WEAPON_BATCHES


class ConstructionMixin:
    def player_build_structure(self, building_type: str) -> None:
        country = self.player_country
        if not country or building_type not in BUILDING_TYPES:
            return
        full_cost = country.build_cost(building_type)
        money = full_cost.get("money", 0)
        resource_cost = {key: value for key, value in full_cost.items() if key in RESOURCES}
        if country.build_structure(building_type):
            self.add_message(f"Construction: built {building_type.replace('_', ' ')} for {money} money.")
        else:
            shortage = country.resource_shortage_text(resource_cost)
            self.add_message(f"Construction: need {money} money and resources ({shortage}).")

    def player_produce_weapons(self, unit_type: str) -> None:
        country = self.player_country
        if not country or unit_type not in UNIT_TYPES:
            return
        batch = WEAPON_BATCHES[unit_type]
        resource_cost = {key: int(batch[key]) for key in RESOURCES}
        if country.produce_weapon_batch(unit_type):
            self.sync_map_armies()
            self.add_message(f"Production: produced {batch['amount']} {unit_type}. Army strength is now {country.army}.")
        else:
            shortage = country.resource_shortage_text(resource_cost)
            self.add_message(f"Production: need {batch['money']} money and resources ({shortage}).")
