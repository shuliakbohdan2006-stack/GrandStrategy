from __future__ import annotations

from datetime import date
from typing import Dict

from core.country_model import Country
from core.version import SAVE_SCHEMA_VERSION
from systems.armies import Army, create_initial_armies
from map.camera import MapCamera
from systems.settings import DEFAULT_SETTINGS


SUPPORTED_LEGACY_SAVE_VERSIONS = {"0.4", "0.5", "0.6", "0.7", "0.8", "0.9", "1.0-alpha", SAVE_SCHEMA_VERSION}


def migrate_save_data(data: Dict[str, object]) -> Dict[str, object]:
    """Normalize old save dictionaries to the current v1.0.1 schema."""
    migrated = dict(data)
    old_version = str(migrated.get("version", "0.4"))
    migrated["_loaded_from_version"] = old_version
    migrated["version"] = SAVE_SCHEMA_VERSION
    migrated.setdefault("countries", {})
    migrated.setdefault("player_country_name", None)
    migrated.setdefault("selected_target_name", None)
    migrated.setdefault("current_tab", "Overview")
    migrated.setdefault("date", "2026-01-01")
    migrated.setdefault("months_elapsed", 0)
    migrated.setdefault("speed", 0)
    migrated.setdefault("active_wars", {})
    migrated.setdefault("armies", [])
    migrated.setdefault("selected_army_id", None)
    migrated.setdefault("camera", {})
    migrated.setdefault("map_version", "natural-earth-110m")
    migrated.setdefault("victory_goal", None)
    migrated.setdefault("game_over", False)
    migrated.setdefault("game_over_reason", "")
    migrated.setdefault("notifications", [])
    migrated.setdefault("settings", {})
    migrated.setdefault("messages", [])
    if old_version not in SUPPORTED_LEGACY_SAVE_VERSIONS:
        messages = list(migrated.get("messages", []))  # type: ignore[arg-type]
        messages.append(f"Save upgrade warning: unknown save version {old_version}, loaded with defaults.")
        migrated["messages"] = messages
    return migrated


class SaveStateMixin:
    def to_dict(self) -> Dict[str, object]:
        return {
            "version": SAVE_SCHEMA_VERSION,
            "countries": {name: country.to_dict() for name, country in self.countries.items()},
            "player_country_name": self.player_country_name,
            "selected_target_name": self.selected_target_name,
            "current_tab": self.current_tab,
            "date": self.date.isoformat(),
            "months_elapsed": self.months_elapsed,
            "speed": self.speed,
            "active_wars": self.active_wars,
            "armies": [army.to_dict() for army in self.armies],
            "selected_army_id": self.selected_army_id,
            "camera": self.camera.to_dict(),
            "map_version": self.map_version,
            "victory_goal": self.victory_goal,
            "game_over": self.game_over,
            "game_over_reason": self.game_over_reason,
            "notifications": self.notifications,
            "settings": self.settings,
            "messages": self.messages,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "GameState":
        data = migrate_save_data(data)
        state = cls()
        state.countries = {
            name: Country.from_dict(country_data)
            for name, country_data in dict(data["countries"]).items()
        }
        try:
            from map.world import ensure_world_metadata

            state.countries = ensure_world_metadata(state.countries)
        except Exception as exc:
            state.messages.append(f"Map upgrade warning: {exc}")
        state.player_country_name = data.get("player_country_name")  # type: ignore[assignment]
        state.selected_target_name = data.get("selected_target_name")  # type: ignore[assignment]
        state.current_tab = str(data.get("current_tab", "Overview"))
        state.date = date.fromisoformat(str(data.get("date", "2026-01-01")))
        state.months_elapsed = int(data.get("months_elapsed", 0))
        state.speed = int(data.get("speed", 0))
        state.active_wars = dict(data.get("active_wars", {}))  # type: ignore[arg-type]
        state.armies = [Army.from_dict(item) for item in data.get("armies", [])] if data.get("armies") else create_initial_armies(state.countries)  # type: ignore[arg-type]
        state.selected_army_id = data.get("selected_army_id")  # type: ignore[assignment]
        state.camera = MapCamera.from_dict(data.get("camera", {}))
        state.map_version = str(data.get("map_version", "natural-earth-110m"))
        state.victory_goal = data.get("victory_goal")  # type: ignore[assignment]
        state.game_over = bool(data.get("game_over", False))
        state.game_over_reason = str(data.get("game_over_reason", ""))
        state.notifications = list(data.get("notifications", []))  # type: ignore[arg-type]
        settings = dict(data.get("settings", {}))  # type: ignore[arg-type]
        state.settings = {
            "sound": bool(settings.get("sound", True)),
            "autosave": bool(settings.get("autosave", False)),
            "difficulty": str(settings.get("difficulty", "Normal")),
        }
        state.settings.update({key: settings.get(key, value) for key, value in DEFAULT_SETTINGS.items()})
        state.messages = list(data.get("messages", []))  # type: ignore[arg-type]
        state.time_accumulator = 0.0
        state.refresh_player_relations()
        state.sync_map_armies()
        return state

