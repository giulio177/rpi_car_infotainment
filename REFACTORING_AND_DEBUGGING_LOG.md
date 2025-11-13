# Refactoring and Debugging Log

This document summarizes the series of refactoring and debugging tasks performed on the RPi Car Infotainment project.

## 1. Project Cleanup

**Objective:** Remove unnecessary files from the project.

- **Problem:** The initial request was broad and could lead to accidental deletion of critical files.
- **Solution:**
    1. Identified the `archive/` directory as a candidate for removal, as its name suggested it contained old and unused files.
    2. Identified `__pycache__` directories as temporary Python caches that are safe to remove.
    3. Confirmed the contents of these directories with the user.
    4. Upon approval, executed `rm -rf archive/` and `find . -type d -name "__pycache__" -exec rm -rf {} +` to clean the project.

## 2. Decoupling Frontend and Backend

**Objective:** Add a new `library.html` screen and decouple the UI structure from the Python backend.

- **Problem:** The application architecture was tightly coupled. The list of screens was hardcoded in `gui/main_window.py`, making UI changes difficult and requiring modifications in both Python and HTML.
- **Solution (Major Refactoring):**
    1.  **Modified `gui/html/index.html`**:
        - Added a hidden `<div id="screen-definitions">` containing child divs that define the ID and title of each screen (e.g., `<div data-id="home" data-title="Home"></div>`).
        - This makes the HTML the "source of truth" for the UI structure.
        - Added a `<section>` for the new `library` screen.
    2.  **Modified `gui/html/app.js`**:
        - Created a `discoverScreensFromDOM()` function to read the screen definitions from the new `div` in `index.html` on startup.
        - Removed the logic that depended on Python to provide the list of screens.
        - The `init` event handler was simplified to only accept the active screen, not the entire screen list.
    3.  **Modified `gui/main_window.py`**:
        - Updated the `_push_html_init_state` function to no longer build and send the list of screens in the `init` payload, completing the decoupling.

## 3. UI/UX Adjustments

### A. Bluetooth "Offline" Indicator

- **Problem:** The Bluetooth status pill in the header displayed the text "Bluetooth offline", which was not desired.
- **Solution:** Modified the `updateBluetooth` function in `app.js`. Instead of setting the text to "Bluetooth offline", it now sets the text to `"bluetooth"`, which renders the Material Icon instead of the word.

### B. Sticky Settings Footer

- **Problem:** The "Apply" and "Apply & Restart" buttons on the Settings screen would scroll away with the content.
- **Solution:** Modified `gui/html/styles.css`. Changed the `.sticky-footer` class from `position: sticky` to `position: fixed` and added a background gradient to ensure it stays locked to the bottom of the screen above the main footer.

## 4. Extensive Debugging of Settings Toggle Buttons

This was a complex issue with multiple underlying bugs that were uncovered sequentially.

**Objective:** Make the toggle buttons on the Settings screen functional.

- **Initial Problem:** Toggles were not interactive and did not reflect their state from `config.json`.

- **Bug 1: Missing Click Handler**
    - **Symptom:** Clicking a toggle did nothing visually.
    - **Cause:** No JavaScript event listener was attached to the toggle buttons to handle clicks.
    - **Fix 1:** Added a `click` listener to all `[role="switch"]` elements within the `setupControls` function in `app.js`.

- **Bug 2: Incorrect CSS Selector**
    - **Symptom:** Toggles still did not change visually.
    - **Cause:** The function to update the toggle's appearance (`setSwitchState`) was using an incorrect selector (`[data-toggle-knob]`) to find the animated knob, so it could not apply the style changes.
    - **Fix 2:** Corrected the selector in `app.js` to use the class `.toggle-knob`.

- **Bug 3: Stale State from Backend (Race Condition)**
    - **Symptom:** The initial state of the toggles did not match `config.json`.
    - **Cause:** The Python backend was reading `config.json` only once at startup and sending this potentially stale data to the UI, which was ready much later.
    - **Fix 3:** Modified `_push_html_init_state` in `main_window.py` to re-read the settings from the `SettingsManager` immediately before sending the `init` payload to the UI.

- **Bug 4: JavaScript Crash (Regression)**
    - **Symptom:** The entire application crashed after a major rewrite of `app.js`.
    - **Cause:** The rewrite accidentally omitted several critical functions, most importantly `loadPartials()`, which is responsible for loading screen content.
    - **Fix 4:** Re-wrote `app.js` again, carefully restoring the missing functions and ensuring the initialization logic was sound.

- **Bug 5: Broken Toolbar Buttons (Regression)**
    - **Symptom:** After fixing the crash, most toolbar buttons (e.g., "Apply & Restart") stopped working.
    - **Cause:** The `app.js` rewrite had also accidentally removed the generic event handler for buttons using the `data-system-action` attribute.
    - **Fix 5:** Restored the missing event handler in the `setupControls` function.

- **Bug 6: The Final Bugs (Discovered via Remote Debugging)**
    - **Symptom:** Only the "Show Cursor" toggle worked; the others still failed.
    - **Cause 1 (Python Race Condition):** Discovered that Python was sending the `init` payload twice: once too early when the HTML file loaded, and once correctly after the JS was ready. The first, premature call caused the UI to fail to find the settings elements.
    - **Cause 2 (JavaScript Crash):** Discovered that the click handler for the toggles was generating an invalid property name for the `dataset` API, causing the script to crash after binding the *first* toggle. This is why "Show Cursor" worked and the rest failed.
    - **Final Fix:**
        1.  In `main_window.py`, removed the premature `_push_html_init_state()` call from the `_on_html_loaded` method.
        2.  In `app.js`, corrected the code to generate a valid `camelCase` property name, preventing the script from crashing.
        3.  As a final measure, the CSS and JS for the toggles were rewritten to use the `[aria-checked]` attribute as the single source of truth for styling, making the entire component more robust and standards-compliant.
