# Repository Guidelines

## Project Structure & Module Organization
- Core Python logic lives in `backend/` (managers for audio, radio, AirPlay, Wi-Fi) and `gui/` (PyQt6 screens, widgets, theming).
- Static visuals are under `assets/` and deployment artifacts live in `deployment/` and `scripts/`; keep executable scripts compatible with systemd on Raspberry Pi OS Lite.
- Tests and setup checks sit in `tests/`; treat them as the single source of truth for expected file paths and boot behavior.
- Shared utilities (e.g., RF helpers) belong in `tools/`; avoid mixing platform-specific stubs with production modules.
- The HTML front-end for the optional embedded UI lives in `gui/html/`; `screens/` holds per-view partials and `dist/` stores the compiled Tailwind bundle.

## Build, Test, and Development Commands
- Create or refresh the virtualenv: `python3 -m venv --system-site-packages venv && source venv/bin/activate`.
- Install dependencies: `pip install -r requirements.txt`; re-run whenever requirements change.
- Launch the app locally on a desktop for quick UI checks: `python main.py`.
- Mirror the kiosk boot flow on Pi hardware with `./scripts/start_infotainment.sh` (expects `/dev/fb0` and the correct touchscreen event node).
- Run the automated checks: `pytest -q`; use `pytest tests/test_ui_layout.py::test_layout_consistency -q` for targeted investigations.
- Build Tailwind assets for the HTML UI: `npm run build:tailwind` (watch mode available via `npm run dev:tailwind`); source file is `gui/html/tailwind.css`.

## Coding Style & Naming Conventions
- Follow PEP 8 with four-space indentation and explicit imports; group Qt widgets, backend managers, and shared helpers as shown in `gui/main_window.py:1`.
- Use `CamelCase` for Qt widgets/screens, `snake_case` for functions, and suffix managers with `Manager`.
- Prefer descriptive logging via `log_streamer` and keep configuration constants in `config.json` or module-level uppercase names.
- Tailwind classes in HTML partials should lean on the design tokens defined in `tailwind.config.js`; augment global overrides in `gui/html/styles.css` when the utility set is insufficient.

## Testing Guidelines
- Place new integration checks beside related modules in `tests/`; name files `test_<feature>.py` and functions `test_<expectation>`.
- Mock hardware and network interfaces—never depend on live Bluetooth or OBD during automated runs; gate external calls behind feature flags.
- Aim to extend coverage for startup safety checks and UI scaling; replicate any new systemd or framebuffer requirements in the tests before shipping.
- When modifying Tailwind-driven screens, regenerate the compiled CSS and smoke test the HTML UI (`INFOTAINMENT_UI_MODE=html python main.py`) to validate layout changes.

## Commit & Pull Request Guidelines
- Use concise, sentence-case subjects (e.g., `Improve WiFi reconnection handling` as seen in `git log`); keep body lines wrapped at 72 chars when context is needed.
- Reference issue IDs or deployment impacts in the body, and include screenshots or framebuffer photos when UI changes are introduced.
- Pull requests should summarize hardware assumptions, list manual test steps (Pi and desktop), and note any Raspberry Pi OS configuration edits that contributors must reproduce.
- HTML UI contributions should mention whether Tailwind styles were rebuilt and include before/after captures when practical.

## HTML UI Runtime Notes
- The settings panel triggers an `apply_settings` bridge event; persist new options inside `MainWindow._handle_html_apply_settings` so they flush through `SettingsManager` and land in `config.json`.
- After mutating config from the HTML layer, call `refresh_html_settings()` (or `_update_settings_field`) to keep the JS snapshot in sync and avoid stale form controls.
