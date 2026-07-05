from __future__ import annotations

from core.game_state import GameState


def action_none(_: object) -> None:
    return None


def select_target_action(state: GameState, name: str) -> None:
    state.selected_target_name = name
    return None


def set_speed_action(state: GameState, speed: int) -> None:
    state.set_speed(speed)
    return None


def dismiss_notification_action(state: GameState) -> None:
    state.clear_notification()
    return None
