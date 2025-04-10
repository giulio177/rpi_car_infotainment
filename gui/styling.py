# gui/styling.py

import math

# --- Helper function to calculate scaled int ---
def scale_value(base_value, scale_factor):
    """Calculates scaled integer value, ensuring minimum of 1."""
    try:
        numeric_base = float(base_value)
        return max(1, int(numeric_base * scale_factor))
    except (ValueError, TypeError):
        print(f"Warning: Could not convert base_value '{base_value}' to number in scale_value. Returning 1.")
        return 1

BASE_SLIDER_THICKNESS = 25 # <<< --- TWEAK THIS SINGLE VALUE --- >>>

# --- Theme Functions accepting scale_factor ---

def get_light_theme(scale_factor=1.0):
    # Base sizes relative to 1920x1080
    base_font_size_pt = 14
    base_padding_px = 12
    base_album_art_size_px = 160 # Base size for square side (adjust as needed for 1080p)
    base_button_min_height_px = 45 # Base for normal buttons
    base_border_radius_px = 6
    base_border_px = 1

    # Calculate scaled sizes
    scaled_font_size = scale_value(base_font_size_pt, scale_factor)
    scaled_padding = scale_value(base_padding_px, scale_factor)
    scaled_album_art_size = scale_value(base_album_art_size_px, scale_factor) # Scaled square size
    scaled_button_min_height = scale_value(base_button_min_height_px, scale_factor)
    scaled_border_radius = scale_value(base_border_radius_px, scale_factor)
    scaled_border = scale_value(base_border_px, scale_factor)
    # --- Calculate DERIVED slider sizes using the CONSTANT ---
    scaled_slider_thickness = scale_value(BASE_SLIDER_THICKNESS, scale_factor)
    # Make handle ~2x groove thickness, ensure it's an even number for centered radius
    scaled_slider_handle_s = max(scaled_slider_thickness + scale_value(10, scale_factor), scale_value(BASE_SLIDER_THICKNESS * 2.0, scale_factor))
    scaled_slider_handle_s = int(math.ceil(scaled_slider_handle_s / 2.0)) * 2 # Ensure even number
    scaled_slider_handle_margin = - (scaled_slider_handle_s - scaled_slider_thickness) // 2
    # Generate QSS String
    return f"""
    /* ==================== Global Styles ==================== */
    QWidget {{
        color: #333333;
        font-size: {scaled_font_size}pt;
    }}
    QMainWindow, QStackedWidget {{ background-color: #f0f0f0; }}
    QWidget#central_widget {{background-color: #f0f0f0;}}
    QWidget#settingsScrollContent {{ background-color: #f0f0f0; }}
    QCheckBox::indicator {{
        width: {scale_value(20, scale_factor)}px; /* Size of the checkbox */
        height: {scale_value(20, scale_factor)}px;
        border-radius: {scale_value(4, scale_factor)}px;
    }}
    /* Light Theme Checkbox */
    QCheckBox::indicator {{
        border: {scaled_border}px solid #888888;
        background-color: #f8f8f8;
    }}
    QCheckBox::indicator:checked {{
        background-color: #007bff; /* Blue when checked */
        border-color: #0056b3;
        image: url(assets/icons/checkmark_light.png); /* Provide checkmark icon */
    }}
    QCheckBox::indicator:disabled {{
         border-color: #c0c0c0;
         background-color: #e0e0e0;
    }}

    /* ==================== Bottom Bar ==================== */
    QWidget#persistentBottomBar {{
        background-color: #e0e0e0;
        border-top: {scaled_border}px solid #b0b0b0;
    }}
    /* Status labels in bottom bar */
    QLabel#statusBarObdLabel, QLabel#statusBarRadioLabel,
    QLabel#statusBarBtNameLabel, QLabel#statusBarBtBatteryLabel {{
         font-size: {scale_value(11, scale_factor)}pt; /* Adjusted base size */
         padding: {scale_value(4, scale_factor)}px; /* Adjusted base size */
    }}
    QLabel#statusBarBtBatteryLabel {{
         padding-left: {scale_value(5, scale_factor)}px; /* Adjusted base size */
         font-weight: bold;
    }}
    QLabel#statusBarSeparator {{
         font-size: {scale_value(11, scale_factor)}pt; /* Adjusted base size */
         color: #888888;
         padding-left: {scaled_padding // 2}px;
         padding-right: {scaled_padding // 2}px;
    }}

    /* ==================== General Widgets ==================== */
    QPushButton {{
        background-color: #dcdcdc;
        border: {scaled_border}px solid #b0b0b0;
        padding: {scale_value(base_padding_px * 0.6, scale_factor)}px {scale_value(base_padding_px * 1.2, scale_factor)}px; /* Adjusted padding */
        border-radius: {scaled_border_radius}px;
        min-height: {scaled_button_min_height}px;
    }}
    QPushButton:pressed {{ background-color: #c0c0c0; }}
    QPushButton:disabled {{ background-color: #e8e8e8; color: #a0a0a0; border-color: #c0c0c0; }}

    QLabel {{ padding: {scaled_padding // 4}px; background-color: transparent; }}

    QLineEdit, QComboBox {{
        background-color: #ffffff;
        border: {scaled_border}px solid #b0b0b0;
        padding: {scale_value(base_padding_px * 0.6, scale_factor)}px; /* Adjusted padding */
        border-radius: {scaled_border_radius // 2}px;
        min-height: {scale_value(base_button_min_height_px * 0.9, scale_factor)}px;
    }}

    /* --- QSlider Styling (Targeting #volumeSlider) --- */
    QSlider#volumeSlider::groove:horizontal {{
        border: {scaled_border}px solid #aaaaaa; background: #e8e8e8;
        height: {scaled_slider_thickness}px; /* Use derived scaled thickness */
        border-radius: {scaled_slider_thickness // 2}px;
        margin: 0px {scaled_slider_handle_s // 3}px;
    }}
    QSlider#volumeSlider::handle:horizontal {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #7070ff, stop:1 #4040fa);
        border: {scaled_border}px solid #3030cc;
        width: {scaled_slider_handle_s}px; /* Use derived scaled handle size */
        height: {scaled_slider_handle_s}px; /* Use derived scaled handle size */
        margin: {scaled_slider_handle_margin}px 0; /* Use derived calculated margin */
        border-radius: {scaled_slider_handle_s // 2}px; /* Make it circular */
    }}
    QSlider#volumeSlider::handle:horizontal:hover {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8e8efa, stop:1 #6060fa);
        border-color: #2020aa;
    }}
    QSlider#volumeSlider::handle:horizontal:pressed {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6060fa, stop:1 #3030e0);
        border-color: #101088;
    }}

    

    QProgressBar {{
        border: {scaled_border}px solid grey; border-radius: {scaled_border_radius // 2}px;
        background-color: #e0e0e0; text-align: center;
        height: {scale_value(18, scale_factor)}px;
    }}
    QProgressBar::chunk {{
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #15c8dc, stop:1 #05b8cc);
        margin: {scale_value(2, scale_factor)}px;
        border-radius: {scale_value(base_border_radius_px // 3, scale_factor)}px;
    }}

    QGroupBox {{
        font-size: {scale_value(base_font_size_pt + 1, scale_factor)}pt;
        border: {scaled_border}px solid gray; border-radius: {scaled_border_radius}px;
        margin-top: {scale_value(12, scale_factor)}px; background-color: #e8e8e8;
        padding: {scale_value(base_padding_px * 0.8, scale_factor)}px;
        padding-top: {scale_value(base_padding_px * 1.5, scale_factor)}px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin; subcontrol-position: top left;
        padding: 0 {scaled_padding // 2}px; left: {scaled_padding}px;
        top: -{scale_value(base_padding_px * 0.4, scale_factor)}px; /* Adjust title pos */
    }}

    QScrollArea#settingsScrollArea {{ border: none; background-color: transparent; }}
    QScrollBar:vertical {{
        border: {scaled_border}px solid #c0c0c0; background: #e0e0e0;
        width: {scale_value(14, scale_factor)}px; margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: #a0a0a0; min-height: {scale_value(30, scale_factor)}px;
        border-radius: {scale_value(6, scale_factor)}px;
    }}
    QScrollBar::handle:vertical:hover {{ background: #909090; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ border: none; background: none; height: 0px; }}

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
         font-size: {scale_value(13, scale_factor)}pt; /* Consistent size */
         font-weight: normal; /* Normal weight */
         color: #0060c0; /* Adjusted blue */
         padding-left: {scaled_padding}px; /* Space before BT status */
         padding-right: {scaled_padding}px; /* Space after BT status */
         /* Align vertically if needed, though layout should center */
         /* margin-top: ...; margin-bottom: ...; */
     }}

    /* --- ComboBox Dropdown --- */
    QComboBox QAbstractItemView {{
        background-color: #ffffff; color: #333333; border: {scaled_border}px solid #b0b0b0;
        selection-background-color: #dcdcdc; selection-color: #333333;
        padding: {scaled_padding // 3}px; outline: 0px;
    }}
    QComboBox QAbstractItemView::item {{
        min-height: {scale_value(base_button_min_height_px * 0.75, scale_factor)}px;
        padding: {scaled_padding // 4}px {scaled_padding // 2}px;
    }}
    QComboBox::drop-down {{
        subcontrol-origin: padding; subcontrol-position: top right;
        width: {scale_value(25, scale_factor)}px; border-left-width: {scaled_border}px;
        border-left-color: #b0b0b0; border-left-style: solid;
        border-top-right-radius: {scaled_border_radius // 2}px; border-bottom-right-radius: {scaled_border_radius // 2}px;
        background-color: #dcdcdc;
    }}
    QComboBox::down-arrow {{
        image: url(assets/icons/down_arrow_light.png);
        width: {scale_value(12, scale_factor)}px; height: {scale_value(12, scale_factor)}px;
    }}

    /* ==================== Screen Specific Styles ==================== */

    /* --- Home Screen Media --- */
    QLabel#albumArtLabel {{ /* Targets ScrollingLabel */
        border: {scale_value(2, scale_factor)}px solid #a0a0a0;
        background-color: rgba(200, 200, 200, 0.15);
        border-radius: {scaled_border_radius}px;
        font-size: {scale_value(base_font_size_pt, scale_factor)}pt; /* Slightly smaller album text */
        color: #555555;
        qproperty-alignment: 'AlignCenter';
        margin-bottom: {scaled_padding // 1.5}px; /* Adjusted margin */
        padding: {scaled_padding}px;
        /* --- Enforce Square Aspect Ratio --- */
        min-width: {scaled_album_art_size}px;
        max-width: {scaled_album_art_size}px;
        min-height: {scaled_album_art_size}px;
        max-height: {scaled_album_art_size}px;
        /* --- */
    }}
    QLabel#trackTitleLabel {{ /* Targets ScrollingLabel */
        min-height: {scale_value(35, scale_factor)}px; /* Ensure enough height */
        font-size: {scale_value(base_font_size_pt + 4, scale_factor)}pt;
        font-weight: bold;
        color: #222222; /* Explicit dark color for light theme */
        margin-bottom: {scaled_padding // 4}px; /* Small margin below title */
    }}
     QLabel#trackArtistLabel {{ /* Targets ScrollingLabel */
        min-height: {scale_value(30, scale_factor)}px;
        font-size: {scale_value(base_font_size_pt + 2, scale_factor)}pt;
        color: #444444; /* Explicit color */
        margin-bottom: {scaled_padding // 2}px; /* More margin below artist */
     }}
     QLabel#trackTimeLabel {{
        min-height: {scale_value(24, scale_factor)}px;
        font-size: {scale_value(base_font_size_pt, scale_factor)}pt;
        color: #666666;
        qproperty-alignment: 'AlignCenter';
        margin-top: {scaled_padding // 2}px; /* Increased margin above time */
        margin-bottom: {scaled_padding}px; /* Increased margin below time */
     }}
     QPushButton#mediaPrevButton, QPushButton#mediaPlayPauseButton, QPushButton#mediaNextButton {{
        min-width: {scale_value(65, scale_factor)}px;
        padding: {scale_value(base_padding_px * 0.7, scale_factor)}px;
     }}
     QPushButton#mediaPlayPauseButton {{
         font-size: {scale_value(base_font_size_pt + 8, scale_factor)}pt;
         min-width: {scale_value(75, scale_factor)}px;
     }}

    /* --- OBD Screen --- */
     QLabel#speed_value, QLabel#rpm_value, QLabel#coolant_value, QLabel#fuel_value {{
         font-size: {scale_value(26, scale_factor)}pt; /* Adjusted base size */
         font-weight: bold; color: #007bff; padding-left: {scaled_padding // 2}px;
     }}

    /* --- Radio Screen --- */
     QLabel#freq_display {{
         font-size: {scale_value(44, scale_factor)}pt; /* Adjusted base size */
         font-weight: bold; color: #17a2b8; qproperty-alignment: 'AlignCenter';
         margin-top: {scaled_padding}px; margin-bottom: {scaled_padding // 2}px;
     }}
     QLabel#radioStatusLabel {{
         font-size: {scale_value(base_font_size_pt, scale_factor)}pt; /* Adjusted base size */
         color: #555555; qproperty-alignment: 'AlignCenter';
     }}

    /* --- Settings Screen --- */
     QPushButton#settingsSaveButton, QPushButton#settingsRestartButton {{
        padding: {scale_value(base_padding_px * 0.9, scale_factor)}px {scale_value(base_padding_px * 2.0, scale_factor)}px;
        min-width: {scale_value(200, scale_factor)}px; /* Adjusted base size */
        font-size: {scale_value(base_font_size_pt + 2, scale_factor)}pt; /* Adjusted base size */
        margin-top: {scaled_padding // 2}px; margin-bottom: {scaled_padding // 2}px;
     }}

    /* --- Special Buttons --- */
    QPushButton#powerNavButton {{ background-color: #ff8080; border-color: #cc6666; }}
    QPushButton#powerNavButton:pressed {{ background-color: #e67373; }}
    """

def get_dark_theme(scale_factor=1.0):
    # Base sizes relative to 1920x1080
    base_font_size_pt = 14
    base_padding_px = 12
    base_album_art_size_px = 160 # Base size for square side (adjust as needed for 1080p)
    base_button_min_height_px = 45 # Base for normal buttons
    base_border_radius_px = 6
    base_border_px = 1
    
    # Calculate scaled sizes
    scaled_font_size = scale_value(base_font_size_pt, scale_factor)
    scaled_padding = scale_value(base_padding_px, scale_factor)
    scaled_album_art_size = scale_value(base_album_art_size_px, scale_factor) # Scaled square size
    scaled_button_min_height = scale_value(base_button_min_height_px, scale_factor)
    scaled_border_radius = scale_value(base_border_radius_px, scale_factor)
    scaled_border = scale_value(base_border_px, scale_factor)
    # --- Calculate DERIVED slider sizes using the CONSTANT ---
    scaled_slider_thickness = scale_value(BASE_SLIDER_THICKNESS, scale_factor)
    scaled_slider_handle_s = max(scaled_slider_thickness + scale_value(10, scale_factor), scale_value(BASE_SLIDER_THICKNESS * 2.0, scale_factor))
    scaled_slider_handle_s = int(math.ceil(scaled_slider_handle_s / 2.0)) * 2 # Ensure even
    scaled_slider_handle_margin = - (scaled_slider_handle_s - scaled_slider_thickness) // 2
    
    # Generate QSS String
    return f"""
    /* ==================== Global Styles ==================== */
    QWidget {{ 
        color: #e0e0e0;
        font-size: {scaled_font_size}pt; 
    }}
    QMainWindow, QStackedWidget {{ background-color: #2e2e2e; }}
    QWidget#central_widget{{ background-color: #2e2e2e; }}
    QWidget#settingsScrollContent {{ background-color: #2e2e2e; }}
    QCheckBox::indicator {{
        width: {scale_value(20, scale_factor)}px; /* Size of the checkbox */
        height: {scale_value(20, scale_factor)}px;
        border-radius: {scale_value(4, scale_factor)}px;
    }}
    /* Dark Theme Checkbox */
    QCheckBox::indicator {{
        border: {scaled_border}px solid #aaaaaa;
        background-color: #444444;
    }}
    QCheckBox::indicator:checked {{
        background-color: #34a4ff;
        border-color: #2080d0;
        image: url(assets/icons/checkmark_dark.png); /* Provide checkmark icon*/
    }}
    QCheckBox::indicator:disabled {{
         border-color: #606060;
         background-color: #505050;
    }}

    /* ==================== Bottom Bar ==================== */
    QWidget#persistentBottomBar {{
        background-color: #3a3a3a;
        border-top: {scaled_border}px solid #505050; 
    }}
    /* Status labels in bottom bar */
    QLabel#statusBarObdLabel, QLabel#statusBarRadioLabel,
    QLabel#statusBarBtNameLabel, QLabel#statusBarBtBatteryLabel {{
        font-size: {scale_value(11, scale_factor)}pt;
        padding: {scale_value(4, scale_factor)}px;
    }}
    QLabel#statusBarBtBatteryLabel {{
        padding-left: {scale_value(5, scale_factor)}px;
        font-weight: bold; 
    }}
    QLabel#statusBarSeparator {{
        font-size: {scale_value(11, scale_factor)}pt;
        color: #888888;
        padding-left: {scaled_padding // 2}px;
        padding-right: {scaled_padding // 2}px;
    }}

    /* ==================== General Widgets ==================== */
    QPushButton {{
        background-color: #505050; 
        border: {scaled_border}px solid #707070; color: #e0e0e0;
        padding: {scale_value(base_padding_px * 0.6, scale_factor)}px {scale_value(base_padding_px * 1.2, scale_factor)}px;
        border-radius: {scaled_border_radius}px; 
        min-height: {scaled_button_min_height}px;
    }}
    QPushButton:pressed {{ background-color: #606060; }}
    QPushButton:disabled {{ background-color: #404040; color: #808080; border-color: #555555; }}

    QLabel {{ padding: {scaled_padding // 4}px; background-color: transparent; }}

    QLineEdit, QComboBox {{
        background-color: #404040; 
        border: {scaled_border}px solid #707070; color: #e0e0e0;
        padding: {scale_value(base_padding_px * 0.6, scale_factor)}px; 
        border-radius: {scaled_border_radius // 2}px;
        min-height: {scale_value(base_button_min_height_px * 0.9, scale_factor)}px;
    }}

    /* --- QSlider Styling (Targeting #volumeSlider) --- */
    QSlider#volumeSlider::groove:horizontal {{
        border: {scaled_border}px solid #555555; background: #444444;
        height: {scaled_slider_thickness}px; /* Use derived scaled thickness */
        border-radius: {scaled_slider_thickness // 2}px;
        margin: 0px {scaled_slider_handle_s // 3}px;
    }}
    QSlider#volumeSlider::handle:horizontal {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8080ff, stop:1 #6060f0);
        border: {scaled_border}px solid #5050dd;
        width: {scaled_slider_handle_s}px; /* Use derived scaled handle size */
        height: {scaled_slider_handle_s}px; /* Use derived scaled handle size */
        margin: {scaled_slider_handle_margin}px 0; /* Use derived calculated margin */
        border-radius: {scaled_slider_handle_s // 2}px; /* Make it circular */
    }}
    QSlider#volumeSlider::handle:horizontal:hover {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #9090ff, stop:1 #7070f0);
        border-color: #4040cc;
    }}
    QSlider#volumeSlider::handle:horizontal:pressed {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #7070f0, stop:1 #5050d0);
        border-color: #3030aa;
    }}
    

     QProgressBar {{
        border: {scaled_border}px solid #555555; border-radius: {scaled_border_radius // 2}px;
        background-color: #444444; text-align: center; 
        height: {scale_value(18, scale_factor)}px;
    }}
    QProgressBar::chunk {{
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2dc8dd, stop:1 #1db8cc);
        margin: {scale_value(2, scale_factor)}px; 
        border-radius: {scale_value(base_border_radius_px // 3, scale_factor)}px;
    }}
     QGroupBox {{
        font-size: {scale_value(base_font_size_pt + 1, scale_factor)}pt;
        border: {scaled_border}px solid #666666; border-radius: {scaled_border_radius}px;
        margin-top: {scale_value(12, scale_factor)}px; background-color: #383838;
        padding: {scale_value(base_padding_px * 0.8, scale_factor)}px;
        padding-top: {scale_value(base_padding_px * 1.5, scale_factor)}px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin; subcontrol-position: top left;
        padding: 0 {scaled_padding // 2}px; left: {scaled_padding}px;
        top: -{scale_value(base_padding_px * 0.4, scale_factor)}px; color: #cccccc;
    }}

    QScrollArea#settingsScrollArea {{ border: none; background-color: transparent; }}
    QScrollBar:vertical {{
        border: {scaled_border}px solid #505050; background: #3a3a3a;
        width: {scale_value(14, scale_factor)}px; margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: #686868; min-height: {scale_value(30, scale_factor)}px;
        border-radius: {scale_value(6, scale_factor)}px;
    }}
    QScrollBar::handle:vertical:hover {{ background: #787878; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ border: none; background: none; height: 0px; }}

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
         font-size: {scale_value(13, scale_factor)}pt;
         font-weight: normal;
         color: #50a0ff; /* Adjusted light blue */
         padding-left: {scaled_padding}px;
         padding-right: {scaled_padding}px;
     }}

    /* --- ComboBox Dropdown --- */
    QComboBox {{ selection-background-color: #6060a0; }} /* Selection inside the box */
    QComboBox QAbstractItemView {{
        background-color: #3a3a3a; color: #e0e0e0; border: {scaled_border}px solid #707070;
        selection-background-color: #5050a0; selection-color: #ffffff;
        padding: {scaled_padding // 3}px; outline: 0px;
    }}
    QComboBox QAbstractItemView::item {{
        min-height: {scale_value(base_button_min_height_px * 0.75, scale_factor)}px;
        padding: {scaled_padding // 4}px {scaled_padding // 2}px;
    }}
    QComboBox::drop-down {{
        subcontrol-origin: padding; subcontrol-position: top right;
        width: {scale_value(25, scale_factor)}px; border-left-width: {scaled_border}px;
        border-left-color: #707070; border-left-style: solid;
        border-top-right-radius: {scaled_border_radius // 2}px; border-bottom-right-radius: {scaled_border_radius // 2}px;
        background-color: #555555;
    }}
    QComboBox::down-arrow {{
        image: url(assets/icons/down_arrow_dark.png); /* PROVIDE A DARK ARROW ICON */
        width: {scale_value(12, scale_factor)}px; height: {scale_value(12, scale_factor)}px;
    }}

    /* ==================== Screen Specific Styles ==================== */

    /* --- Home Screen Media --- */
    QLabel#albumArtLabel {{ /* Targets ScrollingLabel */
        border: {scale_value(2, scale_factor)}px solid #505050;
        background-color: rgba(80, 80, 80, 0.2);
        border-radius: {scaled_border_radius}px;
        font-size: {scale_value(base_font_size_pt, scale_factor)}pt;
        color: #bbbbbb;
        qproperty-alignment: 'AlignCenter';
        margin-bottom: {scaled_padding // 1.5}px;
        padding: {scaled_padding}px;
        /* --- Enforce Square Aspect Ratio --- */
        min-width: {scaled_album_art_size}px;
        max-width: {scaled_album_art_size}px;
        min-height: {scaled_album_art_size}px;
        max-height: {scaled_album_art_size}px;
        /* --- */
    }}
    QLabel#trackTitleLabel {{ /* Targets ScrollingLabel */
        min-height: {scale_value(35, scale_factor)}px;
        font-size: {scale_value(base_font_size_pt + 4, scale_factor)}pt;
        font-weight: bold;
        color: #eeeeee; /* Explicit light color for dark theme */
        margin-bottom: {scaled_padding // 4}px;
    }}
     QLabel#trackArtistLabel {{ /* Targets ScrollingLabel */
        min-height: {scale_value(30, scale_factor)}px;
        font-size: {scale_value(base_font_size_pt + 2, scale_factor)}pt;
        color: #cccccc; /* Explicit color */
        margin-bottom: {scaled_padding // 2}px;
     }}
     QLabel#trackTimeLabel {{
        min-height: {scale_value(24, scale_factor)}px;
        font-size: {scale_value(base_font_size_pt, scale_factor)}pt;
        color: #aaaaaa;
        qproperty-alignment: 'AlignCenter';
        margin-top: {scaled_padding // 2}px;
        margin-bottom: {scaled_padding}px;
     }}
     QPushButton#mediaPrevButton, QPushButton#mediaPlayPauseButton, QPushButton#mediaNextButton {{
        min-width: {scale_value(65, scale_factor)}px;
        padding: {scale_value(base_padding_px * 0.7, scale_factor)}px;
     }}
     QPushButton#mediaPlayPauseButton {{
         font-size: {scale_value(base_font_size_pt + 8, scale_factor)}pt;
         min-width: {scale_value(75, scale_factor)}px;
     }}

    /* --- OBD Screen --- */
    QLabel#speed_value, QLabel#rpm_value, QLabel#coolant_value, QLabel#fuel_value {{
        font-size: {scale_value(26, scale_factor)}pt; font-weight: bold;
        color: #34a4ff; padding-left: {scaled_padding // 2}px;
    }}

    /* --- Radio Screen --- */
    QLabel#freq_display {{
        font-size: {scale_value(44, scale_factor)}pt; 
        font-weight: bold; color: #20c9d6; qproperty-alignment: 'AlignCenter';
        margin-top: {scaled_padding}px; margin-bottom: {scaled_padding // 2}px;
    }}
    QLabel#radioStatusLabel {{
        font-size: {scale_value(base_font_size_pt, scale_factor)}pt; 
        color: #aaaaaa; qproperty-alignment: 'AlignCenter';
    }}

    /* --- Settings Screen --- */
    QPushButton#settingsSaveButton, QPushButton#settingsRestartButton {{
        padding: {scale_value(base_padding_px * 0.9, scale_factor)}px {scale_value(base_padding_px * 2.0, scale_factor)}px;
        min-width: {scale_value(200, scale_factor)}px; 
        font-size: {scale_value(base_font_size_pt + 2, scale_factor)}pt;
        margin-top: {scaled_padding // 2}px; margin-bottom: {scaled_padding // 2}px;
    }}

    /* --- Special Buttons --- */
    QPushButton#powerNavButton {{ background-color: #a04040; border-color: #803333; }}
    QPushButton#powerNavButton:pressed {{ background-color: #b35959; }}
    """

# --- apply_theme function ---
def apply_theme(app, theme_name, scale_factor=1.0):
    """Applies the selected theme stylesheet with the given scale factor."""
    print(f"DEBUG: apply_theme called. Theme: {theme_name}, Scale: {scale_factor:.2f}") # Debug
    if theme_name == "dark":
        # Theme function now gets base thickness from the constant
        style_sheet = get_dark_theme(scale_factor)
    else: # Default to light
        style_sheet = get_light_theme(scale_factor)

    app.setStyleSheet(style_sheet)
