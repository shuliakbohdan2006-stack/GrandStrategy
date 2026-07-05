import sys

try:
    import pygame
except ImportError:
    print("Pygame is required. Install it with: pip install pygame")
    raise SystemExit(1)

from core.game_state import GameState
from core.version import GAME_VERSION
from localization import tr
from systems.settings import apply_settings_to_state
from ui import SCREEN_HEIGHT, SCREEN_WIDTH, UI


def main() -> None:
    pygame.init()
    pygame.display.set_caption(f"Grand Strategy v{GAME_VERSION}")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    state = GameState()
    ui = UI()
    apply_settings_to_state(state, ui.settings)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                loaded_state = ui.handle_key_down(event, state)
                if loaded_state is not None:
                    state = loaded_state
                elif event.key == pygame.K_SPACE and ui.mode == "game":
                    state.set_speed(0 if state.speed else 1)
                elif event.key == pygame.K_F5:
                    from systems.save_load import save_game

                    save_game(state)
                    state.add_message(tr("status.saved"))
                elif event.key == pygame.K_F9:
                    from systems.save_load import load_game

                    try:
                        state = load_game()
                        apply_settings_to_state(state, ui.settings)
                        ui._set_mode("game")
                        state.add_message(tr("status.loaded"))
                    except FileNotFoundError:
                        state.add_message(f"{tr('status.load_failed')}: saves/save_game.json not found.")
            elif event.type == pygame.MOUSEBUTTONDOWN:
                loaded_state = ui.handle_mouse_down(event.pos, event.button, state)
                if loaded_state is not None:
                    state = loaded_state
            elif event.type == pygame.MOUSEMOTION:
                ui.handle_mouse_motion(event.pos, state)
            elif event.type == pygame.MOUSEBUTTONUP:
                loaded_state = ui.handle_mouse_up(event.pos, event.button, state)
                if loaded_state is not None:
                    state = loaded_state
            elif event.type == pygame.MOUSEWHEEL:
                ui.handle_mouse_wheel(pygame.mouse.get_pos(), event.y, state)
            elif event.type == pygame.TEXTINPUT:
                ui.handle_text_input(event.text, state)

        if ui.should_tick_game():
            state.tick(dt)
        ui.current_fps = clock.get_fps()
        if ui.consume_display_mode_changed():
            flags = pygame.FULLSCREEN if ui.settings.get("fullscreen") else 0
            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
        ui.draw(screen, state)
        pygame.display.flip()
        if ui.exit_requested:
            running = False

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
