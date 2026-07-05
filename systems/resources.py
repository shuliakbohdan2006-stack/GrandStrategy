from __future__ import annotations

from core.country_data import RESOURCES


class ResourceMixin:
    def trade_resource(self, target_name: str, resource_name: str, mode: str) -> None:
        player = self.player_country
        if not player or target_name not in self.countries or resource_name not in RESOURCES:
            return
        target = self.countries[target_name]
        if target.name == player.name:
            return
        relation = self.get_relation(player.name, target.name)
        if relation < -35:
            self.add_message(f"Trade: {target.name} refuses due to poor relations.")
            return
        amount = 20
        base_prices = {"oil": 7, "food": 4, "metal": 6}
        price = int(amount * base_prices[resource_name] * (1 + max(0, player.inflation - 2) / 120))
        if mode == "buy":
            if target.resources.get(resource_name, 0) < amount:
                self.add_message(f"Trade: {target.name} lacks enough {resource_name}.")
                return
            if player.money < price:
                self.add_message(f"Trade: need {price} money to buy {resource_name}.")
                return
            player.money -= price
            target.money += price
            target.resources[resource_name] -= amount
            player.resources[resource_name] += amount
            self.add_message(f"Trade: bought {amount} {resource_name} from {target.name} for {price}.")
        elif mode == "sell":
            if player.resources.get(resource_name, 0) < amount:
                self.add_message(f"Trade: you lack enough {resource_name}.")
                return
            if target.money < price:
                self.add_message(f"Trade: {target.name} cannot pay {price}.")
                return
            player.resources[resource_name] -= amount
            target.resources[resource_name] += amount
            target.money -= price
            player.money += price
            self.add_message(f"Trade: sold {amount} {resource_name} to {target.name} for {price}.")
