from __future__ import annotations

from core.country_data import clamp


class DiplomacyMixin:
    def improve_relations(self, target_name: str) -> None:
        player = self.player_country
        if not player or target_name == player.name:
            return
        cost = 45
        if player.money < cost:
            self.add_message(f"Diplomacy: need {cost} money for a state visit.")
            return
        player.money -= cost
        self.add_relation_delta(player.name, target_name, 14)
        self.add_message(f"Diplomacy: relations with {target_name} improved to {self.get_relation(player.name, target_name)}.")

    def worsen_relations(self, target_name: str) -> None:
        player = self.player_country
        if not player or target_name == player.name:
            return
        self.add_relation_delta(player.name, target_name, -16)
        player.stability = clamp(player.stability - 1, 0, 100)
        self.add_message(f"Diplomacy: relations with {target_name} worsened to {self.get_relation(player.name, target_name)}.")

    def offer_alliance(self, target_name: str) -> None:
        player = self.player_country
        if not player or target_name == player.name:
            return
        relation = self.get_relation(player.name, target_name)
        if relation < 50:
            self.add_message(f"Diplomacy: {target_name} refuses. Relations must be at least 50.")
            return
        cost = 60
        if player.money < cost:
            self.add_message(f"Diplomacy: need {cost} money for treaty guarantees.")
            return
        player.money -= cost
        self.make_alliance(player.name, target_name)


