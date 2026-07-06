from __future__ import annotations

import json
import os
import random
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.game_state import GameState
from systems.event_catalog import EVENT_CATALOG, apply_effects, available_events
from systems.save_load import SAVE_PATH, load_game, save_game
from systems.save_state import SAVE_SCHEMA_VERSION


def legacy_save_with_geometry(state: GameState, version: str) -> dict:
    data = json.loads(json.dumps(state.to_dict()))
    data["version"] = version
    for name, country_data in data["countries"].items():
        country = state.countries[name]
        country_data["shape"] = [list(point) for point in country.shape]
        country_data["geo_polygons"] = [
            [[float(point[0]), float(point[1])] for point in ring]
            for ring in country.geo_polygons
        ]
        country_data["label_lon"] = country.label_lon
        country_data["label_lat"] = country.label_lat
        country_data["capital_lon"] = country.capital_lon
        country_data["capital_lat"] = country.capital_lat
    return data


def army_marker_total(state: GameState, country_name: str) -> int:
    return sum(army.size for army in state.armies if army.country_name == country_name)


def test_new_game() -> None:
    state = GameState()
    assert len(state.countries) >= 20
    assert len(state.armies) > 0
    assert "USA" in state.countries


def test_choose_country_and_month() -> None:
    state = GameState()
    state.choose_player_country("USA")
    state.process_month()
    assert state.player_country_name == "USA"
    assert state.months_elapsed == 1
    assert state.player_country is not None
    assert state.player_country.last_month_income > 0


def test_declare_war_and_move_army() -> None:
    state = GameState()
    state.choose_player_country("USA")
    army = next(army for army in state.armies if army.country_name == "USA")
    before = (army.lon, army.lat)
    state.declare_war("USA", "Mexico")
    assert state.get_war_between("USA", "Mexico") is not None
    state.set_player_army_stance("Mexico", "attack")
    for _ in range(12):
        state.tick(0.25)
    after = (army.lon, army.lat)
    assert before != after


def test_save_load_roundtrip() -> None:
    state = GameState()
    state.choose_player_country("USA")
    state.declare_war("USA", "Mexico")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "save_game.json"
        save_game(state, path)
        loaded = load_game(path)
    assert loaded.player_country_name == "USA"
    assert loaded.get_war_between("USA", "Mexico") is not None
    assert len(loaded.armies) == len(state.armies)
    assert loaded.to_dict()["version"] == SAVE_SCHEMA_VERSION


def test_legacy_v04_upgrade() -> None:
    state = GameState()
    state.choose_player_country("USA")
    data = state.to_dict()
    data["version"] = "0.4"
    for key in ["armies", "camera", "map_version", "selected_army_id"]:
        data.pop(key, None)
    for country in data["countries"].values():
        for key in [
            "geo_polygons",
            "iso_a3",
            "continent",
            "label_lon",
            "label_lat",
            "capital_lon",
            "capital_lat",
            "flag_colors",
            "is_core_country",
        ]:
            country.pop(key, None)
    upgraded = GameState.from_dict(data)
    assert len(upgraded.countries) >= 20
    assert upgraded.countries["USA"].geo_polygons
    assert len(upgraded.armies) > 0


def test_legacy_v05_upgrade() -> None:
    state = GameState()
    state.choose_player_country("USA")
    data = json.loads(json.dumps(state.to_dict()))
    loaded = GameState.from_dict(data)
    assert loaded.to_dict()["version"] == SAVE_SCHEMA_VERSION
    assert loaded.camera is not None
    assert len(loaded.armies) > 0


def test_save_schema_version_current() -> None:
    state = GameState()
    data = state.to_dict()
    assert data["version"] == "1.0.1"
    assert data["version"] == SAVE_SCHEMA_VERSION


def test_migration_v06_v07_v08_v09() -> None:
    state = GameState()
    state.choose_player_country("USA")
    for version in ["0.6", "0.7", "0.8", "0.9", "1.0-alpha"]:
        loaded = GameState.from_dict(legacy_save_with_geometry(state, version))
        assert loaded.to_dict()["version"] == SAVE_SCHEMA_VERSION
        assert loaded.countries["USA"].geo_polygons
        assert loaded.armies


def test_no_static_geometry_in_new_save() -> None:
    state = GameState()
    data = state.to_dict()
    for country_data in data["countries"].values():
        assert "geo_polygons" not in country_data
        assert "shape" not in country_data
        assert "label_lon" not in country_data
        assert "capital_lon" not in country_data


def test_new_save_is_smaller_than_legacy_geometry_save() -> None:
    state = GameState()
    state.choose_player_country("USA")
    new_size = len(json.dumps(state.to_dict()))
    legacy_size = len(json.dumps(legacy_save_with_geometry(state, "0.8")))
    assert new_size < legacy_size
    assert new_size < legacy_size * 0.80


def test_army_sync_after_recruit_and_war_loss() -> None:
    state = GameState()
    state.choose_player_country("USA")
    player = state.player_country
    assert player is not None
    state.sync_map_armies()
    assert army_marker_total(state, "USA") == player.army
    state.player_recruit_soldiers()
    assert army_marker_total(state, "USA") == player.army
    state.declare_war("USA", "Mexico")
    state.process_active_wars()
    assert army_marker_total(state, "USA") == state.countries["USA"].army


def test_country_search_text_input_does_not_duplicate_letters() -> None:
    import pygame

    from ui import UI

    pygame.init()
    state = GameState()
    ui = UI()
    ui._set_mode("country_select")
    ui.search_active = True
    event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_j, unicode="j")
    ui.handle_key_down(event, state)
    ui.handle_text_input("j", state)
    assert ui.country_search == "j"


def test_localization_parity() -> None:
    base = ROOT_DIR / "localization"
    english = json.loads((base / "en.json").read_text(encoding="utf-8-sig"))
    english_keys = set(english)
    for code in ["ru", "de", "uk"]:
        data = json.loads((base / f"{code}.json").read_text(encoding="utf-8-sig"))
        assert english_keys <= set(data), code


def test_map_render_smoke() -> None:
    import pygame

    from assets import AssetManager
    from map.render import draw_world_map
    from ui.layout import MAP_RECT, SCREEN_HEIGHT, SCREEN_WIDTH

    pygame.init()
    state = GameState()
    state.choose_player_country("USA")
    screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    assets = AssetManager()
    fonts = {"small": assets.get_font(15), "tiny": assets.get_font(13)}
    draw_world_map(screen, state, MAP_RECT, fonts)
    assert screen.get_at((MAP_RECT.centerx, MAP_RECT.centery)) != (0, 0, 0, 255)


def test_country_hit_test_matches_visible_map_after_zoom_and_drag() -> None:
    from map.render import country_at_screen_pos
    from ui.layout import MAP_RECT

    def hit_name(state: GameState, lon: float, lat: float) -> str | None:
        pos = state.camera.lonlat_to_screen(lon, lat, MAP_RECT)
        assert MAP_RECT.collidepoint(pos), (lon, lat, pos)
        country = country_at_screen_pos(state, pos, MAP_RECT)
        return country.name if country else None

    state = GameState()
    state.choose_player_country("Ukraine")
    state.camera.update(1.0)
    assert hit_name(state, 30.5234, 50.4501) == "Ukraine"

    state.camera.focus_lonlat(13.4050, 52.5200, zoom=2.2)
    state.camera.update(1.0)
    assert hit_name(state, 13.4050, 52.5200) == "Germany"

    state.camera.focus_lonlat(30.5234, 50.4501, zoom=2.4)
    state.camera.update(1.0)
    assert hit_name(state, 34.0, 43.0) is None

    ukraine_pos = state.camera.lonlat_to_screen(30.5234, 50.4501, MAP_RECT)
    state.camera.zoom_at(1, ukraine_pos, MAP_RECT)
    state.camera.update(1.0)
    state.camera.pan_pixels(70, -35)
    assert hit_name(state, 30.5234, 50.4501) == "Ukraine"


def test_save_load_paths_after_project_move() -> None:
    assert ROOT_DIR.name == "GrandStrategy"
    assert SAVE_PATH.parent == ROOT_DIR / "saves"
    state = GameState()
    state.choose_player_country("USA")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "save_game.json"
        save_game(state, path)
        loaded = load_game(path)
    assert loaded.player_country_name == "USA"


def test_ui_search_and_escape_menu() -> None:
    import pygame

    from assets import AssetManager
    from ui import UI

    pygame.init()
    state = GameState()
    ui = UI()
    ui._set_mode("country_select")
    ui.search_active = True
    ui.handle_text_input("jap", state)
    assert ui.country_search == "jap"
    ui._set_mode("game")
    event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, unicode="")
    ui.handle_key_down(event, state)
    assert ui.mode == "pause"
    assets = AssetManager()
    assert assets.get_icon("money", (20, 20)).get_size() == (20, 20)
    assert assets.get_flag(state.countries["USA"], (32, 20)).get_size() == (32, 20)
    assets.play("button", enabled=False)


def test_alpha_event_catalog_and_effects() -> None:
    state = GameState()
    state.choose_player_country("USA")
    player = state.player_country
    assert player is not None
    assert len(EVENT_CATALOG) >= 100
    assert all(event.choices and event.description for event in EVENT_CATALOG)
    assert available_events(player, state)
    before_gdp = player.gdp
    apply_effects(player, {"gdp": 25, "stability": 1, "education": 1, "oil": 3})
    assert player.gdp == before_gdp + 25
    assert player.education >= 1


def test_alpha_diplomacy_actions() -> None:
    state = GameState()
    state.choose_player_country("USA")
    player = state.player_country
    assert player is not None
    player.money = 2000
    state.set_relation("USA", "Germany", 70)
    state.player_trade_agreement("Germany")
    state.player_military_pact("Germany")
    state.player_guarantee_independence("Germany")
    assert "Germany" in player.trade_agreements
    assert "Germany" in player.military_agreements
    assert "Germany" in player.guarantees
    state.set_relation("USA", "Russia", -70)
    state.player_impose_sanctions("Russia")
    state.player_send_ultimatum("Russia")
    assert "Russia" in player.sanctions_against
    assert "USA" in state.countries["Russia"].sanctioned_by
    assert "Russia" in player.ultimatums_sent


def test_alpha_economy_indicators_interact() -> None:
    state = GameState()
    state.choose_player_country("USA")
    player = state.player_country
    assert player is not None
    before_gdp = player.gdp
    before_unemployment = player.unemployment
    state.process_month()
    assert player.tax_income > 0
    assert player.military_spending > 0
    assert player.gdp > 0
    assert player.gdp != before_gdp or player.unemployment != before_unemployment
    assert player.gdp_per_capita() > 0


def test_alpha_army_morale_experience_and_wear() -> None:
    state = GameState()
    state.choose_player_country("USA")
    player = state.player_country
    assert player is not None
    before_experience = player.army_experience
    before_wear = player.equipment_wear
    state.declare_war("USA", "Mexico")
    state.process_active_wars()
    assert player.army_experience >= before_experience
    assert player.equipment_wear >= before_wear
    assert 0 <= player.army_morale <= 100


def test_alpha_v09_save_migration_defaults() -> None:
    state = GameState()
    state.choose_player_country("USA")
    data = json.loads(json.dumps(state.to_dict()))
    data["version"] = "0.9"
    alpha_fields = [
        "gdp",
        "unemployment",
        "education",
        "healthcare",
        "military_spending",
        "tax_income",
        "army_experience",
        "army_morale",
        "equipment_wear",
        "trade_agreements",
        "military_agreements",
        "sanctions_against",
        "sanctioned_by",
        "guarantees",
        "guaranteed_by",
        "ultimatums_sent",
    ]
    for country_data in data["countries"].values():
        for field in alpha_fields:
            country_data.pop(field, None)
    loaded = GameState.from_dict(data)
    assert loaded.to_dict()["version"] == SAVE_SCHEMA_VERSION
    assert loaded.countries["USA"].gdp > 0
    assert loaded.countries["USA"].education > 0
    assert isinstance(loaded.countries["USA"].trade_agreements, set)


def test_alpha_ai_strategy_smoke() -> None:
    from ai import run_monthly_ai

    state = GameState()
    state.choose_player_country("USA")
    for month in range(12):
        state.months_elapsed = month
        run_monthly_ai(state)
    treaty_count = sum(len(country.trade_agreements) + len(country.military_agreements) for country in state.countries.values())
    assert treaty_count >= 0
    assert all(country.gdp > 0 for country in state.countries.values())


def test_v101_balance_24_120_months_no_runaway() -> None:
    random.seed(11)
    state = GameState()
    state.choose_player_country("USA")
    start_gdp = sum(country.gdp for country in state.countries.values())
    start_tech = sum(country.technology for country in state.countries.values())
    for _ in range(24):
        state.process_month()
    gdp_24 = sum(country.gdp for country in state.countries.values())
    tech_24 = sum(country.technology for country in state.countries.values())
    assert gdp_24 < start_gdp * 1.7
    assert tech_24 <= start_tech + 20
    for _ in range(96):
        state.process_month()
    gdp_120 = sum(country.gdp for country in state.countries.values())
    max_money = max(country.money for country in state.countries.values())
    max_tech = max(country.technology for country in state.countries.values())
    assert gdp_120 < start_gdp * 4.2
    assert max_money < 80000
    assert max_tech <= 22


def test_v101_ai_stability_collapse_triggers_recovery() -> None:
    random.seed(4)
    state = GameState()
    country = state.countries["Canada"]
    country.stability = 0
    country.internal_problems["government_crisis"] = 95
    state.process_ai_stability_crisis("Canada")
    assert country.stability > 0
    assert country.internal_problems["government_crisis"] <= 100


def test_v101_sparse_relations_save_is_smaller() -> None:
    state = GameState()
    state.choose_player_country("USA")
    sparse = state.to_dict()
    dense = json.loads(json.dumps(sparse))
    for name, country_data in dense["countries"].items():
        country_data["relations"] = state.countries[name].relations
    sparse_size = len(json.dumps(sparse, separators=(",", ":")))
    dense_size = len(json.dumps(dense, separators=(",", ":")))
    assert sparse_size < dense_size * 0.65
    assert all(len(country_data.get("relations", {})) < len(state.countries) for country_data in sparse["countries"].values())


def test_v101_event_choices_are_category_specific() -> None:
    choice_sets = {tuple(option.label for option in event.choices) for event in EVENT_CATALOG}
    description_sets = {tuple(option.description for option in event.choices) for event in EVENT_CATALOG}
    assert len(choice_sets) >= 10
    assert len(description_sets) >= 10
    assert ("Stabilize", "Exploit") not in choice_sets


def test_v101_diplomacy_guarantee_consequence() -> None:
    state = GameState()
    state.choose_player_country("USA")
    state.set_relation("USA", "Germany", 70)
    assert state.guarantee_independence("USA", "Germany", announce=False)
    before = state.get_relation("USA", "Russia")
    state.declare_war("Russia", "Germany", ai_initiated=True)
    assert state.get_relation("USA", "Russia") < before
    assert "Russia" in state.countries["USA"].sanctions_against


def test_v101_ultimatum_records_outcome() -> None:
    random.seed(6)
    state = GameState()
    state.choose_player_country("USA")
    state.countries["Mexico"].army = 10
    state.countries["Mexico"].sync_army_from_units()
    state.send_ultimatum("USA", "Mexico", announce=False)
    assert state.countries["USA"].ultimatum_outcomes.get("Mexico") in {"accepted_payment", "rejected"}


def run_all() -> None:
    tests = [
        test_new_game,
        test_choose_country_and_month,
        test_declare_war_and_move_army,
        test_save_load_roundtrip,
        test_save_schema_version_current,
        test_legacy_v04_upgrade,
        test_legacy_v05_upgrade,
        test_migration_v06_v07_v08_v09,
        test_no_static_geometry_in_new_save,
        test_new_save_is_smaller_than_legacy_geometry_save,
        test_army_sync_after_recruit_and_war_loss,
        test_country_search_text_input_does_not_duplicate_letters,
        test_localization_parity,
        test_map_render_smoke,
        test_country_hit_test_matches_visible_map_after_zoom_and_drag,
        test_save_load_paths_after_project_move,
        test_ui_search_and_escape_menu,
        test_alpha_event_catalog_and_effects,
        test_alpha_diplomacy_actions,
        test_alpha_economy_indicators_interact,
        test_alpha_army_morale_experience_and_wear,
        test_alpha_v09_save_migration_defaults,
        test_alpha_ai_strategy_smoke,
        test_v101_balance_24_120_months_no_runaway,
        test_v101_ai_stability_collapse_triggers_recovery,
        test_v101_sparse_relations_save_is_smaller,
        test_v101_event_choices_are_category_specific,
        test_v101_diplomacy_guarantee_consequence,
        test_v101_ultimatum_records_outcome,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")


if __name__ == "__main__":
    run_all()
