import random

from ai.profiles import profile_for
from core.country_data import LAW_OPTIONS, RESOURCES
from core.utils import stable_hash


def run_monthly_ai(game_state) -> None:
    player_name = game_state.player_country_name
    names = list(game_state.countries.keys())

    for country in game_state.countries.values():
        if country.name == player_name:
            continue

        profile = profile_for(country.name)
        debt_pressure = country.debt / max(1, country.monthly_income() * 24)
        resource_score = min(country.resources.get(resource, 0) for resource in RESOURCES)
        threat = perceived_threat(game_state, country.name)

        if debt_pressure > profile.debt_caution or country.inflation > 16:
            country.change_law("taxes", "High")
            country.change_law("trade_policy", "Free Trade")
        elif country.stability < 45:
            country.change_law("taxes", "Low")
            country.change_law("censorship", "Regulated")

        acted = develop_country(country, profile, resource_score, threat)

        if country.stability > 55 and profile.technology > 0.55 and country.debt < country.monthly_income() * 18:
            if country.research_technology():
                acted = True

        if profile.diplomacy > 0.55:
            pursue_alliances(game_state, country, names, player_name)
        else:
            manage_player_relation(game_state, country, player_name, profile)

        if should_consider_war(game_state, country, profile, threat):
            target = choose_war_target(game_state, country, names)
            if target:
                game_state.declare_war(country.name, target.name, ai_initiated=True)

        if acted and country.is_core_country and game_state.months_elapsed % 4 == stable_hash(country.name) % 4:
            game_state.add_message(f"AI: {country.name} follows its national strategy.")


def develop_country(country, profile, resource_score: int, threat: float) -> bool:
    weakest = min(RESOURCES, key=lambda resource: country.resources.get(resource, 0) + country.resource_output().get(resource, 0) * 2)
    if resource_score < 35:
        if weakest == "food" and country.build_structure("farm"):
            return True
        if weakest == "oil" and country.build_structure("oil_field"):
            return True
        if weakest == "metal" and country.build_structure("mine"):
            return True

    if profile.economy >= profile.military and country.debt < country.monthly_income() * 18:
        if country.buildings.get("factory", 0) < max(1, country.regional_economy() // 15) and country.build_structure("factory"):
            return True
        if country.invest_in_economy():
            return True

    if profile.military + threat > 0.78 and country.supply_ratio() > 0.55:
        if country.resources.get("metal", 0) > 30 and country.resources.get("oil", 0) > 20:
            choice = "tanks" if profile.military > 0.70 and country.buildings.get("factory", 0) else "infantry"
            if country.produce_weapon_batch(choice):
                return True
        if country.money > country.recruit_cost() and country.recruit_soldiers():
            return True

    return False


def perceived_threat(game_state, country_name: str) -> float:
    country = game_state.countries[country_name]
    hostile = [
        other for other in game_state.countries.values()
        if other.name != country_name and game_state.get_relation(country_name, other.name) < -55
    ]
    if not hostile:
        return 0.0
    strongest = max(hostile, key=lambda other: other.army)
    return min(1.0, strongest.army / max(1, country.army * 1.6))


def pursue_alliances(game_state, country, names, player_name) -> None:
    candidates = [
        game_state.countries[name] for name in names
        if name != country.name and name not in country.allies and game_state.get_relation(country.name, name) > 60
    ]
    candidates.sort(key=lambda other: other.influence + other.army // 30, reverse=True)
    for ally in candidates[:1]:
        if country.debt < country.monthly_income() * 20 and ally.debt < ally.monthly_income() * 24:
            game_state.make_alliance(country.name, ally.name, announce=False)
            if country.is_core_country or ally.name == player_name:
                game_state.add_message(f"AI: {country.name} signs a strategic alliance with {ally.name}.")


def manage_player_relation(game_state, country, player_name, profile) -> None:
    if not player_name or player_name == country.name:
        return
    player = game_state.countries[player_name]
    relation = game_state.get_relation(country.name, player_name)
    desired = 20 if profile.aggression < 0.2 else -10
    if player.army > country.army * 1.5:
        desired += 18
    if country.debt > country.monthly_income() * 18:
        desired += 10
    if relation < desired - 8:
        game_state.add_relation_delta(country.name, player_name, 2)
    elif relation > desired + 12 and profile.aggression > 0.35:
        game_state.add_relation_delta(country.name, player_name, -2)


def should_consider_war(game_state, country, profile, threat: float) -> bool:
    if country.debt > country.monthly_income() * (16 + profile.debt_caution * 12):
        return False
    if country.stability < 48 or country.supply_ratio() < 0.58:
        return False
    if any(country.name in [war.get("attacker"), war.get("defender")] for war in game_state.active_wars.values()):
        return False
    cadence = 8 if profile.aggression < 0.25 else 5 if profile.aggression < 0.5 else 3
    if game_state.months_elapsed % cadence != stable_hash(country.name) % cadence:
        return False
    return profile.aggression + profile.military * 0.25 + threat * 0.18 > 0.47


def choose_war_target(game_state, country, names):
    candidates = []
    for name in names:
        if name == country.name or name in country.allies:
            continue
        target = game_state.countries[name]
        if game_state.get_war_between(country.name, target.name):
            continue
        relation = game_state.get_relation(country.name, target.name)
        if relation > -55:
            continue
        power_ratio = country.army * country.supply_ratio() / max(1, target.army * target.supply_ratio())
        if power_ratio < 1.18:
            continue
        if target.debt > target.monthly_income() * 18:
            power_ratio += 0.25
        candidates.append((relation, -target.influence, -power_ratio, target))
    if not candidates:
        return None
    candidates.sort()
    return candidates[0][3]
