import random

from core.country_data import clamp


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
    if random.random() > 0.42:
        return

    event = random.choice([
        "economic crisis",
        "election scandal",
        "military reform",
        "royal wedding",
        "betrayal",
        "spy scandal",
        "border conflict",
        "technology breakthrough",
    ])

    countries = list(game_state.countries.values())
    country = random.choice(countries)

    if event == "economic crisis":
        loss = max(40, int(country.money * 0.17))
        country.money = max(0, country.money - loss)
        country.stability = clamp(country.stability - 8, 0, 100)
        game_state.add_message(f"Event: economic crisis in {country.name}. Money -{loss}, stability down.")
        if country.name == game_state.player_country_name:
            game_state.add_notification("Economic crisis", f"{country.name} loses {loss} money and stability.")

    elif event == "election scandal":
        country.stability = clamp(country.stability - 12, 0, 100)
        country.influence = max(0, country.influence - 2)
        game_state.add_message(f"Event: election scandal damages {country.name}.")
        if country.name == game_state.player_country_name:
            game_state.add_notification("Election scandal", "Your legitimacy has been damaged.")

    elif event == "military reform":
        gain = max(15, int(country.army * 0.06))
        country.units["infantry"] += gain
        country.sync_army_from_units()
        country.stability = clamp(country.stability + 2, 0, 100)
        game_state.add_message(f"Event: military reform in {country.name}. Army +{gain}.")

    elif event == "royal wedding":
        player = game_state.player_country
        if player and player.spouse is None and random.random() < 0.45:
            player.spouse = random.choice(SPOUSE_NAMES)
            player.stability = clamp(player.stability + 6, 0, 100)
            game_state.add_message(f"Event: royal wedding. {player.spouse} joins your court.")
        else:
            country.stability = clamp(country.stability + 5, 0, 100)
            game_state.add_message(f"Event: royal wedding celebrations boost {country.name}.")

    elif event == "betrayal":
        player = game_state.player_country
        if player and player.lover and random.random() < 0.5:
            player.stability = clamp(player.stability - 9, 0, 100)
            game_state.add_message(f"Event: betrayal. Rumors around {player.lover} hurt your rule.")
        else:
            target = random.choice([c for c in countries if c.name != country.name])
            game_state.add_relation_delta(country.name, target.name, -20)
            game_state.add_message(f"Event: betrayal between {country.name} and {target.name}.")

    elif event == "spy scandal":
        a, b = random.sample(countries, 2)
        game_state.add_relation_delta(a.name, b.name, -24)
        a.stability = clamp(a.stability - 3, 0, 100)
        game_state.add_message(f"Event: spy scandal. Relations fall between {a.name} and {b.name}.")
        if game_state.player_country_name in [a.name, b.name]:
            game_state.add_notification("Spy scandal", f"Relations between {a.name} and {b.name} deteriorate.")

    elif event == "border conflict":
        a, b = random.sample(countries, 2)
        game_state.add_relation_delta(a.name, b.name, -28)
        if game_state.get_relation(a.name, b.name) < -65 and random.random() < 0.35:
            game_state.declare_war(a.name, b.name, ai_initiated=True)
        else:
            game_state.add_message(f"Event: border conflict between {a.name} and {b.name}.")
        if game_state.player_country_name in [a.name, b.name]:
            game_state.add_notification("Border conflict", f"Tension rises between {a.name} and {b.name}.")

    elif event == "technology breakthrough":
        country.technology += 1
        country.money += 50
        game_state.add_message(f"Event: technology breakthrough in {country.name}.")
        if country.name == game_state.player_country_name:
            game_state.add_notification("Technology breakthrough", "Your researchers gained a technology level.", pause=False)


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
