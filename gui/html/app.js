(() => {
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

    function collectHomeRefs() {
        return {
            container: document.getElementById("screen-home"),
            art: document.getElementById("home-art"),
            title: document.getElementById("home-title"),
            artist: document.getElementById("home-artist"),
            album: document.getElementById("home-album"),
            progress: document.getElementById("home-progress"),
            status: document.getElementById("home-status"),
            source: document.getElementById("home-source"),
        };
    }

    function collectSettingsRefs() {
        return {
            theme: document.getElementById("settings-theme"),
            ui_render_mode: document.getElementById("settings-ui_render_mode"),
            ui_scale_mode: document.getElementById("settings-ui_scale_mode"),
            window_resolution: document.getElementById("settings-window_resolution"),
            show_cursor: document.getElementById("settings-show_cursor"),
            position_bottom_right: document.getElementById("settings-position_bottom_right"),
            developer_mode: document.getElementById("settings-developer_mode"),
            volume: document.getElementById("volume-slider"),
            radio_enabled: document.getElementById("settings-radio_enabled"),
            radio_type: document.getElementById("settings-radio_type"),
            last_fm_station: document.getElementById("settings-last_fm_station"),
            radio_i2c_address: document.getElementById("settings-radio_i2c_address"),
            obd_enabled: document.getElementById("settings-obd_enabled"),
            obd_port: document.getElementById("settings-obd_port"),
            obd_baudrate: document.getElementById("settings-obd_baudrate"),
        };
    }

    const elements = {
        app: document.getElementById("app"),
        nav: document.getElementById("nav"),
        main: document.getElementById("main"),
        headerTitle: document.getElementById("header-title"),
        clock: document.getElementById("clock"),
        bluetoothPill: document.getElementById("bluetooth-pill"),
        volumeMute: document.getElementById("volume-mute"),
        volumeSlider: document.getElementById("volume-slider"),
        mediaPrev: document.getElementById("media-previous"),
        mediaPlay: document.getElementById("media-play"),
        mediaNext: document.getElementById("media-next"),
        btnBluetooth: document.getElementById("open-bluetooth"),
        btnWifi: document.getElementById("open-wifi"),
        btnRestartApp: document.getElementById("restart-app"),
        btnReboot: document.getElementById("reboot-system"),
        btnQuit: document.getElementById("quit-app"),
        applySettings: document.getElementById("settings-apply"),
        home: collectHomeRefs(),
        music: {
            art: document.getElementById("music-art"),
            title: document.getElementById("music-title"),
            artist: document.getElementById("music-artist"),
            album: document.getElementById("music-album"),
            progress: document.getElementById("music-progress"),
            status: document.getElementById("music-status"),
        },
        radioStatus: document.getElementById("radio-status"),
        obdStatus: document.getElementById("obd-status"),
        settings: collectSettingsRefs(),
    };

    function cloneSnapshot(payload) {
        return payload && typeof payload === "object" ? { ...payload } : null;
    }

    function refreshDynamicRefs() {
        elements.home = collectHomeRefs();
        elements.music = {
            art: document.getElementById("music-art"),
            title: document.getElementById("music-title"),
            artist: document.getElementById("music-artist"),
            album: document.getElementById("music-album"),
            progress: document.getElementById("music-progress"),
            status: document.getElementById("music-status"),
        };
        elements.radioStatus = document.getElementById("radio-status");
        elements.obdStatus = document.getElementById("obd-status");
        elements.mediaPrev = document.getElementById("media-previous");
        elements.mediaPlay = document.getElementById("media-play");
        elements.mediaNext = document.getElementById("media-next");
        elements.volumeMute = document.getElementById("volume-mute");
        elements.volumeSlider = document.getElementById("volume-slider");
        elements.btnBluetooth = document.getElementById("open-bluetooth");
        elements.btnWifi = document.getElementById("open-wifi");
        elements.btnRestartApp = document.getElementById("restart-app");
        elements.btnReboot = document.getElementById("reboot-system");
        elements.btnQuit = document.getElementById("quit-app");
        elements.applySettings = document.getElementById("settings-apply");
        elements.settings = collectSettingsRefs();
    }

    function reapplySnapshots() {
        if (state.snapshots.volume) {
            updateVolume(state.snapshots.volume);
        }
        if (state.snapshots.bluetooth) {
            updateBluetooth(state.snapshots.bluetooth);
        }
        if (state.snapshots.radio) {
            updateStatusElement(elements.radioStatus, state.snapshots.radio.status);
        }
        if (state.snapshots.obd) {
            updateStatusElement(elements.obdStatus, state.snapshots.obd.status);
        }
        if (state.snapshots.media) {
            updateMedia(state.snapshots.media);
        }
        if (state.snapshots.settings) {
            updateSettings(state.snapshots.settings);
        }
    }

    function loadPartials() {
        const sections = Array.from(document.querySelectorAll("[data-partial]"));
        if (!sections.length) {
            return Promise.resolve();
        }

        const tasks = sections.map((section) => {
            const name = section.dataset.partial;
            if (!name) {
                return Promise.resolve();
            }
            const url = `screens/${name}.html`;
            return fetch(url)
                .then((response) => {
                    if (!response.ok) {
                        throw new Error(`${response.status} ${response.statusText}`);
                    }
                    return response.text();
                })
                .then((html) => {
                    section.innerHTML = html;
                })
                .catch((error) => {
                    console.error(`[HTML] Failed to load partial ${url}:`, error);
                    section.innerHTML =
                        `<div class="partial-error">Unable to load ${name}.html</div>`;
                });
        });

        return Promise.all(tasks).then(() => {
            refreshDynamicRefs();
            setupControls();
            reapplySnapshots();
        });
    }

    function emit(name, payload) {
        if (window.bridge && typeof window.bridge.emit_event === "function") {
            window.bridge.emit_event(name, payload || {});
        }
    }

    function ensureScreenSection(id, title) {
        const elementId = `screen-${id}`;
        if (document.getElementById(elementId)) {
            return;
        }
        const section = document.createElement("section");
        section.id = elementId;
        section.className = "screen";
        section.innerHTML = `<h2>${title}</h2><p>Content for ${title} is not yet customised for the HTML UI.</p>`;
        elements.main.appendChild(section);
    }

    function setActiveScreen(id) {
        if (!id) {
            return;
        }
        state.active = id;
        state.navButtons.forEach((button, buttonId) => {
            if (buttonId === id) {
                button.classList.add("active");
            } else {
                button.classList.remove("active");
            }
        });
        document.querySelectorAll(".screen").forEach((section) => {
            section.classList.remove("active");
        });
        const section = document.getElementById(`screen-${id}`);
        if (section) {
            section.classList.add("active");
        }
        const screenEntry = state.screenMap.get(id);
        elements.headerTitle.textContent = screenEntry ? screenEntry.title : "RPi Car Infotainment";
    }

    function updateNav(screens, active) {
        state.navButtons.clear();
        state.screenMap.clear();
        elements.nav.innerHTML = "";
        screens.forEach((screen) => {
            state.screenMap.set(screen.id, screen);
            ensureScreenSection(screen.id, screen.title);
            const button = document.createElement("button");
            button.className = "nav-button";
            button.textContent = screen.title;
            button.dataset.screen = screen.id;
            button.addEventListener("click", () => triggerNavigation(screen.id));
            elements.nav.appendChild(button);
            state.navButtons.set(screen.id, button);
        });
        setActiveScreen(active || (screens[0] && screens[0].id));
    }

    function formatTime(ms) {
        if (!ms || Number.isNaN(ms)) {
            return "00:00";
        }
        const totalSeconds = Math.floor(ms / 1000);
        const minutes = Math.floor(totalSeconds / 60)
            .toString()
            .padStart(2, "0");
        const seconds = (totalSeconds % 60).toString().padStart(2, "0");
        return `${minutes}:${seconds}`;
    }

    function formatSource(source) {
        if (!source) {
            return "No source";
        }
        const label = String(source);
        return label.charAt(0).toUpperCase() + label.slice(1);
    }

    const toggleMessages = {
        show_cursor: { on: "Visible", off: "Hidden" },
        developer_mode: { on: "Enabled", off: "Disabled" },
        position_bottom_right: { on: "Bottom-right", off: "Top-left" },
        radio_enabled: { on: "Enabled", off: "Disabled" },
        obd_enabled: { on: "Enabled", off: "Disabled" },
    };

    function setSwitchState(element, isOn, key) {
        if (!element) {
            return;
        }
        element.setAttribute("aria-checked", isOn ? "true" : "false");
        element.classList.toggle("bg-primary", isOn);
        element.classList.toggle("bg-surface-dark", !isOn);
        const knob = element.querySelector("[data-toggle-knob]");
        if (knob) {
            knob.classList.toggle("translate-x-7", isOn);
            knob.classList.toggle("translate-x-1", !isOn);
        }
        const label = document.querySelector(`[data-toggle-label="${key}"]`);
        if (label) {
            const messages = toggleMessages[key] || { on: "On", off: "Off" };
            label.textContent = isOn ? messages.on : messages.off;
        }
    }

    function getSwitchValue(element) {
        return element ? element.getAttribute("aria-checked") === "true" : false;
    }

    function readTextInput(element) {
        if (!element) {
            return "";
        }
        const value = typeof element.value === "string" ? element.value.trim() : "";
        return value;
    }

    function buildSettingsPayload() {
        const refs = elements.settings || collectSettingsRefs();
        const payload = {};
        if (!refs) {
            return payload;
        }

        if (refs.theme) {
            payload.theme = refs.theme.value;
        }
        if (refs.ui_render_mode) {
            payload.ui_render_mode = refs.ui_render_mode.value;
        }
        if (refs.ui_scale_mode) {
            payload.ui_scale_mode = refs.ui_scale_mode.value;
        }
        if (refs.window_resolution) {
            payload.window_resolution = refs.window_resolution.value;
        }

        payload.show_cursor = getSwitchValue(refs.show_cursor);
        payload.position_bottom_right = getSwitchValue(refs.position_bottom_right);
        payload.developer_mode = getSwitchValue(refs.developer_mode);
        payload.radio_enabled = getSwitchValue(refs.radio_enabled);
        payload.obd_enabled = getSwitchValue(refs.obd_enabled);

        if (refs.radio_type) {
            payload.radio_type = refs.radio_type.value;
        }

        payload.last_fm_station = readTextInput(refs.last_fm_station);
        payload.radio_i2c_address = readTextInput(refs.radio_i2c_address);
        payload.obd_port = readTextInput(refs.obd_port);
        payload.obd_baudrate = readTextInput(refs.obd_baudrate);

        return payload;
    }

    function updateVolume(data) {
        if (!data) {
            return;
        }
        state.snapshots.volume = cloneSnapshot(data);
        if (elements.volumeSlider && typeof data.level === "number") {
            elements.volumeSlider.value = data.level;
        }
        if (elements.volumeMute) {
            const muted = !!data.muted;
            elements.volumeMute.innerHTML = muted
                ? '<span class="material-symbols-outlined">volume_off</span>'
                : '<span class="material-symbols-outlined">volume_up</span>';
            elements.volumeMute.dataset.muted = muted ? "true" : "false";
        }
    }

    function updateBluetooth(data) {
        if (!data || !elements.bluetoothPill) {
            return;
        }
        state.snapshots.bluetooth = cloneSnapshot(data);
        const pill = elements.bluetoothPill;
        const connected = !!data.connected;
        pill.classList.toggle("pill--online", connected);
        pill.classList.toggle("pill--offline", !connected);
        if (connected) {
            const batteryLabel =
                typeof data.battery === "number" ? ` • ${data.battery}%` : "";
            pill.textContent = `${data.device || "Connected"}${batteryLabel}`;
        } else {
            pill.textContent = "Bluetooth offline";
        }
    }

    function updateStatusElement(element, value) {
        if (element) {
            element.textContent = `Status: ${value || "--"}`;
        }
    }

    function triggerNavigation(screenId) {
        if (!screenId) {
            return;
        }
        if (!state.screenMap.has(screenId)) {
            console.warn('[HTML] Unknown screen id', screenId);
        }
        setActiveScreen(screenId);
        emit("navigate", { screen: screenId });
    }

    function setArt(target, url) {
        if (!target) {
            return;
        }
        target.src = url || state.defaultArt;
    }

    function updateMedia(data) {
        if (!data) {
            return;
        }
        state.snapshots.media = cloneSnapshot(data);
        const statusLabel = data.status || "stopped";
        const progress = `${formatTime(data.position || 0)} / ${formatTime(data.duration || 0)}`;

        if (elements.home) {
            if (elements.home.title) {
                elements.home.title.textContent = data.title || "No track";
            }
            if (elements.home.artist) {
                elements.home.artist.textContent = data.artist || "--";
            }
            if (elements.home.album) {
                elements.home.album.textContent = data.album || "--";
            }
            if (elements.home.progress) {
                elements.home.progress.textContent = progress;
            }
            if (elements.home.status) {
                elements.home.status.textContent = `Status: ${statusLabel}`;
            }
            if (elements.home.source) {
                elements.home.source.textContent = `Source: ${formatSource(data.source)}`;
            }
            if (elements.home.art) {
                setArt(elements.home.art, data.art);
            }
        }
        if (elements.music) {
            if (elements.music.title) {
                elements.music.title.textContent = data.title || "No track";
            }
            if (elements.music.artist) {
                elements.music.artist.textContent = data.artist || "--";
            }
            if (elements.music.album) {
                elements.music.album.textContent = data.album || "--";
            }
            if (elements.music.progress) {
                elements.music.progress.textContent = progress;
            }
            if (elements.music.status) {
                elements.music.status.textContent = `Status: ${statusLabel}`;
            }
            if (elements.music.art) {
                setArt(elements.music.art, data.art);
            }
        }
        if (elements.mediaPlay) {
            elements.mediaPlay.textContent = statusLabel === "playing" ? "⏸" : "⏯";
        }
    }

    function updateSettings(data) {
        if (!data) {
            return;
        }
        if (!state.snapshots.settings) {
            state.snapshots.settings = {};
        }
        if (!elements.settings) {
            elements.settings = collectSettingsRefs();
        }
        const refs = elements.settings || {};
        Object.entries(data).forEach(([key, value]) => {
            state.snapshots.settings[key] = value;
            let el = refs[key];
            if (!el) {
                el = document.getElementById(`settings-${key}`);
            }
            if (!el) {
                if (key === "volume" && elements.volumeSlider) {
                    elements.volumeSlider.value = Number(value) || 0;
                }
                return;
            }

            if (el.getAttribute("role") === "switch") {
                setSwitchState(el, !!value, key);
                return;
            }

            if (el.tagName === "SELECT") {
                const stringValue = value === null || value === undefined ? "" : String(value);
                const options = Array.from(el.options);
                if (options.length && !options.some((opt) => opt.value === stringValue)) {
                    // leave as-is if value not present
                } else {
                    el.value = stringValue;
                }
                return;
            }

            if (el.tagName === "INPUT") {
                if (el.type === "range") {
                    el.value = Number(value) || 0;
                } else {
                    el.value = value === null || value === undefined ? "" : String(value);
                }
                return;
            }

            el.textContent = value === null || value === undefined || value === ""
                ? "—"
                : value;
        });
    }

    function bindEventOnce(element, type, handler, key) {
        if (!element) {
            return;
        }
        const datasetKey = key || `bound${type.toUpperCase()}`;
        if (element.dataset && element.dataset[datasetKey]) {
            return;
        }
        element.addEventListener(type, handler);
        if (element.dataset) {
            element.dataset[datasetKey] = "true";
        }
    }

    function setupControls() {
        if (elements.volumeSlider) {
            bindEventOnce(elements.volumeSlider, "input", (event) => {
                emit("set_volume", { value: Number(event.target.value) });
            }, "boundVolume");
        }

        if (elements.volumeMute) {
            bindEventOnce(elements.volumeMute, "click", () => emit("toggle_mute", {}), "boundMute");
        }

        if (elements.mediaPrev) {
            bindEventOnce(
                elements.mediaPrev,
                "click",
                () => emit("media_control", { action: "previous" }),
                "boundPrev"
            );
        }
        if (elements.mediaPlay) {
            bindEventOnce(
                elements.mediaPlay,
                "click",
                () => emit("media_control", { action: "play_pause" }),
                "boundPlay"
            );
        }
        if (elements.mediaNext) {
            bindEventOnce(
                elements.mediaNext,
                "click",
                () => emit("media_control", { action: "next" }),
                "boundNext"
            );
        }

        if (elements.btnBluetooth) {
            bindEventOnce(
                elements.btnBluetooth,
                "click",
                () => emit("open_dialog", { target: "bluetooth" }),
                "boundBluetooth"
            );
        }
        if (elements.btnWifi) {
            bindEventOnce(
                elements.btnWifi,
                "click",
                () => emit("open_dialog", { target: "wifi" }),
                "boundWifi"
            );
        }
        if (elements.btnRestartApp) {
            bindEventOnce(
                elements.btnRestartApp,
                "click",
                () => emit("system_action", { action: "restart_app" }),
                "boundRestartApp"
            );
        }
        if (elements.btnReboot) {
            bindEventOnce(
                elements.btnReboot,
                "click",
                () => emit("system_action", { action: "reboot" }),
                "boundReboot"
            );
        }
        if (elements.btnQuit) {
            bindEventOnce(
                elements.btnQuit,
                "click",
                () => emit("system_action", { action: "quit" }),
                "boundQuit"
            );
        }

        if (elements.applySettings) {
            bindEventOnce(
                elements.applySettings,
                "click",
                (event) => {
                    event.preventDefault();
                    emit("apply_settings", buildSettingsPayload());
                },
                "boundApplySettings"
            );
        }

        document.querySelectorAll("[data-system-action]").forEach((button) => {
            bindEventOnce(
                button,
                "click",
                (event) => {
                    event.preventDefault();
                    if (button.dataset.applySettings === "true") {
                        emit("apply_settings", buildSettingsPayload());
                    }
                    emit("system_action", { action: button.dataset.systemAction });
                },
                `boundSystemAction${button.dataset.systemAction || ""}`
            );
        });

        document.querySelectorAll("[data-open-dialog]").forEach((button) => {
            bindEventOnce(
                button,
                "click",
                (event) => { event.preventDefault(); emit("open_dialog", { target: button.dataset.openDialog }); },
                `boundOpenDialog${button.dataset.openDialog || ""}`
            );
        });

        document.querySelectorAll("[data-navigate]").forEach((button) => {
            bindEventOnce(
                button,
                "click",
                (event) => { event.preventDefault(); triggerNavigation(button.dataset.navigate); },
                `boundNavigate${button.dataset.navigate || ""}`
            );
        });
    }

    const handlers = {
        init(payload) {
            if (!payload) {
                return;
            }
            state.screens = payload.screens || [];
            updateNav(state.screens, payload.active);
            if (payload.theme && elements.app) {
                elements.app.dataset.theme = payload.theme;
            }
            if (payload.volume) {
                updateVolume(payload.volume);
            }
            if (payload.bluetooth) {
                updateBluetooth(payload.bluetooth);
            }
            if (payload.radio) {
                state.snapshots.radio = cloneSnapshot(payload.radio);
                updateStatusElement(elements.radioStatus, payload.radio.status);
            }
            if (payload.obd) {
                state.snapshots.obd = cloneSnapshot(payload.obd);
                updateStatusElement(elements.obdStatus, payload.obd.status);
            }
            if (payload.media) {
                updateMedia(payload.media);
            }
            if (payload.settings) {
                updateSettings(payload.settings);
            }
        },
        navigation(payload) {
            if (payload && payload.screen) {
                setActiveScreen(payload.screen);
            }
        },
        clock(payload) {
            if (payload && payload.value) {
                if (elements.clock) {
                    elements.clock.textContent = payload.value;
                }
                const settingsClock = document.getElementById("settings-clock");
                if (settingsClock) {
                    settingsClock.textContent = payload.value;
                }
            }
        },
        volume: updateVolume,
        bluetooth_status: updateBluetooth,
        radio_status(payload) {
            if (payload) {
                state.snapshots.radio = cloneSnapshot(payload);
                updateStatusElement(elements.radioStatus, payload.status);
            }
        },
        obd_status(payload) {
            if (payload) {
                state.snapshots.obd = cloneSnapshot(payload);
                updateStatusElement(elements.obdStatus, payload.status);
            }
        },
        media: updateMedia,
        settings: updateSettings,
    };

    window.__pyBridgeDispatch = function dispatchFromPython(name, payload) {
        if (handlers[name]) {
            handlers[name](payload || {});
        } else {
            console.debug("[HTML] Unhandled event from Python:", name, payload);
        }
    };

    const partialPromise = loadPartials();

    new QWebChannel(qt.webChannelTransport, (channel) => {
        window.bridge = channel.objects.bridge;
        setupControls();
        partialPromise.finally(() => emit("ready", {}));
    });
})();
