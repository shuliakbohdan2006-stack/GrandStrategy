import random

from core.country_data import clamp
from localization import tr
from systems.event_catalog import apply_effects, available_events, choose_event_option, summarize_effects


SPOUSE_NAMES = [
    "Anna of Northmarch",
    "Elena Voss",
    "Maria Calder",
    "Sofia Vale",
    "Isabelle Arden",
    "Nadia Orlov",
]

LOVER_NAMES = [
    "Clara West",
    "Vera Sokol",
    "Mina Hart",
    "Lina Duarte",
    "Yuki Mori",
    "Aylin Demir",
]

CHILD_NAMES = [
    "Alex",
    "Mira",
    "Leon",
    "Diana",
    "Victor",
    "Eva",
    "Nikolai",
    "Iris",
]


def maybe_add_child(country) -> str:
    name = random.choice(CHILD_NAMES)
    child = {
        "name": name,
        "age": 0,
        "claim": random.choice(["strong", "medium", "weak"]),
    }
    country.children.append(child)
    return name


def apply_random_event(game_state) -> None:
    if random.random() > 0.48:
        return

    countries = list(game_state.countries.values())
    player = game_state.player_country
    if player and random.random() < 0.35:
        country = player
    else:
        country = random.choice(countries)

    available = available_events(country, game_state)
    if not available:
        return

    event = random.choice(available)
    option = choose_event_option(event, country)
    apply_effects(country, option.effects)
    effect_text = summarize_effects(option.effects)
    game_state.add_message(
        tr("log.event").format(
            category=event.category,
            title=event.title,
            country=country.name,
            option=option.label,
            effects=effect_text,
        )
    )

    important_categories = {"War", "Epidemic", "Terrorism", "Natural Disaster", "Politics", "Energy"}
    if country.name == game_state.player_country_name and event.category in important_categories:
        game_state.add_notification(event.title, f"{event.description} Response: {option.label}. Effects: {effect_text}.", pause=event.category in {"War", "Politics", "Natural Disaster"})

    if event.category in {"Terrorism", "Politics"} and country.stability < 35 and random.random() < 0.18:
        country.internal_problems["government_crisis"] = clamp(country.internal_problems["government_crisis"] + 5, 0, 100)

    if event.category == "War" and country.wars and random.random() < 0.15:
        enemy_name = random.choice(list(country.wars))
        if enemy_name in game_state.countries:
            game_state.add_relation_delta(country.name, enemy_name, -6)


def process_family_month(game_state) -> None:
    player = game_state.player_country
    if not player:
        return

    if game_state.date.month == 1:
        for child in player.children:
            child["age"] = int(child.get("age", 0)) + 1

    has_partner = player.spouse is not None or player.lover is not None
    if has_partner and random.random() < 0.035:
        child_name = maybe_add_child(player)
        game_state.add_message(f"Family: {child_name} is born and added to the succession line.")

    if player.lover and random.random() < 0.025:
        player.stability = clamp(player.stability - 6, 0, 100)
        game_state.add_message("Family: court gossip about your lover causes a minor scandal.")

    if player.spouse and random.random() < 0.012:
        player.stability = clamp(player.stability - 8, 0, 100)
        game_state.add_message("Family: a bitter argument raises rumors of divorce.")
