# Grand Strategy

A Python + Pygame prototype of a 2D global grand strategy game. The player chooses a real-world country, manages economy, army, diplomacy, politics, laws, family, technology and wars on a simplified Natural Earth world map.

Current game version: **v1.0.1**  
Save schema version: **v1.0.1**

## Screenshots

Local verification screenshots are stored in `screenshots/` when available. The folder is ignored by Git so the repository stays lightweight. Add curated screenshots later if you want them to appear on GitHub.

## Features

- Main menu, country selection, settings, credits and pause menu.
- Real-world country polygons from Natural Earth 110m GeoJSON.
- Playable world map with zoom, pan, country selection, labels, capitals, fronts and army markers.
- Country stats for GDP, GDP per capita, unemployment, education, healthcare, military spending, tax income, economy, army, resources, stability, laws, leader, provinces and relations.
- Economy, army, production, construction, trade, diplomacy, politics, laws, family, war, technology and statistics tabs.
- Long wars with fronts, casualties, morale, experience, equipment wear, supply pressure, army stances and peace demands.
- Diplomacy actions for alliances, sanctions, trade agreements, military pacts, guarantees and ultimatums.
- AI country profiles for major countries plus strategic behavior for economy, buildings, research, treaties, sanctions, ultimatums and wars.
- 100+ data-driven random events across economy, politics, war, science, society, disasters, epidemics, terrorism, corruption, sport, culture, migration and energy.
- Compact JSON Save/Load with sparse relations and v0.6/v0.7/v0.8/v0.9/v1.0-alpha migration to save schema v1.0.1.
- Localization scaffolding for English, Russian, German and Ukrainian.
- Smoke/regression tests for Save/Load, migrations, army sync, localization parity, map render, UI input, Alpha events, diplomacy, economy indicators, army stats and AI.

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

- Manual player choice UI for data-driven events.
- More complete localization of gameplay log/event strings.
- Stronger AI profiles for more countries and diplomatic blocs.
- Better responsive layout for non-1440x840 displays.
- Real administrative regions instead of generated province data.
- Deeper war/front logistics, occupation rules and peace negotiation UI.
- Curated screenshots and higher-quality authored assets.

## Version Status

v1.0.1 is a balance and stability release. It slows runaway GDP/money/tech growth, adds AI crisis recovery, makes saves compact with sparse relations, improves event choice data and adds first-pass diplomacy consequences while preserving old save migration.

## License

MIT. See `LICENSE`.
