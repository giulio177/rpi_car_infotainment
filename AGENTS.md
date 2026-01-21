# RPi Car Infotainment - Developer Guidelines

## 1. Project Context
This is a Raspberry Pi-based car infotainment system designed for 1024x600 touchscreens. It features a dual-mode GUI:
1.  **Native Mode:** Pure PyQt6 widgets (default, highly optimized for Pi).
2.  **HTML Mode:** Embedded Chromium (PyQt6-WebEngine) using Tailwind CSS for styling.

The backend manages hardware (OBD-II, Radio, Bluetooth, WiFi, AirPlay) independently of the GUI to ensure stability.

## 2. Environment Setup & Build Commands

### System Dependencies
The system relies on `dbus-python`, `pulseaudio`, and `bluez`. On macOS/Linux dev machines, you might need:
```bash
brew install python-tk portaudio # macOS
sudo apt install libdbus-1-dev libglib2.0-dev # Linux
```

### Python Environment
Always use the virtual environment to avoid polluting system Python.
```bash
# Setup
python3 -m venv --system-site-packages venv
source venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-qt pytest-mock  # Dev dependencies

# Running the App
python main.py                              # Standard Native Mode
INFOTAINMENT_UI_MODE=html python main.py    # HTML/WebEngine Mode
```

### Frontend Build (HTML Mode Only)
If you modify files in `gui/html/` (CSS/JS), you must rebuild the Tailwind bundle:
```bash
npm install               # Install node modules
npm run build:tailwind    # Build finalized CSS
npm run dev:tailwind      # Watch mode for rapid UI dev
```

### Testing & Verification
All new features must include tests.
```bash
# Run the full suite
pytest

# Run a specific test file (e.g., UI Layout)
pytest tests/test_ui_layout.py

# Run a specific test case (e.g., Audio Manager logic)
pytest tests/test_audio_manager.py::test_volume_control -v

# Run with output (useful for debugging prints)
pytest -s
```

## 3. Code Style & Conventions

### Python Guidelines
- **Standard:** Strict PEP 8.
- **Formatting:** Use `black` or `ruff` defaults (line length 88-100 is acceptable).
- **Type Hinting:** Strictly required for `backend/` modules. Optional but recommended for `gui/`.
  ```python
  def calculate_fuel(self, liters: float) -> float: ...
  ```
- **Imports:** Grouped and sorted:
  1.  Standard Library (`os`, `sys`, `typing`)
  2.  Third-party (`PyQt6`, `requests`, `gpiozero`)
  3.  Local (`backend.managers`, `gui.widgets`)
- **Naming:**
  - `PascalCase` for Classes (`WiFiManager`).
  - `snake_case` for methods/variables (`connect_to_network`).
  - `UPPER_CASE` for module constants (`DEFAULT_TIMEOUT`).
  - `_leading_underscore` for internal/private methods (`_handle_signal`).

### PyQt/GUI Patterns
- **Signals:** Use `pyqtSignal` for all inter-component communication. NEVER call methods on other widgets directly if they are siblings.
- **Slots:** Decorate event handlers with `@pyqtSlot()`.
- **Threading:** Heavy hardware I/O (OBD, Radio tuning, Network scans) MUST run in background threads or `QThread`. Use `pyqtSignal` to update the UI from these threads. **Never** block the main GUI thread.

### HTML/JS Guidelines (Hybrid Mode)
- **Communication:** Use the `QWebChannel` bridge. Send JSON payloads.
  - Python -> JS: `self.html_view.send_event("event_name", payload)`
  - JS -> Python: `backend.send_event("action_name", payload)`
- **Styling:** Use Utility-first Tailwind classes. Avoid writing custom CSS in `styles.css` unless necessary for complex animations.

## 4. Error Handling & Safety
- **Hardware Abstraction:** Wrap all hardware calls (GPIO, Serial, I2C) in `try...except` blocks. The app must run on a Desktop (where hardware is missing) without crashing.
- **Graceful Degradation:** If `gpiozero` is missing, the Power Manager should log a warning and disable buttons, not crash the app.
- **Paths:** Use absolute paths relative to `__file__`:
  ```python
  BASE_DIR = os.path.dirname(os.path.abspath(__file__))
  icon_path = os.path.join(BASE_DIR, "assets", "icon.png")
  ```

## 5. Deployment & Hardware Config (Important)
- **Boot Script:** `scripts/install_rpi_car_infotainment.sh` is the master setup script.
- **Secure Shutdown:** We use a hardware-assisted shutdown flow on **GPIO 17**:
  1.  **Boot:** GPIO 17 driven **HIGH** immediately (Keep-Alive signal).
  2.  **Running:** GPIO 17 stays HIGH.
  3.  **Shutdown:** GPIO 17 driven **LOW** by kernel (`dtoverlay=gpio-poweroff`) only when safe.
  - *Do not change GPIO 17 logic without verifying hardware circuit compatibility.*
- **Boot Speed:** `disable_splash=1` and `boot_delay=0` are set in `config.txt` for fast startup.
- **Audio:** PulseAudio is configured for "Just Works" A2DP sink mode with automatic loopback to the analog jack.

## 6. Git & Commit Protocol
- **Messages:** Use imperative mood ("Fix bug" not "Fixed bug").
- **Scope:** Prefix commits with the module affected:
  - `[GUI] Fix alignment in settings`
  - `[OBD] Add retry logic for connection`
  - `[System] Update install script`
- **Review:** Self-review `git diff` before committing. Ensure no debug prints (`print()`) are left in production code; use `log_streamer.py` if logging is needed.

## 7. Critical Files (Source of Truth)
- `config.json`: User settings schema.
- `requirements.txt`: Python package versions.
- `AGENTS.md`: This file.
