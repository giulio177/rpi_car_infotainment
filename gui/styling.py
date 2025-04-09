# gui/styling.py

# --- Helper function to calculate scaled int ---
def scale_value(base_value, scale_factor):
    """Calculates scaled integer value, ensuring minimum of 1."""
    # Ensure base_value is treated as a number before scaling
    try:
        numeric_base = float(base_value)
        return max(1, int(numeric_base * scale_factor))
    except (ValueError, TypeError):
        print(f"Warning: Could not convert base_value '{base_value}' to number in scale_value. Returning 1.")
        return 1 # Fallback value


# --- Theme Functions accepting scale_factor ---

def get_light_theme(scale_factor=1.0):
    # --- Define base sizes relative to 1920x1080 design ---
    # Adjust these base values to fine-tune the look at the reference resolution
    base_font_size_pt = 14 # Slightly larger base font for 1080p
    base_padding_px = 12
    base_button_min_height_px = 45
    base_border_radius_px = 6
    base_border_px = 1 # Use 1 or 2 for base border

    # --- Calculate scaled sizes ---
    scaled_font_size = scale_value(base_font_size_pt, scale_factor)
    scaled_padding = scale_value(base_padding_px, scale_factor)
    scaled_button_min_height = scale_value(base_button_min_height_px, scale_factor)
    scaled_border_radius = scale_value(base_border_radius_px, scale_factor)
    scaled_border = scale_value(base_border_px, scale_factor)

    # --- Generate QSS String ---
    return f"""
    /* ==================== Global Styles ==================== */
    QWidget {{
        color: #333333;
        font-size: {scaled_font_size}pt;
        /* background-color: transparent; Avoid setting global background here */
    }}
    QMainWindow, QStackedWidget {{
         background-color: #f0f0f0; /* Background for main areas */
    }}
    QWidget#central_widget, QWidget#settingsScrollContent {{
         background-color: #f0f0f0; /* Specific backgrounds */
    }}

    /* ==================== Bottom Bar ==================== */
    QWidget#persistentBottomBar {{
        background-color: #e0e0e0;
        border-top: {scaled_border}px solid #b0b0b0;
    }}
    /* Status labels in bottom bar */
    QLabel#statusBarObdLabel, QLabel#statusBarRadioLabel,
    QLabel#statusBarBtNameLabel, QLabel#statusBarBtBatteryLabel {{
         font-size: {scale_value(10, scale_factor)}pt; /* Slightly larger status */
         padding: {scale_value(3, scale_factor)}px;
         /* Color set dynamically */
    }}
    QLabel#statusBarBtBatteryLabel {{
         padding-left: {scale_value(4, scale_factor)}px;
         font-weight: bold;
    }}
    QLabel#statusBarSeparator {{
         font-size: {scale_value(10, scale_factor)}pt;
         color: #888888;
         padding-left: {scaled_padding // 2}px;
         padding-right: {scaled_padding // 2}px;
    }}

    /* ==================== General Widgets ==================== */
    QPushButton {{
        background-color: #dcdcdc;
        border: {scaled_border}px solid #b0b0b0;
        padding: {scaled_padding // 2}px {scaled_padding}px;
        border-radius: {scaled_border_radius}px;
        min-height: {scaled_button_min_height}px;
    }}
    QPushButton:pressed {{
        background-color: #c0c0c0;
    }}
    QPushButton:disabled {{ /* Style for disabled buttons */
        background-color: #e8e8e8;
        color: #a0a0a0;
        border-color: #c0c0c0;
    }}

    QLabel {{
        padding: {scaled_padding // 4}px; /* Default smaller padding for labels */
        background-color: transparent;
    }}

    QLineEdit, QComboBox {{
        background-color: #ffffff;
        border: {scaled_border}px solid #b0b0b0;
        padding: {scaled_padding // 2}px;
        border-radius: {scaled_border_radius // 2}px;
        min-height: {scale_value(base_button_min_height_px * 0.85, scale_factor)}px; /* Relative min height */
    }}

    QSlider::groove:horizontal {{
        border: {scaled_border}px solid #bbb;
        background: #ffffff;
        height: {scale_value(10, scale_factor)}px; /* Scaled slider groove */
        border-radius: {scaled_border_radius // 2}px;
    }}
    QSlider::handle:horizontal {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6e6efa, stop:1 #4040fa); /* Gradient handle */
        border: {scaled_border}px solid #3030cc;
        width: {scale_value(22, scale_factor)}px; /* Scaled handle width */
        margin: -{scale_value(7, scale_factor)}px 0; /* Adjust vertical margin based on handle/groove size */
        border-radius: {scale_value(base_border_radius_px * 0.8, scale_factor)}px; /* Slightly less radius for handle */
    }}
    QSlider::handle:horizontal:hover {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8e8efa, stop:1 #6060fa);
    }}

    QProgressBar {{
        border: {scaled_border}px solid grey;
        border-radius: {scaled_border_radius // 2}px;
        background-color: #e0e0e0;
        text-align: center;
        height: {scale_value(18, scale_factor)}px; /* Scale progress bar height */
    }}
    QProgressBar::chunk {{
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #15c8dc, stop:1 #05b8cc); /* Gradient chunk */
        /* width: {scale_value(10, scale_factor)}px; Not needed when using gradient */
        margin: {scale_value(2, scale_factor)}px;
        border-radius: {scale_value(base_border_radius_px // 3, scale_factor)}px; /* Use _px */
    }}

    QGroupBox {{
        font-size: {scale_value(base_font_size_pt + 1, scale_factor)}pt;
        border: {scaled_border}px solid gray;
        border-radius: {scaled_border_radius}px;
        margin-top: {scale_value(12, scale_factor)}px; /* Space for title */
        background-color: #e8e8e8;
        padding: {scaled_padding // 1.5}px; /* Padding inside group box */
        padding-top: {scale_value(base_padding_px * 1.5, scale_factor)}px; /* More top padding inside for title */
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 {scaled_padding // 2}px;
        left: {scaled_padding}px;
        top: -{scaled_padding // 3}px;
    }}

    QScrollArea#settingsScrollArea {{
        border: none;
        background-color: transparent;
    }}
    QScrollBar:vertical {{
        border: {scaled_border}px solid #c0c0c0;
        background: #e0e0e0;
        width: {scale_value(14, scale_factor)}px; /* Slightly wider scrollbar */
        margin: 0px 0px 0px 0px;
    }}
    QScrollBar::handle:vertical {{
        background: #a0a0a0;
        min-height: {scale_value(30, scale_factor)}px;
        border-radius: {scale_value(6, scale_factor)}px; /* Match width/2 */
    }}
     QScrollBar::handle:vertical:hover {{
        background: #909090;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        border: none; background: none; height: 0px;
    }}

    /* ==================== ComboBox Dropdown ==================== */
    QComboBox QAbstractItemView {{
        background-color: #ffffff;
        color: #333333;
        border: {scaled_border}px solid #b0b0b0;
        selection-background-color: #dcdcdc;
        selection-color: #333333;
        padding: {scaled_padding // 3}px;
        outline: 0px; /* Remove focus outline */
    }}
     QComboBox QAbstractItemView::item {{
         min-height: {scale_value(base_button_min_height_px * 0.75, scale_factor)}px; /* Ensure items are tall enough */
         padding: {scaled_padding // 4}px {scaled_padding // 2}px; /* Item padding */
     }}
     QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: {scale_value(25, scale_factor)}px; /* Scaled width */
        border-left-width: {scaled_border}px;
        border-left-color: #b0b0b0;
        border-left-style: solid;
        border-top-right-radius: {scaled_border_radius // 2}px;
        border-bottom-right-radius: {scaled_border_radius // 2}px;
        background-color: #dcdcdc;
    }}
    QComboBox::down-arrow {{
         image: url(assets/icons/down_arrow_light.png); /* PROVIDE A LIGHT ARROW ICON */
         width: {scale_value(12, scale_factor)}px; /* Scale arrow icon */
         height: {scale_value(12, scale_factor)}px;
    }}
     QComboBox::down-arrow:on {{
        /* top: 1px; left: 1px; */ /* Optional press effect */
     }}

    /* ==================== Screen Specific Styles ==================== */

    /* --- Header --- */
    QLabel#headerTitle {{
        font-size: {scale_value(18, scale_factor)}pt;
        font-weight: bold;
        padding-right: {scaled_padding // 2}px;
    }}
     QLabel#headerClock {{
        font-size: {scale_value(18, scale_factor)}pt;
        padding-left: {scaled_padding // 2}px;
    }}
    
     /* ==================== Header Bar Styles ==================== */
    QLabel#headerTitle {{
        font-size: {scale_value(18, scale_factor)}pt;
        font-weight: bold;
        padding-right: {scaled_padding}px; /* More space after title */
    }}
     QLabel#headerClock {{
        font-size: {scale_value(18, scale_factor)}pt;
        padding-left: {scaled_padding // 2}px;
    }}
     /* Combined BT Status Label in Header */
     QLabel#headerBtStatus {{
         font-size: {scale_value(12, scale_factor)}pt; /* Consistent size */
         font-weight: bold;
         color: #0060c0; /* Adjusted blue */
         padding-left: {scaled_padding}px; /* Space before BT status */
         padding-right: {scaled_padding // 2}px; /* Space between BT and Clock */
     }}

    /* --- Home Screen Media --- */
    QLabel#albumArtLabel {{ /* Targets ScrollingLabel */
        border: {scale_value(2, scale_factor)}px solid #a0a0a0;
        background-color: rgba(200, 200, 200, 0.15); /* Slightly more visible bg */
        border-radius: {scaled_border_radius}px;
        font-size: {scale_value(base_font_size_pt, scale_factor)}pt;
        color: #555555;
        min-height: {scale_value(140, scale_factor)}px;
        qproperty-alignment: 'AlignCenter';
        margin-bottom: {scaled_padding // 2}px;
        padding: {scaled_padding}px;
    }}
    QLabel#trackTitleLabel {{ /* Targets ScrollingLabel */
        min-height: {scale_value(28, scale_factor)}px;
        font-size: {scale_value(base_font_size_pt + 3, scale_factor)}pt; /* Larger Title */
        font-weight: bold;
    }}
     QLabel#trackArtistLabel {{ /* Targets ScrollingLabel */
        min-height: {scale_value(28, scale_factor)}px;
        font-size: {scale_value(base_font_size_pt + 1, scale_factor)}pt; /* Slightly larger Artist */
     }}
     QLabel#trackTimeLabel {{
        min-height: {scale_value(22, scale_factor)}px;
        font-size: {scale_value(base_font_size_pt - 1, scale_factor)}pt;
        color: #666666;
        qproperty-alignment: 'AlignCenter';
        margin-top: {scaled_padding // 3}px;
        margin-bottom: {scaled_padding // 2}px;
     }}
     QPushButton#mediaPrevButton, QPushButton#mediaPlayPauseButton, QPushButton#mediaNextButton {{
        min-width: {scale_value(60, scale_factor)}px; /* Wider media buttons */
        padding: {scaled_padding // 2}px; /* Adjust padding */
     }}
     QPushButton#mediaPlayPauseButton {{
         font-size: {scale_value(base_font_size_pt + 6, scale_factor)}pt; /* Bigger symbol */
         min-width: {scale_value(70, scale_factor)}px;
     }}

    /* --- OBD Screen --- */
     QLabel#speed_value, QLabel#rpm_value, QLabel#coolant_value, QLabel#fuel_value {{
         font-size: {scale_value(24, scale_factor)}pt; /* Larger OBD values */
         font-weight: bold;
         color: #007bff;
         padding-left: {scaled_padding // 2}px;
     }}

    /* --- Radio Screen --- */
     QLabel#freq_display {{
         font-size: {scale_value(40, scale_factor)}pt; /* Larger Freq display */
         font-weight: bold;
         color: #17a2b8;
         qproperty-alignment: 'AlignCenter';
         margin-top: {scaled_padding}px;
         margin-bottom: {scaled_padding // 2}px;
     }}
     QLabel#radioStatusLabel {{ /* Status below frequency */
         font-size: {scale_value(base_font_size_pt - 1, scale_factor)}pt;
         color: #555555;
         qproperty-alignment: 'AlignCenter';
     }}
     QPushButton#presetButton1, QPushButton#presetButton2, /* etc. */ {{
         /* Add preset button styles if needed */
     }}

    /* --- Settings Screen --- */
     QPushButton#settingsSaveButton, QPushButton#settingsRestartButton {{
        padding: {scale_value(base_padding_px * 0.8, scale_factor)}px {scale_value(base_padding_px * 1.8, scale_factor)}px; /* Adjust apply button padding */
        min-width: {scale_value(180, scale_factor)}px; /* Wider apply buttons */
        font-size: {scale_value(base_font_size_pt + 1, scale_factor)}pt;
        margin-top: {scaled_padding // 2}px; /* Space above buttons */
        margin-bottom: {scaled_padding // 2}px; /* Space below buttons */
     }}
      QLabel#resolutionNoteLabel {{
         font-size: {scale_value(base_font_size_pt - 3, scale_factor)}pt; /* Smaller note */
         color: #666666;
         padding-left: {scaled_padding // 2}px;
     }}

    /* --- Special Buttons --- */
    QPushButton#powerNavButton {{ /* Bottom bar power */
        background-color: #ff8080;
        border-color: #cc6666;
    }}
     QPushButton#powerNavButton:pressed {{
        background-color: #e67373;
     }}
     QPushButton#restartNavButton {{ /* Bottom bar restart */
         /* Add distinct style if desired */
     }}
    """

def get_dark_theme(scale_factor=1.0):
    # --- Define base sizes relative to 1920x1080 design ---
    base_font_size_pt = 14
    base_padding_px = 12
    base_button_min_height_px = 45
    base_border_radius_px = 6
    base_border_px = 1

    # --- Calculate scaled sizes ---
    scaled_font_size = scale_value(base_font_size_pt, scale_factor)
    scaled_padding = scale_value(base_padding_px, scale_factor)
    scaled_button_min_height = scale_value(base_button_min_height_px, scale_factor)
    scaled_border_radius = scale_value(base_border_radius_px, scale_factor)
    scaled_border = scale_value(base_border_px, scale_factor)

    # --- Generate QSS String ---
    return f"""
    /* ==================== Global Styles ==================== */
    QWidget {{
        color: #e0e0e0;
        font-size: {scaled_font_size}pt;
    }}
    QMainWindow, QStackedWidget {{ background-color: #2e2e2e; }}
    QWidget#central_widget, QWidget#settingsScrollContent {{ background-color: #2e2e2e; }}

    /* ==================== Bottom Bar ==================== */
    QWidget#persistentBottomBar {{
        background-color: #3a3a3a;
        border-top: {scaled_border}px solid #505050;
    }}
    QLabel#statusBarObdLabel, QLabel#statusBarRadioLabel,
    QLabel#statusBarBtNameLabel, QLabel#statusBarBtBatteryLabel {{
         font-size: {scale_value(10, scale_factor)}pt;
         padding: {scale_value(3, scale_factor)}px;
    }}
    QLabel#statusBarBtBatteryLabel {{
         padding-left: {scale_value(4, scale_factor)}px;
         font-weight: bold;
    }}
    QLabel#statusBarSeparator {{
         font-size: {scale_value(10, scale_factor)}pt;
         color: #888888;
         padding-left: {scaled_padding // 2}px;
         padding-right: {scaled_padding // 2}px;
    }}

    /* ==================== General Widgets ==================== */
    QPushButton {{
        background-color: #505050;
        border: {scaled_border}px solid #707070;
        color: #e0e0e0;
        padding: {scaled_padding // 2}px {scaled_padding}px;
        border-radius: {scaled_border_radius}px;
        min-height: {scaled_button_min_height}px;
    }}
    QPushButton:pressed {{
        background-color: #606060;
    }}
    QPushButton:disabled {{
        background-color: #404040;
        color: #808080;
        border-color: #555555;
    }}

    QLabel {{
        padding: {scaled_padding // 4}px;
        background-color: transparent;
    }}

    QLineEdit, QComboBox {{
        background-color: #404040;
        border: {scaled_border}px solid #707070;
        color: #e0e0e0;
        padding: {scaled_padding // 2}px;
        border-radius: {scaled_border_radius // 2}px;
        min-height: {scale_value(base_button_min_height_px * 0.85, scale_factor)}px;
    }}

    QSlider::groove:horizontal {{
        border: {scaled_border}px solid #666;
        background: #555555;
        height: {scale_value(10, scale_factor)}px;
        border-radius: {scaled_border_radius // 2}px;
    }}
    QSlider::handle:horizontal {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #9090ff, stop:1 #7070f0); /* Lighter Gradient handle */
        border: {scaled_border}px solid #5050dd;
        width: {scale_value(22, scale_factor)}px;
        margin: -{scale_value(7, scale_factor)}px 0;
        border-radius: {scale_value(base_border_radius_px * 0.8, scale_factor)}px;
    }}
     QSlider::handle:horizontal:hover {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #a0a0ff, stop:1 #8080f0);
    }}

     QProgressBar {{
        border: {scaled_border}px solid #555555;
        border-radius: {scaled_border_radius // 2}px;
        background-color: #444444;
        text-align: center;
        height: {scale_value(18, scale_factor)}px;
    }}
    QProgressBar::chunk {{
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2dc8dd, stop:1 #1db8cc); /* Gradient chunk */
        margin: {scale_value(2, scale_factor)}px;
        border-radius: {scale_value(base_border_radius_px // 3, scale_factor)}px; /* Use _px */
    }}
     QGroupBox {{
        font-size: {scale_value(base_font_size_pt + 1, scale_factor)}pt;
        border: {scaled_border}px solid #666666;
        border-radius: {scaled_border_radius}px;
        margin-top: {scale_value(12, scale_factor)}px;
        background-color: #383838;
        padding: {scaled_padding // 1.5}px;
        padding-top: {scale_value(base_padding_px * 1.5, scale_factor)}px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 {scaled_padding // 2}px;
        left: {scaled_padding}px;
        top: -{scaled_padding // 3}px;
        color: #cccccc; /* Lighter title text */
    }}

    QScrollArea#settingsScrollArea {{
        border: none;
        background-color: transparent;
    }}
    QScrollBar:vertical {{
        border: {scaled_border}px solid #505050;
        background: #3a3a3a;
        width: {scale_value(14, scale_factor)}px;
        margin: 0px 0px 0px 0px;
    }}
    QScrollBar::handle:vertical {{
        background: #686868;
        min-height: {scale_value(30, scale_factor)}px;
        border-radius: {scale_value(6, scale_factor)}px;
    }}
     QScrollBar::handle:vertical:hover {{
        background: #787878;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        border: none; background: none; height: 0px;
    }}

    /* ==================== ComboBox Dropdown ==================== */
    QComboBox {{
        selection-background-color: #6060a0; /* Selection inside the box */
    }}
    QComboBox QAbstractItemView {{
        background-color: #3a3a3a;
        color: #e0e0e0;
        border: {scaled_border}px solid #707070;
        selection-background-color: #5050a0;
        selection-color: #ffffff;
        padding: {scaled_padding // 3}px;
        outline: 0px;
    }}
     QComboBox QAbstractItemView::item {{
         min-height: {scale_value(base_button_min_height_px * 0.75, scale_factor)}px;
         padding: {scaled_padding // 4}px {scaled_padding // 2}px;
     }}
     QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: {scale_value(25, scale_factor)}px;
        border-left-width: {scaled_border}px;
        border-left-color: #707070;
        border-left-style: solid;
        border-top-right-radius: {scaled_border_radius // 2}px;
        border-bottom-right-radius: {scaled_border_radius // 2}px;
        background-color: #555555;
    }}
    QComboBox::down-arrow {{
         image: url(assets/icons/down_arrow_dark.png); /* PROVIDE A DARK ARROW ICON */
         width: {scale_value(12, scale_factor)}px;
         height: {scale_value(12, scale_factor)}px;
    }}
     QComboBox::down-arrow:on {{
        /* top: 1px; left: 1px; */
     }}

    /* ==================== Screen Specific Styles ==================== */

    /* --- Header --- */
    QLabel#headerTitle {{
        font-size: {scale_value(18, scale_factor)}pt;
        font-weight: bold;
        padding-right: {scaled_padding // 2}px;
    }}
     QLabel#headerClock {{
        font-size: {scale_value(18, scale_factor)}pt;
        padding-left: {scaled_padding // 2}px;
     }}

     /* ==================== Header Bar Styles ==================== */
    QLabel#headerTitle {{
        font-size: {scale_value(18, scale_factor)}pt;
        font-weight: bold;
        padding-right: {scaled_padding}px;
    }}
     QLabel#headerClock {{
        font-size: {scale_value(18, scale_factor)}pt;
        padding-left: {scaled_padding // 2}px;
    }}
     /* Combined BT Status Label in Header */
     QLabel#headerBtStatus {{
         font-size: {scale_value(12, scale_factor)}pt;
         font-weight: bold;
         color: #50a0ff; /* Adjusted light blue */
         padding-left: {scaled_padding}px;
         padding-right: {scaled_padding // 2}px;
     }}

    /* --- Home Screen Media --- */
    QLabel#albumArtLabel {{ /* Targets ScrollingLabel */
        border: {scale_value(2, scale_factor)}px solid #505050; /* Dark theme border */
        background-color: rgba(80, 80, 80, 0.2); /* Dark theme subtle background */
        border-radius: {scaled_border_radius}px;
        font-size: {scale_value(base_font_size_pt, scale_factor)}pt;
        color: #bbbbbb; /* Dark Theme Dim Text */
        min-height: {scale_value(140, scale_factor)}px;
        qproperty-alignment: 'AlignCenter';
        margin-bottom: {scaled_padding // 2}px;
        padding: {scaled_padding}px;
    }}
    QLabel#trackTitleLabel {{ /* Targets ScrollingLabel */
        min-height: {scale_value(28, scale_factor)}px;
        font-size: {scale_value(base_font_size_pt + 3, scale_factor)}pt;
        font-weight: bold;
    }}
     QLabel#trackArtistLabel {{ /* Targets ScrollingLabel */
        min-height: {scale_value(28, scale_factor)}px;
        font-size: {scale_value(base_font_size_pt + 1, scale_factor)}pt;
     }}
     QLabel#trackTimeLabel {{
        min-height: {scale_value(22, scale_factor)}px;
        font-size: {scale_value(base_font_size_pt - 1, scale_factor)}pt;
        color: #aaaaaa; /* Dark Theme Dim */
        qproperty-alignment: 'AlignCenter';
        margin-top: {scaled_padding // 3}px;
        margin-bottom: {scaled_padding // 2}px;
     }}
     QPushButton#mediaPrevButton, QPushButton#mediaPlayPauseButton, QPushButton#mediaNextButton {{
        min-width: {scale_value(60, scale_factor)}px;
        padding: {scaled_padding // 2}px;
     }}
     QPushButton#mediaPlayPauseButton {{
         font-size: {scale_value(base_font_size_pt + 6, scale_factor)}pt;
         min-width: {scale_value(70, scale_factor)}px;
     }}

    /* --- OBD Screen --- */
     QLabel#speed_value, QLabel#rpm_value, QLabel#coolant_value, QLabel#fuel_value {{
         font-size: {scale_value(24, scale_factor)}pt;
         font-weight: bold;
         color: #34a4ff;
         padding-left: {scaled_padding // 2}px;
     }}

    /* --- Radio Screen --- */
     QLabel#freq_display {{
         font-size: {scale_value(40, scale_factor)}pt;
         font-weight: bold;
         color: #20c9d6;
         qproperty-alignment: 'AlignCenter';
         margin-top: {scaled_padding}px;
         margin-bottom: {scaled_padding // 2}px;
     }}
     QLabel#radioStatusLabel {{
         font-size: {scale_value(base_font_size_pt - 1, scale_factor)}pt;
         color: #aaaaaa;
         qproperty-alignment: 'AlignCenter';
     }}

    /* --- Settings Screen --- */
     QPushButton#settingsSaveButton, QPushButton#settingsRestartButton {{
        padding: {scale_value(base_padding_px * 0.8, scale_factor)}px {scale_value(base_padding_px * 1.8, scale_factor)}px;
        min-width: {scale_value(180, scale_factor)}px;
        font-size: {scale_value(base_font_size_pt + 1, scale_factor)}pt;
        margin-top: {scaled_padding // 2}px;
        margin-bottom: {scaled_padding // 2}px;
     }}
      QLabel#resolutionNoteLabel {{
         font-size: {scale_value(base_font_size_pt - 3, scale_factor)}pt;
         color: #aaaaaa;
         padding-left: {scaled_padding // 2}px;
     }}

    /* --- Special Buttons --- */
    QPushButton#powerNavButton {{
        background-color: #a04040;
        border-color: #803333;
    }}
     QPushButton#powerNavButton:pressed {{
        background-color: #b35959;
     }}
    """

# --- apply_theme function ---
def apply_theme(app, theme_name, scale_factor=1.0):
    """Applies the selected theme stylesheet with the given scale factor."""
    if theme_name == "dark":
        style_sheet = get_dark_theme(scale_factor)
    else: # Default to light
        style_sheet = get_light_theme(scale_factor)

    # Debug: Print the generated stylesheet to check syntax
    # print("--- Applying Stylesheet ---")
    # print(style_sheet)
    # print("--------------------------")
    app.setStyleSheet(style_sheet)
