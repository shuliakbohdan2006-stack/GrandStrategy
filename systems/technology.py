from __future__ import annotations


class TechnologyMixin:
    def player_research_technology(self) -> None:
        country = self.player_country
        if not country:
            return
        cost = country.tech_cost()
        resource_cost = country.tech_resource_cost()
        if country.research_technology():
            self.add_message(f"Technology: researched level {country.technology}. Cost {cost}.")
        else:
            shortage = country.resource_shortage_text(resource_cost)
            self.add_message(f"Technology: need {cost} money and resources ({shortage}).")
