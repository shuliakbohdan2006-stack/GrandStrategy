from __future__ import annotations

import random
from typing import Dict, List, Optional

from core.country_data import RESOURCES, UNIT_POWER, clamp
from core.country_model import Country
from systems.armies import average_morale, average_supply, order_attack, order_defense, order_retreat


class WarMixin:
    def war_id(self, a: str, b: str) -> str:
        return "|".join(sorted([a, b]))

    def get_war_between(self, a: str, b: str) -> Optional[Dict[str, object]]:
        return self.active_wars.get(self.war_id(a, b))

    def get_player_war_with(self, target_name: str) -> Optional[Dict[str, object]]:
        if not self.player_country_name:
            return None
        return self.get_war_between(self.player_country_name, target_name)

    def declare_war(self, attacker_name: Optional[str], defender_name: str, ai_initiated: bool = False) -> None:
        if self.game_over:
            return
        if not attacker_name or attacker_name == defender_name:
            return
        self._start_war(attacker_name, defender_name, ai_initiated=ai_initiated, silent=False)

    def resolve_war(self, attacker_name: str, defender_name: str, ai_initiated: bool = False) -> None:
        self.declare_war(attacker_name, defender_name, ai_initiated=ai_initiated)

    def _start_war(self, attacker_name: str, defender_name: str, ai_initiated: bool, silent: bool) -> None:
        wid = self.war_id(attacker_name, defender_name)
        if wid in self.active_wars:
            if not silent:
                self.add_message(f"War: {attacker_name} and {defender_name} are already at war.")
            return
        attacker = self.countries[attacker_name]
        defender = self.countries[defender_name]
        self.break_alliance(attacker_name, defender_name)
        attacker.wars.add(defender_name)
        defender.wars.add(attacker_name)
        self.set_relation(attacker_name, defender_name, -90)
        self.active_wars[wid] = {
            "id": wid,
            "attacker": attacker_name,
            "defender": defender_name,
            "start_year": self.date.year,
            "start_month": self.date.month,
            "months": 0,
            "score": 0,
            "status": "active",
            "winner": None,
            "loser": None,
            "casualties": {attacker_name: 0, defender_name: 0},
            "fronts": self._create_fronts(attacker_name, defender_name),
            "ai_initiated": ai_initiated,
        }
        order_attack(self.armies, attacker, defender)
        order_defense(self.armies, defender)
        if not silent:
            prefix = "AI war" if ai_initiated else "War"
            self.add_message(f"{prefix}: {attacker_name} declares a long war on {defender_name}.")

    def process_active_wars(self) -> None:
        for wid, war in list(self.active_wars.items()):
            if war.get("status") == "peace_pending":
                if not self._war_involves_player(war):
                    demand = random.choice(["money", "region", "white_peace"])
                    self.sign_peace(wid, demand, automatic=True)
                continue
            if war.get("status") != "active":
                continue

            attacker = self.countries[str(war["attacker"])]
            defender = self.countries[str(war["defender"])]
            if not war.get("fronts"):
                war["fronts"] = self._create_fronts(attacker.name, defender.name)
            war["months"] = int(war.get("months", 0)) + 1

            attacker_power = self._monthly_war_power(attacker)
            defender_power = self._monthly_war_power(defender)
            total_power = max(1.0, attacker_power + defender_power)
            swing = int(((attacker_power - defender_power) / total_power) * 26 + random.randint(-7, 7))
            if swing == 0:
                swing = 1 if attacker_power >= defender_power else -1
            if average_morale(self.armies, defender.name) < 35 and len([army for army in self.armies if army.country_name == attacker.name and army.stance == "attack"]) >= 2:
                swing += 5
                if self._war_involves_player(war) and random.random() < 0.20:
                    self.add_message(f"Front: {defender.name} forces risk encirclement.")
            if average_morale(self.armies, attacker.name) < 30:
                swing -= 4
            war["score"] = clamp(int(war.get("score", 0)) + swing, -100, 100)
            self._advance_fronts(war, swing)

            attacker_loss = self._monthly_casualties(attacker, defender_power, total_power)
            defender_loss = self._monthly_casualties(defender, attacker_power, total_power)
            self._apply_casualties(attacker, attacker_loss)
            self._apply_casualties(defender, defender_loss)
            casualties = dict(war.get("casualties", {}))
            casualties[attacker.name] = int(casualties.get(attacker.name, 0)) + attacker_loss
            casualties[defender.name] = int(casualties.get(defender.name, 0)) + defender_loss
            war["casualties"] = casualties

            self._consume_war_resources(attacker)
            self._consume_war_resources(defender)
            self.sync_map_armies()

            if self._war_involves_player(war):
                self.add_message(
                    f"War update: {attacker.name} vs {defender.name}, month {war['months']}, score {war['score']}."
                )

            decisive = abs(int(war["score"])) >= 85
            exhausted = int(war["months"]) >= 18 or attacker.army < 40 or defender.army < 40
            if decisive or exhausted:
                winner, loser = self._war_leader(war)
                war["status"] = "peace_pending"
                war["winner"] = winner.name
                war["loser"] = loser.name
                self.add_message(f"Peace available: {winner.name} is winning the war against {loser.name}.")
                if not self._war_involves_player(war):
                    self.sign_peace(wid, random.choice(["money", "region", "vassal"]), automatic=True)

    def _monthly_war_power(self, country: Country) -> float:
        country.sync_army_from_units()
        readiness = country.supply_ratio()
        map_supply = average_supply(self.armies, country.name) / 100
        map_morale = average_morale(self.armies, country.name) / 100
        resource_output = country.resource_output()
        industry_bonus = 1.0 + min(0.22, (resource_output["oil"] + resource_output["metal"]) / 220)
        combined_arms = 1.0
        if country.units["tanks"] > 0 and country.units["artillery"] > 0:
            combined_arms += 0.08
        if country.units["aircraft"] > 0:
            combined_arms += 0.07
        stability_factor = 0.68 + country.stability / 165
        tech_factor = 1.0 + country.technology * 0.085
        influence_factor = 1.0 + country.influence / 420
        return max(1.0, country.army * readiness * (0.70 + map_supply * 0.30) * (0.72 + map_morale * 0.38) * industry_bonus * combined_arms * stability_factor * tech_factor * influence_factor * country.law_war_multiplier() * random.uniform(0.88, 1.12))

    def _monthly_casualties(self, country: Country, enemy_power: float, total_power: float) -> int:
        pressure = enemy_power / max(1.0, total_power)
        rate = random.uniform(0.012, 0.034) + pressure * 0.018
        return max(2, int(country.army * rate))

    def _consume_war_resources(self, country: Country) -> None:
        country.consume_supply(multiplier=1.35)
        if any(country.resources[resource_name] == 0 for resource_name in RESOURCES):
            country.stability = clamp(country.stability - 1, 0, 100)

    def _create_fronts(self, attacker_name: str, defender_name: str) -> List[Dict[str, object]]:
        defender = self.countries[defender_name]
        attacker = self.countries[attacker_name]
        front_count = min(3, max(1, len(defender.provinces)))
        fronts = []
        for index, region in enumerate(defender.provinces[:front_count]):
            lon = defender.label_lon + (index - 1) * 2.2
            lat = defender.label_lat + (index - 1) * 1.1
            if defender.capital_lon:
                lon = (lon + defender.capital_lon + attacker.label_lon) / 3
                lat = (lat + defender.capital_lat + attacker.label_lat) / 3
            fronts.append(
                {
                    "name": f"{attacker_name}-{str(region.get('name', defender_name))}",
                    "target_region": str(region.get("name", defender_name)),
                    "progress": 50,
                    "intensity": random.choice(["low", "medium", "high"]),
                    "lon": lon,
                    "lat": lat,
                    "occupied_by": None,
                }
            )
        return fronts

    def _advance_fronts(self, war: Dict[str, object], swing: int) -> None:
        fronts = list(war.get("fronts", []))
        if not fronts:
            return
        for front in fronts:
            intensity_bonus = {"low": 0.7, "medium": 1.0, "high": 1.25}.get(str(front.get("intensity")), 1.0)
            delta = int((swing / max(1, len(fronts))) * intensity_bonus + random.randint(-3, 3))
            front["progress"] = clamp(int(front.get("progress", 50)) + delta, 0, 100)
            if int(front["progress"]) >= 92:
                front["occupied_by"] = war.get("attacker")
            elif int(front["progress"]) <= 8:
                front["occupied_by"] = war.get("defender")
            else:
                front["occupied_by"] = None
        war["fronts"] = fronts

    def _apply_casualties(self, country: Country, losses: int) -> None:
        remaining = max(0, losses)
        loss_order = ["infantry", "artillery", "tanks", "aircraft"]
        for unit_type in loss_order:
            if remaining <= 0:
                break
            weight = max(1, int(UNIT_POWER[unit_type]))
            units_lost = min(country.units[unit_type], max(0, remaining // weight))
            if units_lost <= 0 and country.units[unit_type] > 0:
                units_lost = 1
            country.units[unit_type] -= units_lost
            remaining -= int(units_lost * UNIT_POWER[unit_type])
        country.sync_army_from_units()

    def _war_involves_player(self, war: Dict[str, object]) -> bool:
        return self.player_country_name in [war.get("attacker"), war.get("defender")]

    def _war_leader(self, war: Dict[str, object]) -> tuple[Country, Country]:
        score = int(war.get("score", 0))
        attacker = self.countries[str(war["attacker"])]
        defender = self.countries[str(war["defender"])]
        return (attacker, defender) if score >= 0 else (defender, attacker)

    def can_offer_peace(self, war: Dict[str, object]) -> bool:
        return war.get("status") == "peace_pending" or int(war.get("months", 0)) >= 4

    def player_peace_demand(self, target_name: str, demand: str) -> None:
        player = self.player_country
        if not player:
            return
        war = self.get_player_war_with(target_name)
        if not war:
            self.add_message(f"Peace: you are not at war with {target_name}.")
            return
        if not self.can_offer_peace(war):
            self.add_message("Peace: the war is too new. Fight at least four months or reach a decisive score.")
            return
        winner, loser = self._war_leader(war)
        if demand != "white_peace" and winner.name != player.name:
            self.add_message("Peace: you are not winning enough to demand concessions.")
            return
        self.sign_peace(str(war["id"]), demand, automatic=False)

    def set_player_army_stance(self, target_name: str, stance: str) -> None:
        player = self.player_country
        target = self.countries.get(target_name)
        if not player or not target:
            return
        war = self.get_player_war_with(target_name)
        if not war:
            self.add_message("Army orders: no active war with selected target.")
            return
        if stance == "attack":
            order_attack(self.armies, player, target)
            self.add_message(f"Army orders: armies advance toward {target.name}.")
        elif stance == "defend":
            order_defense(self.armies, player)
            self.add_message("Army orders: armies dig in around key regions.")
        elif stance == "retreat":
            order_retreat(self.armies, player)
            player.stability = clamp(player.stability - 1, 0, 100)
            self.add_message("Army orders: armies retreat to friendly territory.")

    def sign_peace(self, wid: str, demand: str, automatic: bool = False) -> None:
        war = self.active_wars.get(wid)
        if not war:
            return
        winner, loser = self._war_leader(war)
        summary = "white peace"

        if demand == "money":
            tribute = min(loser.money, max(45, int(loser.money * 0.28)))
            loser.money -= tribute
            winner.money += tribute
            winner.influence += 3
            loser.stability = clamp(loser.stability - 3, 0, 100)
            summary = f"{winner.name} takes {tribute} money from {loser.name}"
        elif demand == "region":
            region_name = self.transfer_region(loser.name, winner.name)
            if region_name:
                winner.influence += 5
                loser.stability = clamp(loser.stability - 6, 0, 100)
                summary = f"{winner.name} takes the {region_name} region from {loser.name}"
            else:
                tribute = min(loser.money, max(30, int(loser.money * 0.18)))
                loser.money -= tribute
                winner.money += tribute
                summary = f"{loser.name} has no spare region, so {winner.name} takes {tribute} money"
        elif demand == "vassal":
            if abs(int(war.get("score", 0))) < 55 and int(war.get("months", 0)) < 8:
                demand = "money"
                tribute = min(loser.money, max(45, int(loser.money * 0.25)))
                loser.money -= tribute
                winner.money += tribute
                summary = f"{winner.name} lacks leverage for vassalage and takes {tribute} money"
            else:
                if loser.vassal_of and loser.vassal_of in self.countries:
                    self.countries[loser.vassal_of].vassals.discard(loser.name)
                loser.vassal_of = winner.name
                winner.vassals.add(loser.name)
                winner.influence += 10
                loser.stability = clamp(loser.stability - 10, 0, 100)
                summary = f"{loser.name} becomes a vassal of {winner.name}"
        elif demand == "white_peace":
            winner.stability = clamp(winner.stability + 1, 0, 100)
            loser.stability = clamp(loser.stability + 1, 0, 100)

        attacker = self.countries[str(war["attacker"])]
        defender = self.countries[str(war["defender"])]
        attacker.wars.discard(defender.name)
        defender.wars.discard(attacker.name)
        order_defense(self.armies, attacker)
        order_defense(self.armies, defender)
        self.sync_map_armies()
        self.set_relation(attacker.name, defender.name, -62)
        del self.active_wars[wid]
        prefix = "AI peace" if automatic else "Peace treaty"
        self.add_message(f"{prefix}: {summary}.")
        self.check_victory_and_game_over()

    def transfer_region(self, loser_name: str, winner_name: str) -> Optional[str]:
        loser = self.countries[loser_name]
        winner = self.countries[winner_name]
        if len(loser.provinces) <= 1:
            return None
        region = max(loser.provinces, key=lambda item: int(item.get("economy", 0)))
        loser.provinces.remove(region)
        winner.provinces.append(region)
        loser.recalculate_from_provinces()
        winner.recalculate_from_provinces()
        return str(region.get("name", "Unknown"))


