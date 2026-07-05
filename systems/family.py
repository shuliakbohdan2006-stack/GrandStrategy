from __future__ import annotations

import random

from core.country_data import clamp
from systems.events import LOVER_NAMES, SPOUSE_NAMES, maybe_add_child


class FamilyMixin:
    def choose_spouse(self) -> None:
        player = self.player_country
        if not player:
            return
        if player.spouse:
            self.add_message(f"Family: you are already married to {player.spouse}.")
            return
        cost = 35
        if player.money < cost:
            self.add_message(f"Family: a royal wedding needs {cost} money.")
            return
        player.money -= cost
        player.spouse = random.choice(SPOUSE_NAMES)
        player.stability = clamp(player.stability + 5, 0, 100)
        self.add_message(f"Family: you married {player.spouse}. Stability rises.")

    def choose_lover(self) -> None:
        player = self.player_country
        if not player:
            return
        if player.lover:
            self.add_message(f"Family: {player.lover} is already your private companion.")
            return
        player.lover = random.choice(LOVER_NAMES)
        player.influence += 1
        self.add_message(f"Family: {player.lover} becomes a private companion at court.")

    def try_for_child(self) -> None:
        player = self.player_country
        if not player:
            return
        if not player.spouse and not player.lover:
            self.add_message("Family: you need a spouse or companion before heirs can appear.")
            return
        if random.random() < 0.55:
            name = maybe_add_child(player)
            player.stability = clamp(player.stability + 2, 0, 100)
            self.add_message(f"Family: {name} is born. A new heir enters the line.")
        else:
            self.add_message("Family: no child this time.")

    def divorce(self) -> None:
        player = self.player_country
        if not player:
            return
        if not player.spouse:
            self.add_message("Family: you are not married.")
            return
        old = player.spouse
        player.spouse = None
        player.stability = clamp(player.stability - 10, 0, 100)
        self.add_message(f"Family: divorce from {old}. Stability falls.")


