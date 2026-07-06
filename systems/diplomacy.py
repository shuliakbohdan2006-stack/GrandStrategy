from __future__ import annotations

import random

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

    def apply_sanctions(self, actor_name: str, target_name: str, announce: bool = True) -> bool:
        if actor_name == target_name:
            return False
        actor = self.countries[actor_name]
        target = self.countries[target_name]
        if target_name in actor.sanctions_against:
            return False
        actor.sanctions_against.add(target_name)
        target.sanctioned_by.add(actor_name)
        actor.trade_agreements.discard(target_name)
        target.trade_agreements.discard(actor_name)
        self.add_relation_delta(actor_name, target_name, -18)
        target.stability = clamp(target.stability - 1, 0, 100)
        if actor_name not in target.sanctions_against and random.random() < 0.30:
            target.sanctions_against.add(actor_name)
            actor.sanctioned_by.add(target_name)
            self.add_relation_delta(actor_name, target_name, -6)
            if announce:
                self.add_message(f"Diplomacy: {target_name} retaliates with counter-sanctions against {actor_name}.")
        if announce:
            self.add_message(f"Diplomacy: {actor_name} imposes sanctions on {target_name}.")
        return True

    def sign_trade_agreement(self, actor_name: str, target_name: str, announce: bool = True) -> bool:
        if actor_name == target_name:
            return False
        actor = self.countries[actor_name]
        target = self.countries[target_name]
        if target_name in actor.trade_agreements:
            return False
        if self.get_relation(actor_name, target_name) < 25:
            return False
        actor.trade_agreements.add(target_name)
        target.trade_agreements.add(actor_name)
        actor.sanctions_against.discard(target_name)
        target.sanctioned_by.discard(actor_name)
        target.sanctions_against.discard(actor_name)
        actor.sanctioned_by.discard(target_name)
        actor.money += 18
        target.money += 18
        self.add_relation_delta(actor_name, target_name, 8)
        if announce:
            self.add_message(f"Diplomacy: {actor_name} and {target_name} sign a trade agreement.")
        return True

    def sign_military_pact(self, actor_name: str, target_name: str, announce: bool = True) -> bool:
        if actor_name == target_name:
            return False
        actor = self.countries[actor_name]
        target = self.countries[target_name]
        if target_name in actor.military_agreements:
            return False
        if self.get_relation(actor_name, target_name) < 45:
            return False
        actor.military_agreements.add(target_name)
        target.military_agreements.add(actor_name)
        actor.army_experience = clamp(actor.army_experience + 2, 0, 100)
        target.army_experience = clamp(target.army_experience + 2, 0, 100)
        self.add_relation_delta(actor_name, target_name, 6)
        if announce:
            self.add_message(f"Diplomacy: {actor_name} and {target_name} sign a military cooperation pact.")
        return True

    def guarantee_independence(self, actor_name: str, target_name: str, announce: bool = True) -> bool:
        if actor_name == target_name:
            return False
        actor = self.countries[actor_name]
        target = self.countries[target_name]
        if target_name in actor.guarantees:
            return False
        if self.get_relation(actor_name, target_name) < 15:
            return False
        actor.guarantees.add(target_name)
        target.guaranteed_by.add(actor_name)
        actor.influence = max(0, actor.influence - 1)
        target.stability = clamp(target.stability + 1, 0, 100)
        self.add_relation_delta(actor_name, target_name, 5)
        if announce:
            self.add_message(f"Diplomacy: {actor_name} guarantees {target_name}'s independence.")
        return True

    def send_ultimatum(self, actor_name: str, target_name: str, announce: bool = True) -> bool:
        if actor_name == target_name:
            return False
        actor = self.countries[actor_name]
        target = self.countries[target_name]
        actor.ultimatums_sent.add(target_name)
        self.add_relation_delta(actor_name, target_name, -22)
        pressure = actor.army * actor.military_readiness() / max(1, target.army * target.military_readiness())
        accepts = pressure > 1.55 and target.stability < 72 and random.random() < 0.58
        if accepts:
            payment = min(target.money, max(25, int(target.monthly_income() * 0.35)))
            target.money -= payment
            actor.money += payment
            actor.influence += 2
            target.stability = clamp(target.stability - 3, 0, 100)
            actor.ultimatum_outcomes[target_name] = "accepted_payment"
            target.ultimatum_outcomes[actor_name] = "accepted_payment"
            if announce:
                self.add_message(f"Diplomacy: {target_name} accepts {actor_name}'s ultimatum and pays {payment}.")
        else:
            actor.influence += 1
            target.army_morale = clamp(target.army_morale + 1, 0, 100)
            actor.ultimatum_outcomes[target_name] = "rejected"
            target.ultimatum_outcomes[actor_name] = "rejected"
            if announce:
                self.add_message(f"Diplomacy: {target_name} rejects {actor_name}'s ultimatum.")
        return True

    def player_impose_sanctions(self, target_name: str) -> None:
        player = self.player_country
        if not player:
            return
        if self.get_relation(player.name, target_name) > -20:
            self.add_message("Diplomacy: sanctions require poor relations.")
            return
        if self.apply_sanctions(player.name, target_name):
            self.add_message(f"Diplomacy: sanctions will weaken {target_name}'s economy over time.")
        else:
            self.add_message(f"Diplomacy: sanctions against {target_name} are already active.")

    def player_trade_agreement(self, target_name: str) -> None:
        player = self.player_country
        if not player:
            return
        cost = 55
        if player.money < cost:
            self.add_message(f"Diplomacy: need {cost} money to prepare a trade agreement.")
            return
        player.money -= cost
        if not self.sign_trade_agreement(player.name, target_name):
            player.money += cost
            self.add_message("Diplomacy: trade agreement requires relations of at least 25.")

    def player_military_pact(self, target_name: str) -> None:
        player = self.player_country
        if not player:
            return
        cost = 70
        if player.money < cost:
            self.add_message(f"Diplomacy: need {cost} money for joint exercises.")
            return
        player.money -= cost
        if not self.sign_military_pact(player.name, target_name):
            player.money += cost
            self.add_message("Diplomacy: military pact requires relations of at least 45.")

    def player_guarantee_independence(self, target_name: str) -> None:
        player = self.player_country
        if not player:
            return
        if not self.guarantee_independence(player.name, target_name):
            self.add_message("Diplomacy: guarantee requires relations of at least 15.")

    def player_send_ultimatum(self, target_name: str) -> None:
        player = self.player_country
        if not player:
            return
        if player.stability < 45:
            self.add_message("Diplomacy: your state is too unstable to issue an ultimatum.")
            return
        self.send_ultimatum(player.name, target_name)
