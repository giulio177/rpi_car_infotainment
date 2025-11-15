/**
 * @file Main JavaScript application for the RPi Car Infotainment HTML UI.
 *
 * This script runs within a Qt WebEngineView and communicates with the Python
 * backend via a QWebChannel. It handles UI updates, user interactions, and
 * state management for the frontend.
 */
(() => {
    // =================================================================================
    // Application State
    // =================================================================================
    const state = {
        screens: [],
        screenMap: new Map(),
        navButtons: new Map(),
        active: null,
        defaultArt: "assets/media/album_placeholder.svg",
        snapshots: {
            volume: null,
            bluetooth: null,
            radio: null,
            obd: null,
            media: null,
            settings: null,
        },
    };

    // =================================================================================
    // DOM Element Cache
    // =================================================================================
    const elements = {
        app: document.getElementById("app"),
        main: document.getElementById("main"),
        headerTitle: document.getElementById("header-title"),
        clock: document.getElementById("clock"),
        bluetoothPill: document.getElementById("bluetooth-pill"),
        // Dynamic elements are populated by collectDynamicRefs() after partials load
    };

    function collectDynamicRefs() {
        // Static controls
        elements.volumeMute = document.getElementById("volume-mute");
        elements.volumeSlider = document.getElementById("volume-slider");
        elements.btnBluetooth = document.getElementById("open-bluetooth");
        elements.btnWifi = document.getElementById("open-wifi");
        elements.btnRestartApp = document.getElementById("restart-app");
        elements.btnReboot = document.getElementById("reboot-system");
        elements.btnQuit = document.getElementById("quit-app");

        // Screen-specific controls
        elements.home = {
            art: document.getElementById("home-art"),
            title: document.getElementById("home-title"),
            artist: document.getElementById("home-artist"),
            album: document.getElementById("home-album"),
            progress: document.getElementById("home-progress"),
            status: document.getElementById("home-status"),
            source: document.getElementById("home-source"),
        };
        elements.music = {
            art: document.getElementById("music-art"),
            title: document.getElementById("music-title"),
            artist: document.getElementById("music-artist"),
            album: document.getElementById("music-album"),
            progress: document.getElementById("music-progress"),
            status: document.getElementById("music-status"),
            mediaPrev: document.getElementById("media-previous"),
            mediaPlay: document.getElementById("media-play"),
            mediaNext: document.getElementById("media-next"),
        };
        elements.settings = {
            theme: document.getElementById("settings-theme"),
            ui_render_mode: document.getElementById("settings-ui_render_mode"),
            ui_scale_mode: document.getElementById("settings-ui_scale_mode"),
            window_resolution: document.getElementById("settings-window_resolution"),
            show_cursor: document.getElementById("settings-show_cursor"),
            position_bottom_right: document.getElementById("settings-position_bottom_right"),
            developer_mode: document.getElementById("settings-developer_mode"),
            radio_enabled: document.getElementById("settings-radio_enabled"),
            radio_type: document.getElementById("settings-radio_type"),
            last_fm_station: document.getElementById("settings-last_fm_station"),
            radio_i2c_address: document.getElementById("settings-radio_i2c_address"),
            obd_enabled: document.getElementById("settings-obd_enabled"),
            obd_port: document.getElementById("settings-obd_port"),
            obd_baudrate: document.getElementById("settings-obd_baudrate"),
        };
        elements.applySettings = document.getElementById("settings-apply");
        elements.radioStatus = document.getElementById("radio-status");
        elements.obdStatus = document.getElementById("obd-status");
    }

    // =================================================================================
    // Settings Toggle Switch Logic (REWRITTEN AND FIXED)
    // =================================================================================

    const toggleMessages = {
        developer_mode: { on: "Enabled", off: "Disabled" },
        radio_enabled: { on: "Enabled", off: "Disabled" },
        obd_enabled: { on: "Enabled", off: "Disabled" },
    };

    function setSwitchState(element, isOn, key) {
        if (!element) {
            console.error(`[setSwitchState] Called with null element for key: ${key}`);
            return;
        }
        console.log(`[setSwitchState] Called for key: '${key}', setting state to: ${isOn}`);

        try {
            element.setAttribute("aria-checked", isOn ? "true" : "false");
            console.log(`[setSwitchState] Attribute 'aria-checked' set to '${isOn}' on element`, element);

            const label = document.querySelector(`[data-toggle-label="${key}"]`);
            if (label) {
                console.log(`[setSwitchState] Found label for key: '${key}'`, label);
                const messages = toggleMessages[key] || { on: "On", off: "Off" };
                const newText = isOn ? messages.on : messages.off;
                console.log(`[setSwitchState] Setting label text to: '${newText}'`);
                label.textContent = newText;
                console.log(`[setSwitchState] Label text set successfully for key: '${key}'.`);
            } else {
                console.log(`[setSwitchState] No label found for key: '${key}'. This is expected for some toggles like 'Show Cursor'.`);
            }
            console.log(`[setSwitchState] Completed successfully for key: '${key}'.`);
        } catch (e) {
            console.error(`[setSwitchState] CRITICAL ERROR for key '${key}':`, e);
        }
    }

    function getSwitchValue(element) {
        return element ? element.getAttribute("aria-checked") === "true" : false;
    }

    function bindToggleSwitch(toggle) {
        const key = toggle.id.replace('settings-', '');
        // Create a valid camelCase key like 'boundToggleDeveloperMode' for the dataset
        const camelCaseKey = ('bound_toggle_' + key).replace(/_([a-z])/g, (g) => g[1].toUpperCase());

        bindEventOnce(toggle, "click", (event) => {
            event.preventDefault();
            const isChecked = toggle.getAttribute("aria-checked") === "true";
            setSwitchState(toggle, !isChecked, key);
        }, camelCaseKey);
    }

    // =================================================================================
    // Backend Communication & Event Handling
    // =================================================================================

    function emit(name, payload) {
        if (window.bridge && typeof window.bridge.emit_event === "function") {
            window.bridge.emit_event(name, payload || {});
        }
    }

    window.__pyBridgeDispatch = function dispatchFromPython(name, payload) {
        const handler = handlers[name];
        if (handler) {
            handler(payload || {});
        } else {
            console.debug("[HTML] Unhandled event from Python:", name, payload);
        }
    };

    function renderLibrary(tracks) {
        const container = document.getElementById("library-items");
        if (!container) {
            console.warn("[HTML] library-items container not found");
            return;
        }

        container.innerHTML = "";

        if (!tracks || !tracks.length) {
            container.innerHTML = `<p class="empty-state">No tracks found in library.</p>`;
            return;
        }

        tracks.forEach((track, index) => {
            const isActive = index === 0; // se vuoi il primo evidenziato

            const btn = document.createElement("button");
            btn.className = "track-item" + (isActive ? " track-item--active" : "");
            btn.dataset.trackId = track.id || track.filename || `track-${index}`;

            btn.innerHTML = `
            <div class="track-item__left">
                <div class="track-item__icon ${isActive ? "track-item__icon--active" : ""}">
                <span class="material-symbols-outlined">
                    ${isActive ? "volume_up" : "music_note"}
                </span>
                </div>
                <div class="track-item__meta">
                <p class="track-item__title ${isActive ? "track-item__title--active" : ""}">
                    ${track.title || track.filename || "Unknown"}
                </p>
                <p class="track-item__subtitle">
                    ${track.artist || track.filename || ""}
                </p>
                </div>
            </div>
            <span class="track-item__duration ${isActive ? "track-item__duration--active" : ""}">
                ${track.duration || "--:--"}
            </span>
            `;

            // qui un domani puoi attaccare il play:
            // btn.addEventListener("click", () => emit("play_track", { id: btn.dataset.trackId }));

            container.appendChild(btn);
        });
    }


    const handlers = {
        init(payload) {
            setActiveScreen(payload.active || 'home');
            if (payload.theme) elements.app.dataset.theme = payload.theme;
            if (payload.volume) updateVolume(payload.volume);
            if (payload.bluetooth) updateBluetooth(payload.bluetooth);
            if (payload.radio) updateStatusElement(elements.radioStatus, payload.radio.status);
            if (payload.obd) updateStatusElement(elements.obdStatus, payload.obd.status);
            if (payload.media) updateMedia(payload.media);
            if (payload.settings) updateSettings(payload.settings);
        },
        navigation(payload) {
            if (payload.screen) setActiveScreen(payload.screen);
        },
        clock(payload) {
            if (payload.value) elements.clock.textContent = payload.value;
        },
        volume: updateVolume,
        bluetooth_status: updateBluetooth,
        radio_status(payload) {
            if (payload) updateStatusElement(elements.radioStatus, payload.status);
        },
        obd_status(payload) {
            if (payload) updateStatusElement(elements.obdStatus, payload.status);
        },
        media: updateMedia,
        settings: updateSettings,
        library_update(payload) {
            renderLibrary(payload.tracks || []);
        },

    };

    // =================================================================================
    // Screen and Navigation Management
    // =================================================================================

    function discoverScreensFromDOM() {
        const screenDefs = document.querySelectorAll("#screen-definitions > div");
        state.screens = Array.from(screenDefs).map(def => ({ id: def.dataset.id, title: def.dataset.title }));
        state.screenMap.clear();
        state.screens.forEach(screen => {
            state.screenMap.set(screen.id, screen);
            ensureScreenSection(screen.id, screen.title);
        });

        state.navButtons.clear();
        document.querySelectorAll("[data-navigate]").forEach(button => {
            const screenId = button.dataset.navigate;
            if (state.screenMap.has(screenId)) {
                state.navButtons.set(screenId, button);
            }
        });
    }

    function ensureScreenSection(id, title) {
        if (!document.getElementById(`screen-${id}`)) {
            const section = document.createElement("section");
            section.id = `screen-${id}`;
            section.className = "screen";
            section.innerHTML = `<div class="partial-loading">Loading ${title}...</div>`;
            elements.main.appendChild(section);
        }
    }

    function setActiveScreen(id) {
        if (!id || !state.screenMap.has(id)) {
            console.warn(`[HTML] Attempted to navigate to unknown screen: '${id}'`);
            return;
        }
        state.active = id;
        state.navButtons.forEach((button, buttonId) => button.classList.toggle("active", buttonId === id));
        document.querySelectorAll(".screen").forEach(section => section.classList.remove("active"));
        
        const section = document.getElementById(`screen-${id}`);
        if (section) section.classList.add("active");

        const screenEntry = state.screenMap.get(id);
        elements.headerTitle.textContent = screenEntry ? screenEntry.title : "RPi Car Infotainment";

        // Se entri nella schermata Library, chiedi a Python la lista dei file
        if (id === "library") {
            emit("library_request", {});
        }
    }

    function triggerNavigation(screenId) {
        if (screenId && state.screenMap.has(screenId)) {
            setActiveScreen(screenId);
            emit("navigate", { screen: screenId });
        }
    }

    // =================================================================================
    // UI Update Functions
    // =================================================================================

    function reapplySnapshots() {
        if (state.snapshots.volume) updateVolume(state.snapshots.volume);
        if (state.snapshots.bluetooth) updateBluetooth(state.snapshots.bluetooth);
        if (state.snapshots.radio) updateStatusElement(elements.radioStatus, state.snapshots.radio.status);
        if (state.snapshots.obd) updateStatusElement(elements.obdStatus, state.snapshots.obd.status);
        if (state.snapshots.media) updateMedia(state.snapshots.media);
        if (state.snapshots.settings) updateSettings(state.snapshots.settings);
    }

    function updateStatusElement(element, value) {
        if (element) {
            element.textContent = `Status: ${value || "--"}`;
        }
    }

    function updateVolume(data) {
        if (!data) return;
        state.snapshots.volume = { ...data };
        if (elements.volumeSlider && typeof data.level === "number") {
            elements.volumeSlider.value = data.level;
        }
        if (elements.volumeMute) {
            elements.volumeMute.innerHTML = data.muted ?
                '<span class="material-symbols-outlined">volume_off</span>' :
                '<span class="material-symbols-outlined">volume_up</span>';
        }
    }

    function updateBluetooth(data) {
        if (!data || !elements.bluetoothPill) return;
        state.snapshots.bluetooth = { ...data };
        const pill = elements.bluetoothPill;
        const connected = !!data.connected;
        pill.classList.toggle("pill--online", connected);
        pill.classList.toggle("pill--offline", !connected);

        if (connected) {
            const batteryLabel = typeof data.battery === "number" ? ` • ${data.battery}%` : "";
            pill.textContent = `${data.device || "Connected"}${batteryLabel}`;
        } else {
            pill.textContent = "bluetooth";
        }
    }

    function updateMedia(data) {
        if (!data) return;
        state.snapshots.media = { ...data };
        const statusLabel = data.status || "stopped";
        const progress = `${formatTime(data.position || 0)} / ${formatTime(data.duration || 0)}`;

        const targets = [elements.home, elements.music];
        targets.forEach(target => {
            if (target) {
                if (target.title) target.title.textContent = data.title || "No track";
                if (target.artist) target.artist.textContent = data.artist || "--";
                if (target.album) target.album.textContent = data.album || "--";
                if (target.progress) target.progress.textContent = progress;
                if (target.status) target.status.textContent = `Status: ${statusLabel}`;
                if (target.source) target.source.textContent = `Source: ${formatSource(data.source)}`;
                if (target.art) target.art.src = data.art || state.defaultArt;
            }
        });
        if (elements.music && elements.music.mediaPlay) {
            elements.music.mediaPlay.textContent = statusLabel === "playing" ? "⏸" : "⏯";
        }
    }

    function updateSettings(data) {
        if (!data) return;
        state.snapshots.settings = { ...state.snapshots.settings, ...data };

        Object.entries(data).forEach(([key, value]) => {
            // Bypassing the cache and querying the DOM directly for robustness.
            const el = document.getElementById(`settings-${key}`);
            
            if (!el) {
                // This log will appear in the developer console if an element is missing.
                console.log(`[SETTINGS] Element not found for key: settings-${key}`);
                return;
            }

            if (el.getAttribute("role") === "switch") {
                setSwitchState(el, !!value, key);
            } else if (el.tagName === "SELECT") {
                el.value = String(value ?? "");
            } else if (el.tagName === "INPUT") {
                el.value = (el.type === "range") ? (Number(value) || 0) : (value ?? "");
            }
        });
    }

    // =================================================================================
    // User Input and Control Setup
    // =================================================================================

    function bindEventOnce(element, type, handler, key) {
        if (!element) return;
        const datasetKey = key || `bound${type.toUpperCase()}`;
        if (element.dataset[datasetKey]) return;
        element.addEventListener(type, handler);
        element.dataset[datasetKey] = "true";
    }

    function setupControls() {
        // Global controls
        bindEventOnce(elements.volumeSlider, "input", (e) => emit("set_volume", { value: Number(e.target.value) }));
        bindEventOnce(elements.volumeMute, "click", () => emit("toggle_mute", {}));
        bindEventOnce(elements.btnBluetooth, "click", () => emit("open_dialog", { target: "bluetooth" }));
        bindEventOnce(elements.btnWifi, "click", () => emit("open_dialog", { target: "wifi" }));
        bindEventOnce(elements.btnRestartApp, "click", () => emit("system_action", { action: "restart_app" }));
        bindEventOnce(elements.btnReboot, "click", () => emit("system_action", { action: "reboot" }));
        bindEventOnce(elements.btnQuit, "click", () => emit("system_action", { action: "quit" }));

        // Media controls
        if (elements.music) {
            bindEventOnce(elements.music.mediaPrev, "click", () => emit("media_control", { action: "previous" }));
            bindEventOnce(elements.music.mediaPlay, "click", () => emit("media_control", { action: "play_pause" }));
            bindEventOnce(elements.music.mediaNext, "click", () => emit("media_control", { action: "next" }));
        }

        // Generic data-attribute based controls
        document.querySelectorAll("[data-navigate]").forEach(button => {
            bindEventOnce(button, "click", (e) => {
                e.preventDefault();
                triggerNavigation(button.dataset.navigate);
            }, `boundNavigate${button.dataset.navigate}`);
        });
        
        // RESTORED: Generic handler for system actions
        document.querySelectorAll("[data-system-action]").forEach(button => {
            bindEventOnce(button, "click", (e) => {
                e.preventDefault();
                if (button.dataset.applySettings === "true") {
                    emit("apply_settings", buildSettingsPayload());
                }
                emit("system_action", { action: button.dataset.systemAction });
            }, `boundSystemAction${button.dataset.systemAction}`);
        });
        
        // Settings screen controls
        if (elements.applySettings) {
            bindEventOnce(elements.applySettings, "click", (e) => {
                e.preventDefault();
                emit("apply_settings", buildSettingsPayload());
            }, "boundApplySettings");
        }
        
        document.querySelectorAll('[role="switch"]').forEach(bindToggleSwitch);
    }

    function buildSettingsPayload() {
        const refs = elements.settings;
        if (!refs) return {};
        return {
            theme: refs.theme?.value,
            ui_render_mode: refs.ui_render_mode?.value,
            ui_scale_mode: refs.ui_scale_mode?.value,
            window_resolution: refs.window_resolution?.value,
            show_cursor: getSwitchValue(refs.show_cursor),
            position_bottom_right: getSwitchValue(refs.position_bottom_right),
            developer_mode: getSwitchValue(refs.developer_mode),
            radio_enabled: getSwitchValue(refs.radio_enabled),
            obd_enabled: getSwitchValue(refs.obd_enabled),
            radio_type: refs.radio_type?.value,
            last_fm_station: refs.last_fm_station?.value.trim(),
            radio_i2c_address: refs.radio_i2c_address?.value.trim(),
            obd_port: refs.obd_port?.value.trim(),
            obd_baudrate: refs.obd_baudrate?.value.trim(),
        };
    }

    // =================================================================================
    // Utility and Initialization
    // =================================================================================

    function formatTime(ms) {
        if (!ms || Number.isNaN(ms)) return "00:00";
        const totalSeconds = Math.floor(ms / 1000);
        const minutes = Math.floor(totalSeconds / 60).toString().padStart(2, "0");
        const seconds = (totalSeconds % 60).toString().padStart(2, "0");
        return `${minutes}:${seconds}`;
    }

    function formatSource(source) {
        if (!source) return "No source";
        const label = String(source);
        return label.charAt(0).toUpperCase() + label.slice(1);
    }

    function loadPartials() {
        const sections = Array.from(document.querySelectorAll("[data-partial]"));
        if (!sections.length) return Promise.resolve();

        const tasks = sections.map((section) => {
            const name = section.dataset.partial;
            if (!name) return Promise.resolve();

            const url = `screens/${name}.html`;
            return fetch(url)
                .then((response) => {
                    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
                    return response.text();
                })
                .then((html) => { section.innerHTML = html; })
                .catch((error) => {
                    console.error(`[HTML] Failed to load partial ${url}:`, error);
                    section.innerHTML = `<div class="partial-error">Unable to load ${name}.html</div>`;
                });
        });
        return Promise.all(tasks);
    }

    function init() {
        discoverScreensFromDOM();
        
        const partialPromise = loadPartials();
        partialPromise.then(() => {
            // This runs after all HTML partials are loaded
            collectDynamicRefs();
            setupControls();
            reapplySnapshots();
        });

        new QWebChannel(qt.webChannelTransport, (channel) => {
            window.bridge = channel.objects.bridge;
            // Wait for partials to be fully loaded and controls to be bound
            // before signaling that the frontend is ready.
            partialPromise.finally(() => {
                emit("ready", {});
            });
        });
    }

    init();

})();
