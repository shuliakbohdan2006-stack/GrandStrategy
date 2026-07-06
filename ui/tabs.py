from __future__ import annotations

import pygame

from core.country_data import BUILDING_TYPES, LAW_OPTIONS, PARTIES, RESOURCES, UNIT_TYPES, WEAPON_BATCHES
from localization import tr
from ui.actions import action_none
from ui.helpers import draw_fitted_text, draw_panel, draw_text
from ui.layout import ACTION_RECT


class UITabsMixin:
    def _draw_tab_panel(self, screen: pygame.Surface, state: GameState) -> None:
        panel = ACTION_RECT
        draw_panel(screen, panel, (38, 48, 55))
        title_icons = {
            "Overview": "victory",
            "Economy": "economy",
            "Army": "army",
            "Production": "factory",
            "Construction": "construction",
            "Trade": "trade",
            "Diplomacy": "diplomacy",
            "Politics": "politics",
            "Laws": "government",
            "Family": "family",
            "War": "war",
            "Technology": "technology",
            "Statistics": "statistics",
        }
        title_icon = self.assets.get_icon(title_icons.get(state.current_tab, "menu"), (24, 24))
        screen.blit(title_icon, (panel.x + 18, panel.y + 14))
        draw_text(screen, tr(f"tabs.{state.current_tab.lower()}"), (panel.x + 50, panel.y + 12), self.title_font, (238, 241, 244))
        if state.current_tab == "Overview":
            self._draw_overview_tab(screen, state, panel)
        elif state.current_tab == "Economy":
            self._draw_economy_tab(screen, state, panel)
        elif state.current_tab == "Army":
            self._draw_army_tab(screen, state, panel)
        elif state.current_tab == "Production":
            self._draw_production_tab(screen, state, panel)
        elif state.current_tab == "Construction":
            self._draw_construction_tab(screen, state, panel)
        elif state.current_tab == "Trade":
            self._draw_trade_tab(screen, state, panel)
        elif state.current_tab == "Diplomacy":
            self._draw_diplomacy_tab(screen, state, panel)
        elif state.current_tab == "Politics":
            self._draw_politics_tab(screen, state, panel)
        elif state.current_tab == "Laws":
            self._draw_laws_tab(screen, state, panel)
        elif state.current_tab == "Family":
            self._draw_family_tab(screen, state, panel)
        elif state.current_tab == "War":
            self._draw_war_tab(screen, state, panel)
        elif state.current_tab == "Technology":
            self._draw_technology_tab(screen, state, panel)
        elif state.current_tab == "Statistics":
            self._draw_statistics_tab(screen, state, panel)

    def _draw_overview_tab(self, screen: pygame.Surface, state: GameState, panel: pygame.Rect) -> None:
        player = state.player_country
        if not player:
            return
        progress = state.victory_progress()
        problems = player.internal_problems
        active_wars = len([war for war in state.active_wars.values() if player.name in [war.get("attacker"), war.get("defender")]])
        draw_text(screen, tr("tab.overview.dashboard"), (panel.x + 18, panel.y + 45), self.small_font, (197, 207, 216))
        lines = [
            f"Power {player.national_power_score()} | Economy {player.economy} | Regional economy {player.regional_economy()}",
            f"GDP {player.gdp} | GDP per capita {player.gdp_per_capita()} | Unemployment {player.unemployment:.1f}%",
            f"Army {player.army} | Units I{player.units['infantry']} T{player.units['tanks']} A{player.units['artillery']} Air{player.units['aircraft']}",
            f"Resources oil {player.resources['oil']} food {player.resources['food']} metal {player.resources['metal']}",
            f"Stability {player.stability} | Education {player.education} | Healthcare {player.healthcare} | Wars {active_wars}",
            f"Debt {player.debt} | Inflation {player.inflation:.1f}% | Tax income {player.tax_income} | Military spending {player.military_spending}",
            f"Problems P{problems['protests']} C{problems['corruption']} S{problems['separatism']} G{problems['government_crisis']}",
            f"Victory goal: {progress['goal']} | {progress['label']} {progress['value']}/{progress['target']}",
        ]
        y = panel.y + 68
        for line in lines:
            draw_text(screen, line, (panel.x + 18, y), self.tiny_font, (197, 207, 216))
            y += 18

        goal_x = panel.x + 595
        self._add_button(
            pygame.Rect(goal_x, panel.y + 50, 190, 30),
            tr("victory.world_conquest"),
            lambda s: action_none(s.set_victory_goal("world_conquest")),
            active=state.victory_goal == "world_conquest",
            tooltip="Win by controlling or vassalizing every country.",
            icon="victory",
        )
        self._add_button(
            pygame.Rect(goal_x, panel.y + 86, 190, 30),
            tr("victory.economic"),
            lambda s: action_none(s.set_victory_goal("economic_dominance")),
            active=state.victory_goal == "economic_dominance",
            tooltip="Win by building a dominant economy and low debt.",
            icon="economy",
        )
        self._add_button(
            pygame.Rect(goal_x, panel.y + 122, 190, 30),
            tr("victory.diplomatic"),
            lambda s: action_none(s.set_victory_goal("diplomatic_dominance")),
            active=state.victory_goal == "diplomatic_dominance",
            tooltip="Win through allies and vassals.",
            icon="diplomacy",
        )

    def _draw_economy_tab(self, screen: pygame.Surface, state: GameState, panel: pygame.Rect) -> None:
        player = state.player_country
        if not player:
            return
        output = player.resource_output()
        draw_text(screen, f"Income: {player.monthly_income()} | Expenses: {player.monthly_expenses()} | Last balance: {player.last_month_balance}", (panel.x + 18, panel.y + 50), self.small_font, (197, 207, 216))
        draw_text(screen, f"Debt: {player.debt} | Inflation: {player.inflation:.1f}% | Investment cost: {player.invest_cost()} + metal {player.invest_resource_cost()['metal']}", (panel.x + 18, panel.y + 75), self.small_font, (197, 207, 216))
        draw_text(screen, f"Output: oil {output['oil']}, food {output['food']}, metal {output['metal']} | Regional economy: {player.regional_economy()}", (panel.x + 18, panel.y + 100), self.small_font, (197, 207, 216))
        self._add_button(pygame.Rect(panel.x + 18, panel.y + 112, 190, 36), tr("action.invest_economy"), lambda s: action_none(s.player_invest_economy()), icon="economy")

    def _draw_army_tab(self, screen: pygame.Surface, state: GameState, panel: pygame.Rect) -> None:
        player = state.player_country
        if not player:
            return
        rc = player.recruit_resource_cost()
        supply = player.supply_need()
        draw_text(screen, f"Army strength: {player.army} | Supply need/month O{supply['oil']} F{supply['food']} M{supply['metal']} | Readiness {int(player.supply_ratio()*100)}%", (panel.x + 18, panel.y + 50), self.small_font, (197, 207, 216))
        draw_text(screen, f"Units: infantry {player.units['infantry']}, tanks {player.units['tanks']}, artillery {player.units['artillery']}, aircraft {player.units['aircraft']}", (panel.x + 18, panel.y + 75), self.small_font, (197, 207, 216))
        draw_text(screen, f"Recruit cost: {player.recruit_cost()} | Needs O{rc['oil']} F{rc['food']} M{rc['metal']} | Conscription: {player.laws['conscription']}", (panel.x + 18, panel.y + 100), self.small_font, (197, 207, 216))
        self._add_button(pygame.Rect(panel.x + 18, panel.y + 112, 190, 36), tr("action.recruit_soldiers"), lambda s: action_none(s.player_recruit_soldiers()), icon="army")

    def _draw_production_tab(self, screen: pygame.Surface, state: GameState, panel: pygame.Rect) -> None:
        player = state.player_country
        if not player:
            return
        draw_text(screen, f"Factories: {player.buildings['factory']} | Equipment stock: I{player.equipment['infantry']} T{player.equipment['tanks']} A{player.equipment['artillery']} Air{player.equipment['aircraft']}", (panel.x + 18, panel.y + 50), self.small_font, (197, 207, 216))
        x = panel.x + 18
        for unit_type in UNIT_TYPES:
            batch = WEAPON_BATCHES[unit_type]
            label = f"{unit_type} +{batch['amount']}"
            self._add_button(pygame.Rect(x, panel.y + 92, 150, 34), label, lambda s, u=unit_type: action_none(s.player_produce_weapons(u)), icon="factory")
            draw_text(screen, f"${batch['money']} O{batch['oil']} F{batch['food']} M{batch['metal']}", (x + 4, panel.y + 130), self.tiny_font, (169, 179, 188))
            x += 160

    def _draw_construction_tab(self, screen: pygame.Surface, state: GameState, panel: pygame.Rect) -> None:
        player = state.player_country
        if not player:
            return
        draw_text(screen, f"Buildings: factories {player.buildings['factory']}, farms {player.buildings['farm']}, oil fields {player.buildings['oil_field']}, mines {player.buildings['mine']}", (panel.x + 18, panel.y + 50), self.small_font, (197, 207, 216))
        x = panel.x + 18
        for building_type in BUILDING_TYPES:
            cost = player.build_cost(building_type)
            icon = "oil" if building_type == "oil_field" else "mine" if building_type == "mine" else building_type
            self._add_button(pygame.Rect(x, panel.y + 92, 150, 34), building_type.replace("_", " "), lambda s, b=building_type: action_none(s.player_build_structure(b)), icon=icon)
            draw_text(screen, f"${cost['money']} O{cost['oil']} F{cost['food']} M{cost['metal']}", (x + 4, panel.y + 130), self.tiny_font, (169, 179, 188))
            x += 160

    def _draw_trade_tab(self, screen: pygame.Surface, state: GameState, panel: pygame.Rect) -> None:
        self._draw_target_list(screen, state, pygame.Rect(panel.x + 18, panel.y + 50, 350, 92))
        target = state.selected_target
        player = state.player_country
        if not target or not player:
            return
        draw_text(screen, f"Trade partner: {target.name} | Relation {state.get_relation(player.name, target.name)} | Partner O{target.resources['oil']} F{target.resources['food']} M{target.resources['metal']}", (panel.x + 390, panel.y + 50), self.small_font, (197, 207, 216))
        x = panel.x + 390
        for resource_name in RESOURCES:
            self._add_button(pygame.Rect(x, panel.y + 86, 92, 30), f"{tr('action.buy')} {resource_name}", lambda s, r=resource_name, n=target.name: action_none(s.trade_resource(n, r, "buy")), icon="trade")
            self._add_button(pygame.Rect(x, panel.y + 122, 92, 30), f"{tr('action.sell')} {resource_name}", lambda s, r=resource_name, n=target.name: action_none(s.trade_resource(n, r, "sell")), icon="trade")
            x += 102

    def _draw_diplomacy_tab(self, screen: pygame.Surface, state: GameState, panel: pygame.Rect) -> None:
        self._draw_target_list(screen, state, pygame.Rect(panel.x + 18, panel.y + 50, 350, 92))
        target = state.selected_target
        if target:
            relation = state.get_relation(state.player_country_name, target.name)  # type: ignore[arg-type]
            draw_text(screen, f"Target: {target.name} | Relation: {relation} | Leader: {target.leader}", (panel.x + 390, panel.y + 52), self.small_font, (197, 207, 216))
            treaty_line = f"Trade {'yes' if target.name in state.player_country.trade_agreements else 'no'} | Military {'yes' if target.name in state.player_country.military_agreements else 'no'} | Sanctions {'yes' if target.name in state.player_country.sanctions_against else 'no'}"  # type: ignore[union-attr]
            draw_text(screen, treaty_line, (panel.x + 390, panel.y + 72), self.tiny_font, (169, 179, 188))
            self._add_button(pygame.Rect(panel.x + 390, panel.y + 86, 120, 34), tr("action.improve"), lambda s, n=target.name: action_none(s.improve_relations(n)), icon="diplomacy")
            self._add_button(pygame.Rect(panel.x + 520, panel.y + 86, 120, 34), tr("action.worsen"), lambda s, n=target.name: action_none(s.worsen_relations(n)), icon="war")
            self._add_button(pygame.Rect(panel.x + 650, panel.y + 86, 165, 34), tr("action.offer_alliance"), lambda s, n=target.name: action_none(s.offer_alliance(n)), icon="diplomacy")
            self._add_button(pygame.Rect(panel.x + 390, panel.y + 126, 92, 30), tr("action.sanction"), lambda s, n=target.name: action_none(s.player_impose_sanctions(n)), icon="diplomacy")
            self._add_button(pygame.Rect(panel.x + 488, panel.y + 126, 92, 30), tr("action.trade_agreement"), lambda s, n=target.name: action_none(s.player_trade_agreement(n)), icon="trade")
            self._add_button(pygame.Rect(panel.x + 586, panel.y + 126, 92, 30), tr("action.military_pact"), lambda s, n=target.name: action_none(s.player_military_pact(n)), icon="army")
            self._add_button(pygame.Rect(panel.x + 684, panel.y + 126, 92, 30), tr("action.guarantee"), lambda s, n=target.name: action_none(s.player_guarantee_independence(n)), icon="stability")
            self._add_button(pygame.Rect(panel.x + 782, panel.y + 126, 92, 30), tr("action.ultimatum"), lambda s, n=target.name: action_none(s.player_send_ultimatum(n)), icon="war")

    def _draw_politics_tab(self, screen: pygame.Surface, state: GameState, panel: pygame.Rect) -> None:
        player = state.player_country
        if not player:
            return
        draw_text(screen, f"Leader: {player.leader} | Government: {player.government_type} | Current party: {player.party}", (panel.x + 18, panel.y + 50), self.small_font, (197, 207, 216))
        if player.is_democratic:
            draw_text(screen, f"Next election year: {player.next_election_year}", (panel.x + 18, panel.y + 74), self.small_font, (197, 207, 216))
        x = panel.x + 18
        y = panel.y + 106
        for party in PARTIES:
            self._add_button(
                pygame.Rect(x, y, 116, 34),
                party,
                lambda s, p=party: action_none(s.change_player_party(p)),
                active=party == player.party,
            )
            x += 123
        self._add_button(pygame.Rect(panel.x + 540, panel.y + 106, 170, 34), tr("action.call_election"), lambda s: action_none(s.call_player_election()), enabled=player.is_democratic, icon="politics")

    def _draw_laws_tab(self, screen: pygame.Surface, state: GameState, panel: pygame.Rect) -> None:
        player = state.player_country
        if not player:
            return
        rows = [
            ("taxes", "Taxes"),
            ("conscription", "Conscription"),
            ("censorship", "Censorship"),
            ("trade_policy", "Trade"),
        ]
        y = panel.y + 48
        for category, label in rows:
            draw_text(screen, label, (panel.x + 18, y + 6), self.small_font, (197, 207, 216))
            x = panel.x + 132
            for option in LAW_OPTIONS[category]:
                self._add_button(
                    pygame.Rect(x, y, 116, 28),
                    option,
                    lambda s, c=category, o=option: action_none(s.change_player_law(c, o)),
                    active=player.laws.get(category) == option,
                )
                x += 126
            y += 32

    def _draw_family_tab(self, screen: pygame.Surface, state: GameState, panel: pygame.Rect) -> None:
        player = state.player_country
        if not player:
            return
        spouse = player.spouse or "none"
        lover = player.lover or "none"
        heirs = ", ".join(f"{c['name']}({c['age']})" for c in player.children) or "none"
        draw_text(screen, f"Spouse: {spouse} | Companion: {lover}", (panel.x + 18, panel.y + 50), self.small_font, (197, 207, 216))
        draw_fitted_text(screen, f"Heirs: {heirs}", pygame.Rect(panel.x + 18, panel.y + 74, 790, 22), self.small_font, (197, 207, 216), align="left")
        self._add_button(pygame.Rect(panel.x + 18, panel.y + 112, 116, 34), tr("action.choose_spouse"), lambda s: action_none(s.choose_spouse()), icon="family")
        self._add_button(pygame.Rect(panel.x + 142, panel.y + 112, 116, 34), tr("action.take_lover"), lambda s: action_none(s.choose_lover()), icon="family")
        self._add_button(pygame.Rect(panel.x + 266, panel.y + 112, 116, 34), tr("action.plan_heir"), lambda s: action_none(s.try_for_child()), icon="family")
        self._add_button(pygame.Rect(panel.x + 390, panel.y + 112, 116, 34), tr("action.divorce"), lambda s: action_none(s.divorce()), icon="politics")

    def _draw_war_tab(self, screen: pygame.Surface, state: GameState, panel: pygame.Rect) -> None:
        draw_text(screen, tr("tab.war.target"), (panel.x + 18, panel.y + 46), self.small_font, (197, 207, 216))
        self._draw_target_list(screen, state, pygame.Rect(panel.x + 18, panel.y + 68, 350, 92))
        target = state.selected_target
        player = state.player_country
        if not target or not player:
            return

        war = state.get_player_war_with(target.name)
        draw_text(screen, f"Selected: {target.name} | Regions: {len(target.provinces)} | Army: {target.army}", (panel.x + 390, panel.y + 48), self.small_font, (197, 207, 216))
        if not war:
            player_score = int(player.army * (1 + player.technology * 0.09) * player.law_war_multiplier())
            target_score = int(target.army * (1 + target.technology * 0.09) * target.law_war_multiplier())
            draw_text(screen, f"Estimated strength: {player.name} {player_score} vs {target.name} {target_score}", (panel.x + 390, panel.y + 75), self.small_font, (197, 207, 216))
            self._add_button(pygame.Rect(panel.x + 390, panel.y + 111, 190, 36), tr("action.declare_war"), lambda s, n=target.name: action_none(s.declare_war(s.player_country_name, n)), icon="war")  # type: ignore[arg-type]
            return

        score = int(war.get("score", 0))
        months = int(war.get("months", 0))
        casualties = dict(war.get("casualties", {}))
        fronts = list(war.get("fronts", []))
        draw_text(screen, f"Active war: month {months} | Score {score} | Status: {war.get('status')}", (panel.x + 390, panel.y + 70), self.small_font, (197, 207, 216))
        draw_text(screen, f"Casualties: you {casualties.get(player.name, 0)} | target {casualties.get(target.name, 0)} | Supply {int(player.supply_ratio()*100)}%", (panel.x + 390, panel.y + 91), self.small_font, (197, 207, 216))
        front_text = "Fronts: " + " | ".join(f"{front.get('target_region')} {front.get('progress')}%" for front in fronts[:3])
        draw_fitted_text(screen, front_text, pygame.Rect(panel.x + 390, panel.y + 111, 450, 20), self.tiny_font, (197, 207, 216), align="left")
        self._add_button(pygame.Rect(panel.x + 390, panel.y + 132, 72, 28), tr("action.attack"), lambda s, n=target.name: action_none(s.set_player_army_stance(n, "attack")), tooltip=tr("tooltip.army_attack"), icon="war")
        self._add_button(pygame.Rect(panel.x + 466, panel.y + 132, 72, 28), tr("action.defend"), lambda s, n=target.name: action_none(s.set_player_army_stance(n, "defend")), tooltip=tr("tooltip.army_defend"), icon="stability")
        self._add_button(pygame.Rect(panel.x + 542, panel.y + 132, 76, 28), tr("action.retreat"), lambda s, n=target.name: action_none(s.set_player_army_stance(n, "retreat")), tooltip=tr("tooltip.army_retreat"), icon="army")
        can_peace = state.can_offer_peace(war)
        self._add_button(pygame.Rect(panel.x + 588, panel.y + 132, 62, 28), tr("action.peace_region"), lambda s, n=target.name: action_none(s.player_peace_demand(n, "region")), enabled=can_peace)
        self._add_button(pygame.Rect(panel.x + 654, panel.y + 132, 62, 28), tr("action.peace_money"), lambda s, n=target.name: action_none(s.player_peace_demand(n, "money")), enabled=can_peace)
        self._add_button(pygame.Rect(panel.x + 720, panel.y + 132, 62, 28), tr("action.peace_vassal"), lambda s, n=target.name: action_none(s.player_peace_demand(n, "vassal")), enabled=can_peace)
        self._add_button(pygame.Rect(panel.x + 786, panel.y + 132, 62, 28), tr("action.peace_white"), lambda s, n=target.name: action_none(s.player_peace_demand(n, "white_peace")), enabled=can_peace)

    def _draw_technology_tab(self, screen: pygame.Surface, state: GameState, panel: pygame.Rect) -> None:
        player = state.player_country
        if not player:
            return
        rc = player.tech_resource_cost()
        draw_text(screen, f"Technology level: {player.technology} | Research cost: {player.tech_cost()} + O{rc['oil']} M{rc['metal']}", (panel.x + 18, panel.y + 50), self.small_font, (197, 207, 216))
        draw_text(screen, tr("tab.technology.description"), (panel.x + 18, panel.y + 75), self.small_font, (197, 207, 216))
        self._add_button(pygame.Rect(panel.x + 18, panel.y + 112, 190, 36), tr("action.research_technology"), lambda s: action_none(s.player_research_technology()), icon="technology")

    def _draw_statistics_tab(self, screen: pygame.Surface, state: GameState, panel: pygame.Rect) -> None:
        player = state.player_country
        if not player:
            return
        supply = player.supply_need()
        lines = [
            f"GDP: {player.gdp} | GDP per capita {player.gdp_per_capita()} | Tax income {player.tax_income} | Military spending {player.military_spending}",
            f"Society: unemployment {player.unemployment:.1f}% | education {player.education} | healthcare {player.healthcare}",
            f"Economy: income {player.last_month_income}, expenses {player.last_month_expenses}, balance {player.last_month_balance}, debt {player.debt}, inflation {player.inflation:.1f}%",
            f"Military: strength {player.army}, morale {player.army_morale}, experience {player.army_experience}, wear {player.equipment_wear}",
            f"Units: infantry {player.units['infantry']}, tanks {player.units['tanks']}, artillery {player.units['artillery']}, aircraft {player.units['aircraft']}",
            f"Supply need: oil {supply['oil']}, food {supply['food']}, metal {supply['metal']} | readiness {int(player.supply_ratio()*100)}%",
            f"Industry: factories {player.buildings['factory']}, farms {player.buildings['farm']}, oil fields {player.buildings['oil_field']}, mines {player.buildings['mine']}",
            f"Treaties: trade {len(player.trade_agreements)}, military {len(player.military_agreements)}, guarantees {len(player.guarantees)}, sanctioned by {len(player.sanctioned_by)}",
            f"Regions: {len(player.provinces)} | Regional economy {player.regional_economy()} | Active wars {len([w for w in state.active_wars.values() if player.name in [w.get('attacker'), w.get('defender')]])}",
        ]
        y = panel.y + 50
        for line in lines:
            draw_text(screen, line, (panel.x + 18, y), self.small_font, (197, 207, 216))
            y += 25


