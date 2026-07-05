from __future__ import annotations

import random
from typing import Dict

from core.country_data import LAW_OPTIONS, PARTIES, clamp


class GovernanceMixin:
    def set_victory_goal(self, goal: str) -> None:
        if goal not in ["world_conquest", "economic_dominance", "diplomatic_dominance"]:
            return
        self.victory_goal = goal
        labels = {
            "world_conquest": "World conquest",
            "economic_dominance": "Economic dominance",
            "diplomatic_dominance": "Diplomatic dominance",
        }
        self.add_notification("Victory goal selected", labels[goal], pause=False)

    def toggle_setting(self, setting: str) -> None:
        if setting in ["sound", "autosave"]:
            self.settings[setting] = not bool(self.settings.get(setting, False))
            self.add_message(f"Settings: {setting} {'on' if self.settings[setting] else 'off'}.")

    def cycle_difficulty(self) -> None:
        options = ["Easy", "Normal", "Hard"]
        current = str(self.settings.get("difficulty", "Normal"))
        next_value = options[(options.index(current) + 1) % len(options)] if current in options else "Normal"
        self.settings["difficulty"] = next_value
        self.add_message(f"Settings: difficulty set to {next_value}.")

    def difficulty_pressure(self) -> float:
        return {"Easy": 0.78, "Normal": 1.0, "Hard": 1.25}.get(str(self.settings.get("difficulty", "Normal")), 1.0)

    def process_internal_problems(self) -> None:
        for country in self.countries.values():
            problems = country.internal_problems
            pressure = self.difficulty_pressure() if country.name == self.player_country_name else 1.0

            protests_delta = 0
            if country.stability < 55:
                protests_delta += 2
            if country.inflation > 10:
                protests_delta += 1
            if country.last_month_balance < -100:
                protests_delta += 1
            if country.laws["censorship"] == "State Media":
                protests_delta -= 1
            if country.stability > 72 and country.last_month_balance >= 0:
                protests_delta -= 2
            problems["protests"] = clamp(problems["protests"] + int(protests_delta * pressure), 0, 100)

            corruption_delta = 1 if country.money > 2500 or country.laws["censorship"] == "State Media" else 0
            if country.laws["taxes"] == "Low":
                corruption_delta -= 1
            if random.random() < 0.18:
                corruption_delta += random.choice([-1, 0, 1])
            problems["corruption"] = clamp(problems["corruption"] + int(corruption_delta * pressure), 0, 100)

            separatism_delta = 0
            if country.stability < 45:
                separatism_delta += 1
            if len(country.provinces) > 5:
                separatism_delta += 1
            if country.vassal_of:
                separatism_delta += 1
            if country.stability > 70:
                separatism_delta -= 1
            problems["separatism"] = clamp(problems["separatism"] + int(separatism_delta * pressure), 0, 100)

            crisis_delta = 0
            if problems["protests"] > 65:
                crisis_delta += 2
            if country.debt > 6000:
                crisis_delta += 1
            if country.stability < 35:
                crisis_delta += 2
            if country.stability > 75 and problems["protests"] < 35:
                crisis_delta -= 2
            problems["government_crisis"] = clamp(problems["government_crisis"] + int(crisis_delta * pressure), 0, 100)

            if problems["protests"] > 75:
                country.stability = clamp(country.stability - 2, 0, 100)
            if problems["government_crisis"] > 80:
                country.stability = clamp(country.stability - 3, 0, 100)
            if problems["separatism"] > 85 and len(country.provinces) > 1 and random.random() < 0.12:
                lost = country.provinces.pop()
                country.recalculate_from_provinces()
                country.stability = clamp(country.stability - 8, 0, 100)
                if country.name == self.player_country_name:
                    self.add_notification("Separatist crisis", f"{lost.get('name', 'A region')} has broken away from your control.")

            if country.name == self.player_country_name:
                if problems["protests"] >= 70 and random.random() < 0.25:
                    self.add_notification("Mass protests", "Protests are threatening state stability.")
                if problems["government_crisis"] >= 75 and random.random() < 0.25:
                    self.add_notification("Government crisis", "Your cabinet is close to collapse.")

    def change_player_party(self, party: str) -> None:
        player = self.player_country
        if not player:
            return
        if party not in PARTIES:
            return
        old_party = player.party
        if player.change_party(party):
            self.sync_map_armies()
            if party == "Nationalist":
                for target in self.target_names():
                    self.add_relation_delta(player.name, target, -4)
            self.add_message(f"Politics: party changed from {old_party} to {party}.")
        else:
            self.add_message(f"Politics: {party} is already in power.")

    def change_player_law(self, category: str, value: str) -> None:
        player = self.player_country
        if not player:
            return
        if category not in LAW_OPTIONS:
            return
        old = player.laws.get(category)
        if player.change_law(category, value):
            self.add_message(f"Laws: {category.replace('_', ' ')} changed from {old} to {value}.")
        else:
            self.add_message(f"Laws: {value} is already selected for {category.replace('_', ' ')}.")

    def process_elections(self) -> None:
        for country in self.countries.values():
            if country.is_democratic and self.date.year >= country.next_election_year:
                self.run_election(country.name, forced=False)

    def victory_progress(self) -> Dict[str, object]:
        player = self.player_country
        if not player or not self.victory_goal:
            return {"goal": "none", "label": "Select a goal", "value": 0, "target": 1}
        others = [country for country in self.countries.values() if country.name != player.name]
        if self.victory_goal == "world_conquest":
            controlled = sum(1 for country in others if country.vassal_of == player.name)
            return {"goal": "world conquest", "label": "controlled", "value": controlled, "target": len(others)}
        if self.victory_goal == "economic_dominance":
            global_income = sum(country.monthly_income() for country in self.countries.values())
            share = int(player.monthly_income() / max(1, global_income) * 100)
            return {"goal": "economic dominance", "label": "world income %", "value": share, "target": 45}
        if self.victory_goal == "diplomatic_dominance":
            aligned = sum(1 for country in others if country.name in player.allies or country.vassal_of == player.name or self.get_relation(player.name, country.name) >= 70)
            return {"goal": "diplomatic dominance", "label": "aligned", "value": aligned, "target": max(6, len(others) - 1)}
        return {"goal": "unknown", "label": "progress", "value": 0, "target": 1}

    def check_victory_and_game_over(self) -> None:
        if self.game_over or not self.player_country_name:
            return
        player = self.player_country
        if not player:
            return

        if player.debt > 12000:
            self.end_game("Debt default", "Your country can no longer service its debt.")
            return
        if player.stability <= 3:
            self.end_game("State collapse", "Stability fell to zero and the government collapsed.")
            return
        if player.vassal_of:
            self.end_game("Country subjugated", f"{player.name} has become a vassal of {player.vassal_of}.")
            return
        if len(player.provinces) <= 0:
            self.end_game("Country conquered", "You no longer control any regions.")
            return
        if player.internal_problems["government_crisis"] >= 100:
            self.end_game("Government collapse", "The crisis consumed the state.")
            return

        if not self.victory_goal:
            return
        others = [country for country in self.countries.values() if country.name != player.name]
        if self.victory_goal == "world_conquest":
            controlled = sum(1 for country in others if country.vassal_of == player.name)
            if controlled >= len(others):
                self.end_game("Victory", "World conquest achieved.", victory=True)
        elif self.victory_goal == "economic_dominance":
            global_income = sum(country.monthly_income() for country in self.countries.values())
            if player.monthly_income() >= global_income * 0.45 and player.money >= 5000 and player.debt < 2500:
                self.end_game("Victory", "Economic dominance achieved.", victory=True)
        elif self.victory_goal == "diplomatic_dominance":
            aligned = sum(1 for country in others if country.name in player.allies or country.vassal_of == player.name or self.get_relation(player.name, country.name) >= 70)
            if aligned >= max(6, len(others) - 1) and player.influence >= 85:
                self.end_game("Victory", "Diplomatic dominance achieved.", victory=True)

    def end_game(self, title: str, reason: str, victory: bool = False) -> None:
        self.game_over = True
        self.game_over_reason = f"{title}: {reason}"
        self.speed = 0
        self.add_notification(title, reason, pause=True)

    def call_player_election(self) -> None:
        player = self.player_country
        if not player:
            return
        if not player.is_democratic:
            self.add_message("Election: this government does not hold competitive elections.")
            return
        self.run_election(player.name, forced=True)

    def run_election(self, country_name: str, forced: bool) -> None:
        country = self.countries[country_name]
        old_leader = country.leader
        choices = [name for name in country.leader_pool if name != old_leader] or country.leader_pool
        country.leader = random.choice(choices)
        country.party = random.choice(PARTIES)
        country.next_election_year = self.date.year + 4
        country.stability = clamp(country.stability + random.randint(-5, 5), 0, 100)
        label = "snap election" if forced else "election"
        if country.name == self.player_country_name or random.random() < 0.28:
            self.add_message(f"{label.title()}: {country.name} chooses {country.leader} ({country.party}).")


