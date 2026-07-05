# Grand Strategy

A Python + Pygame prototype of a 2D global grand strategy game. The player chooses a real-world country, manages economy, army, diplomacy, politics, laws, family, technology and wars on a simplified Natural Earth world map.

Current game version: **v0.9.1**  
Save schema version: **v0.9**

## Screenshots

Local verification screenshots are stored in `screenshots/` when available. The folder is ignored by Git so the repository stays lightweight. Add curated screenshots later if you want them to appear on GitHub.

## Features

- Main menu, country selection, settings, credits and pause menu.
- Real-world country polygons from Natural Earth 110m GeoJSON.
- Playable world map with zoom, pan, country selection, labels, capitals, fronts and army markers.
- Country stats for economy, army, resources, stability, laws, leader, provinces and relations.
- Economy, army, production, construction, trade, diplomacy, politics, laws, family, war, technology and statistics tabs.
- Long wars with fronts, casualties, army stances and peace demands.
- AI country profiles for major countries plus default behavior for the rest of the world.
- JSON Save/Load with v0.6/v0.7/v0.8 migration to save schema v0.9.
- Localization scaffolding for English, Russian, German and Ukrainian.
- Smoke/regression tests for Save/Load, migrations, army sync, localization parity, map render and UI input.

## Requirements

- Python 3.11+
- Pygame

Install dependencies:

```powershell
cd D:\GrandStrategy
pip install -r requirements.txt
```

## Run

```powershell
cd D:\GrandStrategy
python main.py
```

## Controls

- Left mouse: press UI buttons, select countries and targets.
- Mouse wheel: zoom the world map during gameplay; scroll country list during country selection.
- Drag map: pan the world map during gameplay.
- Space: pause/resume time while in game.
- F5: save to `saves/save_game.json`.
- F9: load from `saves/save_game.json`.
- Esc: open/close the in-game pause menu.

## Project Structure

- `main.py` - Pygame entry point.
- `core/` - game state, country model, country data, serialization and version constants.
- `systems/` - economy, diplomacy, family, governance, resources, construction, technology, war, armies and Save/Load.
- `map/` - Natural Earth loading, camera and map rendering.
- `ui/` - menus, country selection, game HUD, tabs, settings and UI helpers.
- `ai/` - monthly AI logic and AI profiles.
- `assets/` - icons, flags, images, sounds and optional fonts.
- `data/` - Natural Earth GeoJSON.
- `localization/` - language dictionaries.
- `tests/` - smoke/regression tests.
- `saves/`, `screenshots/`, `backups/` - local runtime artifacts ignored by Git.
- `.github/` - issue templates, pull request template and CI workflow.

## Add a Language

1. Copy `localization/en.json` to `localization/<code>.json`.
2. Translate values, keeping every key from English.
3. Add the language option in `ui/settings_view.py` if it should appear in Settings.
4. Run `python tests\smoke_tests.py` to verify localization parity.

## Add Assets

- Flags: add PNG files to `assets/flags/<iso_a2>.png`.
- Icons: add transparent PNG files to `assets/icons/<name>.png` and use `self.assets.get_icon("<name>")`.
- Sounds: add WAV files to `assets/sounds/<name>.wav` and call `self.assets.play("<name>")`.
- Images: add PNG/JPG files to `assets/images/`.
- Fonts: add `NotoSans-Regular.ttf` and `NotoSans-Bold.ttf` or `Inter-Regular.ttf` and `Inter-Bold.ttf` to `assets/fonts/`.

Document third-party asset sources in `ASSET_CREDITS.md`.

## Tests

```powershell
cd D:\GrandStrategy
python tests\smoke_tests.py
python -m py_compile main.py
```

The smoke suite runs headless with `SDL_VIDEODRIVER=dummy`.

## Roadmap

- More complete localization of gameplay log/event strings.
- Stronger AI profiles for more countries.
- Better responsive layout for non-1440x840 displays.
- Real administrative regions instead of generated province data.
- Deeper war/front logistics and occupation rules.
- Curated screenshots and higher-quality authored assets.

## Version Status

v0.9.1 is a GitHub preparation release. It does not add new gameplay mechanics. It adds repository hygiene, documentation, templates, version constants and CI configuration while preserving v0.9 Save/Load behavior.

## License

MIT. See `LICENSE`.
