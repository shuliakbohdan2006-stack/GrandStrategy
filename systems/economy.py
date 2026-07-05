from __future__ import annotations

class EconomyMixin:
    def player_invest_economy(self) -> None:
        country = self.player_country
        if not country:
            return
        cost = country.invest_cost()
        resource_cost = country.invest_resource_cost()
        if country.invest_in_economy():
            self.add_message(
                f"Economy: invested {cost} and metal {resource_cost['metal']}. Economy level is now {country.economy}."
            )
        else:
            shortage = country.resource_shortage_text(resource_cost)
            self.add_message(f"Economy: need {cost} money and resources ({shortage}).")

    def player_recruit_soldiers(self) -> None:
        country = self.player_country
        if not country:
            return
        old_army = country.army
        cost = country.recruit_cost()
        resource_cost = country.recruit_resource_cost()
        if country.recruit_soldiers():
            self.sync_map_armies()
            self.add_message(f"Army: recruited {country.army - old_army} soldiers. Cost {cost}, resources spent.")
        else:
            shortage = country.resource_shortage_text(resource_cost)
            self.add_message(f"Army: need {cost} money and resources ({shortage}).")


