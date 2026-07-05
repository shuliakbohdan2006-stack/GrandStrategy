# Contributing

Thanks for helping improve Grand Strategy. The project is still a prototype, so changes should be small, testable and easy to review.

## Setup

```powershell
cd D:\GrandStrategy
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run the game:

```powershell
python main.py
```

## Tests

Run smoke/regression tests before every pull request:

```powershell
python tests\smoke_tests.py
python -m py_compile main.py
```

The tests set `SDL_VIDEODRIVER=dummy` for headless Pygame checks.

## Code Style

- Prefer simple Python modules and clear functions.
- Keep gameplay systems separated under `systems/`.
- Keep shared model/state code under `core/`.
- Keep rendering and map code under `map/`.
- Keep UI code under `ui/`.
- Avoid circular imports. Internal code should import from package modules such as `core.game_state`, `systems.save_load` and `map.render`.
- Do not add large new mechanics in cleanup-only changes.
- Add or update smoke tests for behavior changes.

## Adding New Systems

1. Put gameplay logic in a focused module under `systems/`.
2. Expose behavior through a mixin or a narrow method on `GameState`.
3. Keep UI wiring in `ui/`.
4. Keep serialization compatibility in mind if new state is saved.
5. Add regression coverage in `tests/smoke_tests.py`.

## Localization

- English is the source language.
- Every language file must contain every key from `localization/en.json`.
- UI strings should use `tr()`.
- If a translation is missing, the runtime falls back to English, then to the key.
- Run smoke tests after editing localization files.

## Pull Requests

Before opening a PR:

- Confirm the game starts with `python main.py`.
- Run `python tests\smoke_tests.py`.
- Run `python -m py_compile main.py`.
- Update README or CHANGELOG when behavior, setup or project structure changes.
- Document new third-party assets in `ASSET_CREDITS.md`.

## Do Not Commit

- `backups/`
- `saves/*.json`
- `screenshots/*.png`, `.jpg`, `.jpeg`
- `__pycache__/`
- `*.pyc`
- `*.log`
- `.pytest_cache/`
- `.vscode/`
- virtual environments
