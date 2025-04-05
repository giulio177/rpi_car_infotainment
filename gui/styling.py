# gui/styling.py

# --- Helper function to calculate scaled int ---
def scale_value(base_value, scale_factor):
    """Calculates scaled integer value, ensuring minimum of 1."""
    return max(1, int(base_value * scale_factor))

# --- MODIFIED Functions to accept scale factor ---

def get_light_theme(scale_factor=1.0):
    # Define base sizes
    base_font_size_pt = 12 # Base font size in points for base resolution
    base_padding_px = 10
    base_button_min_height_px = 40
    base_border_radius_px = 5
    base_border_px = 1

    # Calculate scaled sizes
    scaled_font_size = scale_value(base_font_size_pt, scale_factor)
    scaled_padding = scale_value(base_padding_px, scale_factor)
    scaled_button_min_height = scale_value(base_button_min_height_px, scale_factor)
    scaled_border_radius = scale_value(base_border_radius_px, scale_factor)
    scaled_border = scale_value(base_border_px, scale_factor)

    # Use scaled sizes in the QSS string
    return f"""
    QWidget {{
        color: #333;
        font-size: {scaled_font_size}pt; /* Apply scaled base font size */
    }}
    QMainWindow, QStackedWidget {{
         background-color: #f0f0f0; /* Apply background to main containers */
    }}
    QWidget#central_widget {{ /* Target central widget specifically */
         background-color: #f0f0f0;
    }}
    QWidget#persistentBottomBar {{ /* Style bottom bar */
        background-color: #e0e0e0;
        border-top: {scaled_border}px solid #b0b0b0;
    }}
    QWidget#grid_widget {{ /* Example: specific widget styling */
         background-color: transparent; /* Make grid container transparent */
    }}
     QWidget#media_widget {{
         background-color: transparent;
     }}
     /* Specific styling for settings screen scroll area */
     QWidget#settingsScrollContent {{
         background-color: #f0f0f0; /* Match main background */
     }}

    QPushButton {{
        background-color: #dcdcdc;
        border: {scaled_border}px solid #b0b0b0;
        padding: {scaled_padding // 2}px {scaled_padding}px; /* Scaled padding */
        border-radius: {scaled_border_radius}px;
        min-height: {scaled_button_min_height}px; /* Scaled min height */
    }}
    QPushButton:pressed {{
        background-color: #c0c0c0;
    }}

    QPushButton#powerNavButton {{
        background-color: #ff8080;
        border-color: #cc6666;
    }}
     QPushButton#powerNavButton:pressed {{
        background-color: #e67373;
     }}
     QPushButton#settingsSaveButton, QPushButton#settingsRestartButton {{
        padding: {scaled_padding // 1.5}px {scaled_padding * 1.5}px;
        min-width: {scale_value(150, scale_factor)}px;
     }}


    QLabel {{
        padding: {scaled_padding // 3}px;
        background-color: transparent;
    }}
    QLabel#headerTitle {{
        font-size: {scale_value(16, scale_factor)}pt;
        font-weight: bold;
    }}
     QLabel#headerClock {{
        font-size: {scale_value(16, scale_factor)}pt;
     }}
     QLabel#statusBarObdLabel, QLabel#statusBarRadioLabel,
     QLabel#statusBarBtNameLabel, QLabel#statusBarBtBatteryLabel {{
         font-size: {scale_value(9, scale_factor)}pt;
         padding: 2px;
     }}
      QLabel#statusBarBtBatteryLabel {{
         padding-left: {scale_value(3, scale_factor)}px;
         font-weight: bold;
     }}
     QLabel#statusBarSeparator {{
         font-size: {scale_value(9, scale_factor)}pt;
         color: #888;
         padding-left: {scaled_padding // 2}px;
         padding-right: {scaled_padding // 2}px;
     }}
     /* Styling for specific labels */
     QLabel#freq_display {{
         font-size: {scale_value(36, scale_factor)}pt;
         font-weight: bold;
         color: #17a2b8;
         qproperty-alignment: 'AlignCenter';
     }}
      QLabel#speed_value, QLabel#rpm_value, QLabel#coolant_value, QLabel#fuel_value {{
         font-size: {scale_value(22, scale_factor)}pt;
         font-weight: bold;
         color: #007bff;
     }}
      QLabel#resolutionNoteLabel {{
         font-size: {scale_value(base_font_size_pt - 2, scale_factor)}pt;
         color: #666666;
     }}

    /* --- Home Screen Media Player --- */
    QLabel#albumArtLabel {{ /* Targets ScrollingLabel */
        border: {scale_value(2, scale_factor)}px solid #a0a0a0; /* Thicker border */
        background-color: rgba(128, 128, 128, 0.1);
        border-radius: {scaled_border_radius}px;
        font-size: {scale_value(base_font_size_pt, scale_factor)}pt;
        color: #555555;
        min-height: {scale_value(140, scale_factor)}px; /* Adjusted min height */
        /* Width is ignored by ScrollingLabel's policy */
        qproperty-alignment: 'AlignCenter'; /* Alignment from code */
        margin-bottom: {scaled_padding // 2}px;
        padding: {scaled_padding}px; /* Increase padding inside */
    }}
    QLabel#trackTitleLabel, QLabel#trackArtistLabel {{ /* Targets ScrollingLabel */
        min-height: {scale_value(25, scale_factor)}px; /* Ensure min height for text lines */
        /* Alignment set in code */
    }}
    QLabel#trackTitleLabel {{
        font-size: {scale_value(base_font_size_pt + 2, scale_factor)}pt;
        font-weight: bold;
    }}
     QLabel#trackArtistLabel {{
        font-size: {scale_value(base_font_size_pt, scale_factor)}pt;
     }}
     QLabel#trackTimeLabel {{
        min-height: {scale_value(20, scale_factor)}px;
        font-size: {scale_value(base_font_size_pt - 1, scale_factor)}pt;
        color: #666666;
        qproperty-alignment: 'AlignCenter';
        margin-top: {scaled_padding // 3}px;
        margin-bottom: {scaled_padding // 2}px;
     }}
     QPushButton#mediaPrevButton, QPushButton#mediaPlayPauseButton, QPushButton#mediaNextButton {{
        min-width: {scale_value(50, scale_factor)}px;
     }}
     QPushButton#mediaPlayPauseButton {{
         font-size: {scale_value(base_font_size_pt + 4, scale_factor)}pt;
     }}
     /* --- End Media Player Styles --- */


    QLineEdit, QComboBox {{
        background-color: white;
        border: {scaled_border}px solid #b0b0b0;
        padding: {scaled_padding // 2}px;
        border-radius: {scaled_border_radius // 2}px;
        min-height: {scale_value(base_button_min_height_px * 0.8, scale_factor)}px;
    }}
    /* Styling for QComboBox dropdown */
    QComboBox QAbstractItemView {{
        background-color: white;
        color: #333;
        border: {scaled_border}px solid #b0b0b0;
        selection-background-color: #dcdcdc;
        selection-color: #333;
        padding: {scaled_padding // 3}px;
        outline: 0px;
    }}
     QComboBox QAbstractItemView::item {{
         min-height: {scale_value(base_button_min_height_px * 0.7, scale_factor)}px;
     }}
     QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: {scale_value(20, scale_factor)}px;
        border-left-width: {scaled_border}px;
        border-left-color: #b0b0b0;
        border-left-style: solid;
        border-top-right-radius: {scaled_border_radius // 2}px;
        border-bottom-right-radius: {scaled_border_radius // 2}px;
        background-color: #dcdcdc;
    }}
    QComboBox::down-arrow {{
         image: url(assets/icons/down_arrow_light.png); /* PROVIDE A LIGHT ARROW ICON */
         width: {scale_value(10, scale_factor)}px;
         height: {scale_value(10, scale_factor)}px;
    }}


    QSlider::groove:horizontal {{
        border: {scaled_border}px solid #bbb;
        background: white;
        height: {scale_value(8, scale_factor)}px;
        border-radius: {scaled_border_radius // 2}px;
    }}
    QSlider::handle:horizontal {{
        background: #5050fa;
        border: {scaled_border}px solid #3030cc;
        width: {scale_value(18, scale_factor)}px;
        margin: -{scale_value(6, scale_factor)}px 0;
        border-radius: {scaled_border_radius}px;
    }}
    QProgressBar {{
        border: {scaled_border}px solid grey;
        border-radius: {scaled_border_radius // 2}px;
        background-color: #e0e0e0;
        text-align: center;
        height: {scale_value(15, scale_factor)}px;
    }}
    QProgressBar::chunk {{
        background-color: #05B8CC;
        width: {scale_value(10, scale_factor)}px;
        margin: {scale_value(1, scale_factor)}px;
        border-radius: {scale_value(base_border_radius // 3, scale_factor)}px;
    }}
    QGroupBox {{
        font-size: {scale_value(base_font_size_pt + 1, scale_factor)}pt;
        border: {scaled_border}px solid gray;
        border-radius: {scaled_border_radius}px;
        margin-top: {scale_value(10, scale_factor)}px;
         background-color: #e8e8e8;
         padding: {scaled_padding // 2}px;
         padding-top: {scale_value(base_padding_px * 1.2, scale_factor)}px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 {scaled_padding // 2}px;
        left: {scaled_padding}px;
        top: -{scaled_padding // 3}px;
    }}

    /* ScrollArea Styling Light */
    QScrollArea#settingsScrollArea {{
        border: none;
        background-color: transparent;
    }}
    QScrollBar:vertical {{
        border: {scaled_border}px solid #c0c0c0;
        background: #e0e0e0;
        width: {scale_value(12, scale_factor)}px;
        margin: 0px 0px 0px 0px;
    }}
    QScrollBar::handle:vertical {{
        background: #a0a0a0;
        min-height: {scale_value(25, scale_factor)}px;
        border-radius: {scale_value(5, scale_factor)}px;
    }}
     QScrollBar::handle:vertical:hover {{
        background: #909090;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        border: none; background: none; height: 0px;
        subcontrol-position: top; subcontrol-origin: margin;
    }}

    /* Add other specific styles */
    """

def get_dark_theme(scale_factor=1.0):
    # Define base sizes
    base_font_size_pt = 12
    base_padding_px = 10
    base_button_min_height_px = 40
    base_border_radius_px = 5
    base_border_px = 1

    # Calculate scaled sizes
    scaled_font_size = scale_value(base_font_size_pt, scale_factor)
    scaled_padding = scale_value(base_padding_px, scale_factor)
    scaled_button_min_height = scale_value(base_button_min_height_px, scale_factor)
    scaled_border_radius = scale_value(base_border_radius_px, scale_factor)
    scaled_border = scale_value(base_border_px, scale_factor)

    return f"""
    QWidget {{
        color: #e0e0e0;
        font-size: {scaled_font_size}pt;
    }}
     QMainWindow, QStackedWidget {{ background-color: #2e2e2e; }}
    QWidget#central_widget {{ background-color: #2e2e2e; }}
    QWidget#persistentBottomBar {{ background-color: #3a3a3a; border-top: {scaled_border}px solid #505050; }}
     QWidget#grid_widget, QWidget#media_widget {{ background-color: transparent; }}
     QWidget#settingsScrollContent {{ background-color: #2e2e2e; }}

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
     QPushButton#powerNavButton {{
        background-color: #a04040;
        border-color: #803333;
    }}
     QPushButton#powerNavButton:pressed {{
        background-color: #b35959;
     }}
     QPushButton#settingsSaveButton, QPushButton#settingsRestartButton {{
        padding: {scaled_padding // 1.5}px {scaled_padding * 1.5}px;
        min-width: {scale_value(150, scale_factor)}px;
     }}


    QLabel {{
        padding: {scaled_padding // 3}px;
        background-color: transparent;
    }}
    QLabel#headerTitle {{
        font-size: {scale_value(16, scale_factor)}pt;
        font-weight: bold;
    }}
     QLabel#headerClock {{
        font-size: {scale_value(16, scale_factor)}pt;
     }}
      QLabel#statusBarObdLabel, QLabel#statusBarRadioLabel,
      QLabel#statusBarBtNameLabel, QLabel#statusBarBtBatteryLabel {{
         font-size: {scale_value(9, scale_factor)}pt;
         padding: 2px;
     }}
      QLabel#statusBarBtBatteryLabel {{
         padding-left: {scale_value(3, scale_factor)}px;
         font-weight: bold;
     }}
     QLabel#statusBarSeparator {{
         font-size: {scale_value(9, scale_factor)}pt;
         color: #888;
         padding-left: {scaled_padding // 2}px;
         padding-right: {scaled_padding // 2}px;
     }}
     QLabel#freq_display {{
         font-size: {scale_value(36, scale_factor)}pt;
         font-weight: bold;
         color: #20c9d6;
         qproperty-alignment: 'AlignCenter';
     }}
      QLabel#speed_value, QLabel#rpm_value, QLabel#coolant_value, QLabel#fuel_value {{
         font-size: {scale_value(22, scale_factor)}pt;
         font-weight: bold;
         color: #34a4ff;
     }}
      QLabel#resolutionNoteLabel {{
         font-size: {scale_value(base_font_size_pt - 2, scale_factor)}pt;
         color: #aaaaaa;
     }}

    /* --- Home Screen Media Player --- */
    QLabel#albumArtLabel {{ /* Targets ScrollingLabel */
        border: {scale_value(2, scale_factor)}px solid #505050; /* Dark theme border */
        background-color: rgba(80, 80, 80, 0.2); /* Dark theme subtle background */
        border-radius: {scaled_border_radius}px;
        font-size: {scale_value(base_font_size_pt, scale_factor)}pt;
        color: #bbbbbb; /* Dark Theme Dim Text */
        min-height: {scale_value(140, scale_factor)}px; /* Adjusted min height */
        qproperty-alignment: 'AlignCenter';
        margin-bottom: {scaled_padding // 2}px;
        padding: {scaled_padding}px;
    }}
    QLabel#trackTitleLabel, QLabel#trackArtistLabel {{ /* Targets ScrollingLabel */
        min-height: {scale_value(25, scale_factor)}px;
    }}
    QLabel#trackTitleLabel {{
        font-size: {scale_value(base_font_size_pt + 2, scale_factor)}pt;
        font-weight: bold;
    }}
     QLabel#trackArtistLabel {{
        font-size: {scale_value(base_font_size_pt, scale_factor)}pt;
     }}
     QLabel#trackTimeLabel {{
        min-height: {scale_value(20, scale_factor)}px;
        font-size: {scale_value(base_font_size_pt - 1, scale_factor)}pt;
        color: #aaaaaa; /* Dark Theme Dim */
        qproperty-alignment: 'AlignCenter';
        margin-top: {scaled_padding // 3}px;
        margin-bottom: {scaled_padding // 2}px;
     }}
     QPushButton#mediaPrevButton, QPushButton#mediaPlayPauseButton, QPushButton#mediaNextButton {{
        min-width: {scale_value(50, scale_factor)}px;
     }}
     QPushButton#mediaPlayPauseButton {{
         font-size: {scale_value(base_font_size_pt + 4, scale_factor)}pt;
     }}
     /* --- End Media Player Styles --- */

    QLineEdit {{
        background-color: #404040;
        border: {scaled_border}px solid #707070;
        color: #e0e0e0;
        padding: {scaled_padding // 2}px;
        border-radius: {scaled_border_radius // 2}px;
        min-height: {scale_value(base_button_min_height_px * 0.8, scale_factor)}px;
    }}

    QComboBox {{
        background-color: #404040;
        border: {scaled_border}px solid #707070;
        color: #e0e0e0;
        padding: {scaled_padding // 2}px;
        border-radius: {scaled_border_radius // 2}px;
        min-height: {scale_value(base_button_min_height_px * 0.8, scale_factor)}px;
        selection-background-color: #6060a0;
    }}
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: {scale_value(20, scale_factor)}px;
        border-left-width: {scaled_border}px;
        border-left-color: #707070;
        border-left-style: solid;
        border-top-right-radius: {scaled_border_radius // 2}px;
        border-bottom-right-radius: {scaled_border_radius // 2}px;
        background-color: #555555;
    }}
    QComboBox::down-arrow {{
         image: url(assets/icons/down_arrow_dark.png); /* PROVIDE A DARK ARROW ICON */
         width: {scale_value(10, scale_factor)}px;
         height: {scale_value(10, scale_factor)}px;
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
         min-height: {scale_value(base_button_min_height_px * 0.7, scale_factor)}px;
     }}


    QSlider::groove:horizontal {{
        border: {scaled_border}px solid #666;
        background: #555;
        height: {scale_value(8, scale_factor)}px;
        border-radius: {scaled_border_radius // 2}px;
    }}
    QSlider::handle:horizontal {{
        background: #8080ff;
        border: {scaled_border}px solid #6060dd;
        width: {scale_value(18, scale_factor)}px;
        margin: -{scale_value(6, scale_factor)}px 0;
        border-radius: {scaled_border_radius}px;
    }}
     QProgressBar {{
        border: {scaled_border}px solid #555;
        border-radius: {scaled_border_radius // 2}px;
        background-color: #444;
        text-align: center;
        height: {scale_value(15, scale_factor)}px;
    }}
    QProgressBar::chunk {{
        background-color: #1db8cc;
        width: {scale_value(10, scale_factor)}px;
        margin: {scale_value(1, scale_factor)}px;
         border-radius: {scale_value(base_border_radius // 3, scale_factor)}px;
    }}
     QGroupBox {{
        font-size: {scale_value(base_font_size_pt + 1, scale_factor)}pt;
        border: {scaled_border}px solid #666;
        border-radius: {scaled_border_radius}px;
        margin-top: {scale_value(10, scale_factor)}px;
        background-color: #383838;
        padding: {scaled_padding // 2}px;
        padding-top: {scale_value(base_padding_px * 1.2, scale_factor)}px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 {scaled_padding // 2}px;
        left: {scaled_padding}px;
        top: -{scaled_padding // 3}px;
    }}

    /* ScrollArea Styling Dark */
    QScrollArea#settingsScrollArea {{
        border: none;
        background-color: transparent;
    }}
    QScrollBar:vertical {{
        border: {scaled_border}px solid #505050;
        background: #3a3a3a;
        width: {scale_value(12, scale_factor)}px;
        margin: 0px 0px 0px 0px;
    }}
    QScrollBar::handle:vertical {{
        background: #686868;
        min-height: {scale_value(25, scale_factor)}px;
        border-radius: {scale_value(5, scale_factor)}px;
    }}
     QScrollBar::handle:vertical:hover {{
        background: #787878;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        border: none; background: none; height: 0px;
        subcontrol-position: top; subcontrol-origin: margin;
    }}

    /* Add other specific styles */
    """

# --- apply_theme function ---
def apply_theme(app, theme_name, scale_factor=1.0):
    """Applies the selected theme stylesheet with the given scale factor."""
    if theme_name == "dark":
        app.setStyleSheet(get_dark_theme(scale_factor))
    else: # Default to light
        app.setStyleSheet(get_light_theme(scale_factor))
