from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.game_state import GameState
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


def test_save_schema_version_09() -> None:
    state = GameState()
    data = state.to_dict()
    assert data["version"] == "0.9"
    assert data["version"] == SAVE_SCHEMA_VERSION


def test_migration_v06_v07_v08() -> None:
    state = GameState()
    state.choose_player_country("USA")
    for version in ["0.6", "0.7", "0.8"]:
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


def run_all() -> None:
    tests = [
        test_new_game,
        test_choose_country_and_month,
        test_declare_war_and_move_army,
        test_save_load_roundtrip,
        test_save_schema_version_09,
        test_legacy_v04_upgrade,
        test_legacy_v05_upgrade,
        test_migration_v06_v07_v08,
        test_no_static_geometry_in_new_save,
        test_new_save_is_smaller_than_legacy_geometry_save,
        test_army_sync_after_recruit_and_war_loss,
        test_country_search_text_input_does_not_duplicate_letters,
        test_localization_parity,
        test_map_render_smoke,
        test_save_load_paths_after_project_move,
        test_ui_search_and_escape_menu,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")


if __name__ == "__main__":
    run_all()
