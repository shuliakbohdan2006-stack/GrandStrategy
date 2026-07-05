import json
from pathlib import Path

from core.game_state import GameState


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAVE_DIR = PROJECT_ROOT / "saves"
SAVE_PATH = SAVE_DIR / "save_game.json"
LEGACY_SAVE_PATH = PROJECT_ROOT / "save_game.json"


def save_game(game_state: GameState, path: Path = SAVE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(game_state.to_dict(), file, indent=2)


def load_game(path: Path = SAVE_PATH) -> GameState:
    if path == SAVE_PATH and not path.exists() and LEGACY_SAVE_PATH.exists():
        path = LEGACY_SAVE_PATH
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return GameState.from_dict(data)
