# Changelog

## v1.0.1

- Added diminishing returns for GDP and replaced linear GDP income scaling with a softer GDP anchor.
- Added economy, technology and excessive-reserve maintenance costs to slow money runaway.
- Limited AI research cadence and added technology soft-cap pressure.
- Added AI stability crisis outcomes: recovery program, regime change, civil unrest and debt restructuring.
- Reworked event choice labels/descriptions so categories no longer all use identical `Stabilize` / `Exploit` options.
- Changed saves to compact JSON and sparse relation serialization while preserving old full relation-matrix migration.
- Added diplomacy consequences for guarantees, sanction retaliation and stored ultimatum outcomes.
- Expanded notification categories and localized new v1.0.1 UI/log keys in English, Russian, German and Ukrainian.
- Refactored country Alpha indicators and finance helpers into `core/country_indicators.py`; `core/country_model.py` is below 400 lines again.
- Marked root compatibility wrapper files as deprecated.
- Added regression tests for balance simulation, AI crisis handling, sparse saves, event choices and diplomacy guarantees.

## v1.0 Alpha

- Added interconnected country indicators: GDP, GDP per capita, unemployment, education, healthcare, military spending and tax income.
- Connected economy, stability, services, debt, inflation, resources and internal problems through monthly indicator drift.
- Added 100+ data-driven events with categories, trigger conditions, descriptions, response choices and gameplay effects.
- Expanded diplomacy with sanctions, trade agreements, military pacts, guarantees of independence and ultimatums.
- Deepened war calculations with national army morale, experience, equipment wear, supply readiness and combined arms effects.
- Improved AI strategy for investments, buildings, research, treaties, sanctions, ultimatums and war target selection.
- Updated country detail, overview, diplomacy and statistics UI to expose the new Alpha systems.
- Updated Save/Load schema to `1.0-alpha` with migration from v0.6, v0.7, v0.8 and v0.9.
- Added regression coverage for Alpha events, diplomacy, economy indicators, army stats, v0.9 migration and AI smoke behavior.

## v0.9.1

- Prepared the project for GitHub publication and future collaborative development.
- Added MIT `LICENSE`.
- Added `CONTRIBUTING.md`.
- Added GitHub issue templates for bug reports and feature requests.
- Added a pull request template with testing, Save/Load, localization and asset-source checks.
- Added GitHub Actions workflow for py_compile, package compile and smoke tests.
- Cleaned up README with setup, run, controls, project structure, tests, asset guidance and roadmap.
- Added `core/version.py` with `GAME_VERSION = "0.9.1"` and `SAVE_SCHEMA_VERSION = "0.9"`.

## v0.9

- Moved the active project into `D:\GrandStrategy\` to avoid scanning or backing up unrelated files in the drive root.
- Added Save/Load schema version `0.9` with migration normalization for v0.6, v0.7 and v0.8 saves.
- Reduced save size by omitting static map geometry from country save data and restoring it from Natural Earth on load.
- Made `Country.units` the source of military strength and synchronized map army markers after recruitment, production, losses, events and loading.
- Fixed country-search text input so printable characters are handled by `TEXTINPUT` only.
- Added map/render performance cleanup: pre-transform bbox culling and cached ocean/menu/shadow surfaces.
- Replaced internal wrapper imports with direct package imports while keeping root wrappers for compatibility.
- Added localization parity coverage and `ASSET_CREDITS.md`.

## v0.8

- Added centralized `AssetManager` for cached icons, flags, images, sounds and fonts.
- Generated PNG UI icons for economy, army, diplomacy, resources, construction, settings, save/load and more.
- Added 171 real country flag PNGs from FlagCDN keyed by ISO alpha-2 code, with placeholder fallback.
- Added generated WAV UI feedback sounds for buttons, popups, war, error, save and load.
- Added a generated main menu background image and stronger visual identity.
- Improved map polish: clipped rendering, richer ocean color, cleaner borders, better labels and river colors.
- Added real flag rendering to country selection and in-game country detail panels.
- Added icons to the main menu, country card, top bar, left tabs and many action buttons.
- Extended country metadata with `iso_a2` while preserving old save compatibility.
- Added smoke coverage for AssetManager, country search text input and Esc menu state.

## v0.7

- Added a main menu with New Game, Load Game, Settings, Credits and Exit.
- Added a dedicated country selection screen with search, continent filter, sorting and a country details card.
- Reworked the UI theme with modern panels, rounded buttons, hover states, tooltips and larger map space.
- Added an Esc menu with Resume, Save, Load, Settings, Main Menu and Exit.
- Added localization scaffolding for English, Russian, German and Ukrainian.
- Added persistent UI settings in `saves/settings.json`.
- Moved saves, screenshots and backups into dedicated folders.
- Added `requirements.txt` and `.gitignore`.
- Split the in-game HUD into `ui/game_view.py` to keep UI files small.

## v0.6

- Refactored large files into packages: `core/`, `systems/`, `ui/`, `map/`, `ai/`.
- Split systems for economy, diplomacy, family, governance, construction, resources, technology, war, armies and Save/Load.
- Added automated smoke tests.
- Added README and changelog.
- Preserved Save/Load compatibility with v0.4 and v0.5-style saves.
- Kept map polygon projection cached in the renderer.

## v0.5

- Replaced the block map with a Natural Earth GeoJSON world map.
- Added 177 countries with real polygons.
- Added camera zoom and drag.
- Added country picking by real borders.
- Added flags, capitals, labels, map icons, map armies and army movement.
- Added front coordinates and army stances.
- Added AI profiles by country strategy.

## v0.4

- Added country overview dashboard.
- Added victory goals, game over, internal problems and settings.
- Added important notifications and pause-on-alert behavior.
- Improved AI decision logic.
- Added v0.3 save compatibility handling.

## v0.3

- Improved the simplified map layout.
- Added fronts, supply, unit types, factories, production and construction.
- Added resource trading, inflation, debt and statistics screen.

## v0.2

- Added real year/month calendar.
- Added long wars, peace treaties and war demands.
- Added provinces, resources, laws and democratic elections.
- Improved UI layout with separate message area.

## v0.1

- Initial Pygame prototype.
- Added country selection, simplified world map, economy, army, diplomacy, politics, family, war and technology tabs.
- Added basic AI, events and JSON Save/Load.
