# gui/styling.py

import math


# --- Helper function to calculate scaled int ---
def scale_value(base_value, scale_factor):
    """Calculates scaled integer value, ensuring minimum of 1."""
    try:
        numeric_base = float(base_value)
        return max(1, int(numeric_base * scale_factor))
    except (ValueError, TypeError):
        print(
            f"Warning: Could not convert base_value '{base_value}' to number in scale_value. Returning 1."
        )
        return 1


BASE_SLIDER_THICKNESS = 25  # <<< --- ADJUSTED FOR 1024x600 RESOLUTION --- >>>

SCROLL_BAR_WIDTH = 25 # spessore barra di scorrimento impostazioni e logs

# --- Theme Functions accepting scale_factor ---


def get_light_theme(scale_factor=1.0):
    # Base sizes relative to 1024x600
    base_font_size_pt = 12
    base_padding_px = 8
    base_album_art_size_px = 120  # Base size for square side (adjusted for 1024x600)
    base_button_min_height_px = 35  # Base for normal buttons (adjusted for 1024x600)
    base_border_radius_px = 4
    base_border_px = 1

    # Calculate scaled sizes
    scaled_font_size = scale_value(base_font_size_pt, scale_factor)
    scaled_padding = scale_value(base_padding_px, scale_factor)
    scaled_album_art_size = scale_value(
        base_album_art_size_px, scale_factor
    )  # Scaled square size
    scaled_button_min_height = scale_value(base_button_min_height_px, scale_factor)
    scaled_border_radius = scale_value(base_border_radius_px, scale_factor)
    scaled_border = scale_value(base_border_px, scale_factor)
    # --- Calculate DERIVED slider sizes ---
    scaled_slider_thickness = scale_value(BASE_SLIDER_THICKNESS, scale_factor)
    # Handle size based on groove thickness (e.g., 1.8x thickness, ensure minimum size)
    scaled_slider_handle_s = max(
        scaled_slider_thickness + scale_value(10, scale_factor),
        scale_value(BASE_SLIDER_THICKNESS * 1.2, scale_factor),
    )  # Slightly smaller ratio?
    scaled_slider_handle_s = (
        int(math.ceil(scaled_slider_handle_s / 2.0)) * 2
    )  # Ensure even number
    # Calculate margin to center handle vertically on groove
    scaled_slider_handle_margin_v = (
        -(scaled_slider_handle_s - scaled_slider_thickness) // 2
    )  # Vertical margin
    scaled_slider_handle_margin_h = (
        scaled_slider_handle_s // 20
    )  # Horizontal margin based on handle size (prevents clipping groove too much)

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
    /* Status labels removed from bottom bar for cleaner design */

    /* ==================== General Widgets ==================== */
    QPushButton {{
        background-color: #dcdcdc;
        border: {scaled_border}px solid #b0b0b0;
        padding: {scale_value(base_padding_px * 0.6, scale_factor)}px {scale_value(base_padding_px * 0.6, scale_factor)}px; /* Symmetric padding */
        border-radius: {scaled_border_radius}px;
        min-height: {scaled_button_min_height}px;
        outline: none; /* Remove focus outline */
    }}
    QPushButton:pressed {{ background-color: #c0c0c0; }}
    QPushButton:disabled {{ background-color: #e8e8e8; color: #a0a0a0; border-color: #c0c0c0; }}
    QPushButton:focus {{ outline: none; border: {scaled_border}px solid #b0b0b0; }} /* Remove focus dotted outline */

    QLabel {{ padding: {scaled_padding // 4}px; background-color: transparent; }}

    QLineEdit, QComboBox {{
        background-color: #ffffff;
        border: {scaled_border}px solid #b0b0b0;
        padding: {scale_value(base_padding_px * 0.6, scale_factor)}px; /* Adjusted padding */
        border-radius: {scaled_border_radius // 2}px;
        min-height: {scale_value(base_button_min_height_px * 0.9, scale_factor)}px;
    }}

    /* --- QSlider Styling (Targeting #volumeSlider and #timeSlider) --- */
    QSlider#volumeSlider, QSlider#timeSlider {{ /* Style the slider widget itself */
        min-height: {scaled_slider_handle_s + scale_value(4, scale_factor)}px; /* Ensure widget is tall enough for handle + small buffer */
    }}

    QSlider#volumeSlider::groove:horizontal, QSlider#timeSlider::groove:horizontal {{
        border: {scaled_border}px solid #aaaaaa;
        background: #e8e8e8;
        height: {scaled_slider_thickness}px; /* Use derived scaled thickness */
        border-radius: {scaled_slider_thickness // 2}px;
        margin: 0px {scaled_slider_handle_margin_h}px; /* Adjust horizontal margin based on derived handle size to avoid clipping */
    }}
    QSlider#volumeSlider::handle:horizontal, QSlider#timeSlider::handle:horizontal {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #7070ff, stop:1 #4040fa);
        border: {scaled_border}px solid #3030cc;
        width: {scaled_slider_handle_s}px;
        height: {scaled_slider_handle_s}px;
        margin: {scaled_slider_handle_margin_v}px 0; /* Apply calculated vertical margin */
        border-radius: {scaled_slider_handle_s // 2}px; /* Make it circular */
    }}
    QSlider#volumeSlider::handle:horizontal:hover, QSlider#timeSlider::handle:horizontal:hover {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8e8efa, stop:1 #6060fa);
        border-color: #2020aa;
    }}
    QSlider#volumeSlider::handle:horizontal:pressed, QSlider#timeSlider::handle:horizontal:pressed {{
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
        width: {scale_value(SCROLL_BAR_WIDTH, scale_factor)}px; margin: 0px;
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

     /* Header Quit Button */
     QPushButton#headerQuitButton {{
         background-color: #ff5252;
         border: {scaled_border}px solid #d32f2f;
         border-radius: {scaled_border_radius}px;
         outline: none;
     }}

     QPushButton#headerQuitButton:hover {{
         background-color: #ff7070;
     }}

     QPushButton#headerQuitButton:pressed {{
         background-color: #d32f2f;
     }}

     QPushButton#headerQuitButton:focus {{
         outline: none;
         border: {scaled_border}px solid #d32f2f;
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
        max-height: {scaled_album_art_size // 2}px;
        /* --- */
        margin-bottom: {40}px; /* Use full scaled padding or adjust (e.g., * 1.5) */
    }}
    QLabel#trackTitleLabel {{ /* Targets ScrollingLabel */
        min-height: {scale_value(30, scale_factor)}px; /* INCREASED min-height for larger font */
        font-size: {scale_value(base_font_size_pt + 4, scale_factor)}pt; /* RESTORED/ADJUSTED larger font size */
        font-weight: bold;
        color: #222222; /* Explicit dark color for light theme */
        /* REMOVED debug background/border */
        margin-bottom: {scaled_padding // 4}px;
    }}
     QLabel#trackArtistLabel {{ /* Targets ScrollingLabel */
        min-height: {scale_value(26, scale_factor)}px; /* INCREASED min-height */
        font-size: {scale_value(base_font_size_pt + 2, scale_factor)}pt; /* RESTORED/ADJUSTED font size */
        color: #444444; /* Explicit color */
        /* REMOVED debug background/border */
        margin-bottom: {scaled_padding // 2}px;
     }}
     QLabel#trackTimeLabel {{
        min-height: {scale_value(22, scale_factor)}px;
        font-size: {scale_value(base_font_size_pt, scale_factor)}pt;
        color: #666666;
        qproperty-alignment: 'AlignCenter';
        margin-top: {scaled_padding // 3}px; /* Increased margin above time */
        margin-bottom: {scaled_padding // 2}px; /* Increased margin below time */
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
        padding: {scale_value(base_padding_px * 0.9, scale_factor)}px {scale_value(base_padding_px * 0.9, scale_factor)}px;
        font-size: {scale_value(base_font_size_pt + 2, scale_factor)}pt; /* Adjusted base size */
        margin-top: {scaled_padding // 2}px; margin-bottom: {scaled_padding // 2}px;
     }}
     QPushButton#airplayInfoButton {{
        padding: {scale_value(base_padding_px * 0.7, scale_factor)}px {scale_value(base_padding_px * 1.5, scale_factor)}px;
        min-width: {scale_value(180, scale_factor)}px;
        font-size: {scale_value(base_font_size_pt + 1, scale_factor)}pt;
        margin-top: {scaled_padding // 2}px; margin-bottom: {scaled_padding // 2}px;
        background-color: #4a90e2; border-color: #357abd;
     }}
     QPushButton#airplayInfoButton:pressed {{
        background-color: #357abd;
     }}

    /* --- Music Player Screen --- */
    QScrollArea#lyricsScrollArea {{
        border: {scaled_border}px solid #b0b0b0;
        border-radius: {scaled_border_radius}px;
        background-color: #f8f8f8;
    }}

    /* --- Logs Screen --- */

    QPlainTextEdit#logsText {{
        font-size: {scale_value(base_font_size_pt, scale_factor)}pt;
        padding: {scaled_padding}px;
        line-height: 150%;
        background-color: #f8f8f8;
        color: #333333;
    }}

    QPlainTextEdit#logsText QScrollBar:vertical {{
        width: {scale_value(SCROLL_BAR_WIDTH, scale_factor)}px;
    }}


    /* --- AirPlay Screen (scroll area removed) --- */

    QLabel#lyricsContent {{
        font-size: {scale_value(base_font_size_pt, scale_factor)}pt;
        padding: {scaled_padding}px;
        line-height: 150%;
        background-color: #f8f8f8;
        color: #333333;
    }}

    QLabel#currentTimeLabel, QLabel#totalTimeLabel {{
        font-size: {scale_value(base_font_size_pt, scale_factor)}pt;
        min-width: {scale_value(50, scale_factor)}px;
    }}

    QPushButton#libraryButton, QPushButton#backButton, QPushButton#downloadButton, QPushButton#selectFolderButton {{
        padding: {scale_value(base_padding_px * 0.9, scale_factor)}px {scale_value(base_padding_px * 2.0, scale_factor)}px;
        min-width: {scale_value(150, scale_factor)}px;
        font-size: {scale_value(base_font_size_pt + 1, scale_factor)}pt;
        margin-top: {scaled_padding}px;
    }}

    QLabel#libraryTitle {{
        font-size: {scale_value(base_font_size_pt + 4, scale_factor)}pt;
        font-weight: bold;
        margin-bottom: {scaled_padding}px;
    }}

    
    /* --- Special Action Buttons --- */
    /* Azioni a livello di APP (Grigio scuro, meno prominente) */
    QPushButton#appActionButton {{
        background-color: #a9a9a9; /* Dark Gray */
        border-color: #808080; /* Gray */
        outline: none;
    }}
    QPushButton#appActionButton:pressed {{
        background-color: #696969; /* Dim Gray */
    }}
    QPushButton#appActionButton:focus {{
        outline: none;
        border-color: #808080;
    }}

    /* Azioni a livello di SISTEMA (Rosso, "pericoloso") */
    QPushButton#systemActionButton {{
        background-color: #ff8080; /* Rosso Chiaro */
        border-color: #cc6666;
        outline: none;
    }}
    QPushButton#systemActionButton:pressed {{
        background-color: #e67373; /* Rosso più scuro quando premuto */
    }}
    QPushButton#systemActionButton:focus {{
        outline: none;
        border-color: #cc6666;
    }}



    /* ==================== Dialog and Popup Styles ==================== */
    QMessageBox {{
        background-color: #f0f0f0;
        color: #333333;
        border: {scaled_border}px solid #b0b0b0;
        border-radius: {scaled_border_radius}px;
    }}
    QMessageBox QLabel {{
        color: #333333;
        font-size: {scaled_font_size}pt;
        padding: {scaled_padding}px;
    }}
    QMessageBox QPushButton {{
        background-color: #dcdcdc;
        border: {scaled_border}px solid #b0b0b0;
        padding: {scale_value(base_padding_px * 0.8, scale_factor)}px {scale_value(base_padding_px * 1.5, scale_factor)}px;
        border-radius: {scaled_border_radius}px;
        min-height: {scaled_button_min_height}px;
        min-width: {scale_value(80, scale_factor)}px;
        outline: none;
    }}
    QMessageBox QPushButton:pressed {{
        background-color: #c0c0c0;
    }}
    QMessageBox QPushButton:focus {{
        outline: none;
        border: {scaled_border}px solid #007bff;
    }}

    QDialog {{
        background-color: #f0f0f0;
        color: #333333;
        border: {scaled_border}px solid #b0b0b0;
        border-radius: {scaled_border_radius}px;
    }}

    /* ==================== Network Dialog Styles ==================== */
    QDialog#networkDialog {{
        background-color: #f0f0f0;
        color: #333333;
        border: {scaled_border}px solid #b0b0b0;
        border-radius: {scaled_border_radius}px;
    }}
    QLabel#dialogTitle {{
        font-size: {scale_value(base_font_size_pt + 4, scale_factor)}pt;
        font-weight: bold;
        color: #333333;
        margin-bottom: {scaled_padding}px;
    }}
    QListWidget {{
        background-color: #ffffff;
        border: {scaled_border}px solid #b0b0b0;
        border-radius: {scaled_border_radius}px;
        selection-background-color: #dcdcdc;
        selection-color: #333333;
        padding: {scaled_padding // 2}px;
    }}
    QListWidget::item {{
        padding: {scaled_padding // 2}px;
        border-bottom: 1px solid #e0e0e0;
    }}
    QListWidget::item:selected {{
        background-color: #007bff;
        color: #ffffff;
    }}

    /* ==================== Virtual Keyboard Styles ==================== */
    QDialog#virtualKeyboard {{
        background-color: #f0f0f0;
        color: #333333;
        border: {scaled_border}px solid #b0b0b0;
        border-radius: {scaled_border_radius}px;
    }}
    QLineEdit#keyboardTextInput {{
        font-size: {scale_value(base_font_size_pt + 2, scale_factor)}pt;
        padding: {scale_value(base_padding_px, scale_factor)}px;
        min-height: {scale_value(40, scale_factor)}px;
        border: {scaled_border}px solid #b0b0b0;
        border-radius: {scaled_border_radius}px;
        background-color: #ffffff;
    }}
    QPushButton#keyboardKey {{
        background-color: #e8e8e8;
        border: {scaled_border}px solid #c0c0c0;
        border-radius: {scaled_border_radius}px;
        min-width: {scale_value(40, scale_factor)}px;
        min-height: {scale_value(40, scale_factor)}px;
        font-size: {scale_value(base_font_size_pt, scale_factor)}pt;
        outline: none;
    }}
    QPushButton#keyboardKey:pressed {{
        background-color: #d0d0d0;
    }}
    QPushButton#keyboardSpecialKey {{
        background-color: #d0d0d0;
        border: {scaled_border}px solid #a0a0a0;
        border-radius: {scaled_border_radius}px;
        min-width: {scale_value(50, scale_factor)}px;
        min-height: {scale_value(40, scale_factor)}px;
        font-size: {scale_value(base_font_size_pt, scale_factor)}pt;
        outline: none;
    }}
    QPushButton#keyboardSpecialKey:pressed {{
        background-color: #b0b0b0;
    }}
    QPushButton#keyboardSpaceKey {{
        background-color: #e8e8e8;
        border: {scaled_border}px solid #c0c0c0;
        border-radius: {scaled_border_radius}px;
        min-width: {scale_value(200, scale_factor)}px;
        min-height: {scale_value(40, scale_factor)}px;
        font-size: {scale_value(base_font_size_pt, scale_factor)}pt;
        outline: none;
    }}
    QPushButton#keyboardSpaceKey:pressed {{
        background-color: #d0d0d0;
    }}

    QFileDialog {{
        background-color: #f0f0f0;
        color: #333333;
    }}
    QFileDialog QListView {{
        background-color: #ffffff;
        border: {scaled_border}px solid #b0b0b0;
        color: #333333;
        selection-background-color: #dcdcdc;
        selection-color: #333333;
    }}
    QFileDialog QTreeView {{
        background-color: #ffffff;
        border: {scaled_border}px solid #b0b0b0;
        color: #333333;
        selection-background-color: #dcdcdc;
        selection-color: #333333;
    }}
    QFileDialog QPushButton {{
        background-color: #dcdcdc;
        border: {scaled_border}px solid #b0b0b0;
        padding: {scale_value(base_padding_px * 0.6, scale_factor)}px {scale_value(base_padding_px * 1.2, scale_factor)}px;
        border-radius: {scaled_border_radius}px;
        min-height: {scaled_button_min_height}px;
        outline: none;
    }}
    QFileDialog QPushButton:pressed {{
        background-color: #c0c0c0;
    }}
    QFileDialog QLineEdit {{
        background-color: #ffffff;
        border: {scaled_border}px solid #b0b0b0;
        padding: {scale_value(base_padding_px * 0.6, scale_factor)}px;
        border-radius: {scaled_border_radius // 2}px;
    }}
    """


def get_dark_theme(scale_factor=1.0):
    # Base sizes relative to 1024x600
    base_font_size_pt = 12
    base_padding_px = 8
    base_album_art_size_px = 120  # Base size for square side (adjusted for 1024x600)
    base_button_min_height_px = 35  # Base for normal buttons (adjusted for 1024x600)
    base_border_radius_px = 4
    base_border_px = 1

    # Calculate scaled sizes
    scaled_font_size = scale_value(base_font_size_pt, scale_factor)
    scaled_padding = scale_value(base_padding_px, scale_factor)
    scaled_album_art_size = scale_value(
        base_album_art_size_px, scale_factor
    )  # Scaled square size
    scaled_button_min_height = scale_value(base_button_min_height_px, scale_factor)
    scaled_border_radius = scale_value(base_border_radius_px, scale_factor)
    scaled_border = scale_value(base_border_px, scale_factor)
    # --- Calculate DERIVED slider sizes ---
    scaled_slider_thickness = scale_value(BASE_SLIDER_THICKNESS, scale_factor)
    scaled_slider_handle_s = max(
        scaled_slider_thickness + scale_value(10, scale_factor),
        scale_value(BASE_SLIDER_THICKNESS * 1.2, scale_factor),
    )
    scaled_slider_handle_s = int(math.ceil(scaled_slider_handle_s / 2.0)) * 2
    scaled_slider_handle_margin_v = (
        -(scaled_slider_handle_s - scaled_slider_thickness) // 2
    )
    scaled_slider_handle_margin_h = scaled_slider_handle_s // 20

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
    /* Status labels removed from bottom bar for cleaner design */

    /* ==================== General Widgets ==================== */
    QPushButton {{
        background-color: #505050;
        border: {scaled_border}px solid #707070; color: #e0e0e0;
        padding: {scale_value(base_padding_px * 0.6, scale_factor)}px {scale_value(base_padding_px * 0.6, scale_factor)}px;
        border-radius: {scaled_border_radius}px;
        min-height: {scaled_button_min_height}px;
        outline: none; /* Remove focus outline */
    }}
    QPushButton:pressed {{ background-color: #606060; }}
    QPushButton:disabled {{ background-color: #404040; color: #808080; border-color: #555555; }}
    QPushButton:focus {{ outline: none; border: {scaled_border}px solid #707070; }} /* Remove focus dotted outline */

    QLabel {{ padding: {scaled_padding // 4}px; background-color: transparent; }}

    QLineEdit, QComboBox {{
        background-color: #404040;
        border: {scaled_border}px solid #707070; color: #e0e0e0;
        padding: {scale_value(base_padding_px * 0.6, scale_factor)}px;
        border-radius: {scaled_border_radius // 2}px;
        min-height: {scale_value(base_button_min_height_px * 0.9, scale_factor)}px;
    }}

    /* --- QSlider Styling (Targeting #volumeSlider and #timeSlider) --- */
    QSlider#volumeSlider, QSlider#timeSlider {{
        min-height: {scaled_slider_handle_s + scale_value(4, scale_factor)}px;
    }}

    QSlider#volumeSlider::groove:horizontal, QSlider#timeSlider::groove:horizontal {{
        border: {scaled_border}px solid #555555; 
        background: #444444;
        height: {scaled_slider_thickness}px;
        border-radius: {scaled_slider_thickness // 2}px;
        margin: 0px {scaled_slider_handle_margin_h}px; /* Use derived horizontal margin */
    }}
    QSlider#volumeSlider::handle:horizontal, QSlider#timeSlider::handle:horizontal {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8080ff, stop:1 #6060f0);
        border: {scaled_border}px solid #5050dd;
        width: {scaled_slider_handle_s}px;
        height: {scaled_slider_handle_s}px;
        margin: {scaled_slider_handle_margin_v}px 0; /* Use derived vertical margin */
        border-radius: {scaled_slider_handle_s // 2}px;
    }}
    QSlider#volumeSlider::handle:horizontal:hover, QSlider#timeSlider::handle:horizontal:hover {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #9090ff, stop:1 #7070f0);
        border-color: #4040cc;
    }}
    QSlider#volumeSlider::handle:horizontal:pressed, QSlider#timeSlider::handle:horizontal:pressed {{
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
        width: {scale_value(SCROLL_BAR_WIDTH, scale_factor)}px; margin: 0px;
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

     /* Header Quit Button */
     QPushButton#headerQuitButton {{
         background-color: #d32f2f;
         border: {scaled_border}px solid #b71c1c;
         border-radius: {scaled_border_radius}px;
         outline: none;
     }}

     QPushButton#headerQuitButton:hover {{
         background-color: #ef5350;
     }}

     QPushButton#headerQuitButton:pressed {{
         background-color: #b71c1c;
     }}

     QPushButton#headerQuitButton:focus {{
         outline: none;
         border: {scaled_border}px solid #b71c1c;
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
        max-height: {scaled_album_art_size // 2}px;
        /* --- */
        margin-bottom: {40}px; /* Use full scaled padding or adjust (e.g., * 1.5) */
    }}
    QLabel#trackTitleLabel {{ /* Targets ScrollingLabel */
        min-height: {scale_value(20, scale_factor)}px; /* INCREASED min-height */
        font-size: {scale_value(base_font_size_pt + 4, scale_factor)}pt; /* RESTORED/ADJUSTED larger font size */
        font-weight: bold; /* RESTORED bold */
        color: #eeeeee; /* Explicit light color for dark theme */
        /* background-color: rgba(255,0,0,0.1); */
        margin-bottom: {scaled_padding // 3}px;
    }}
     QLabel#trackArtistLabel {{ /* Targets ScrollingLabel */
        min-height: {scale_value(26, scale_factor)}px; /* INCREASED min-height */
        font-size: {scale_value(base_font_size_pt + 2, scale_factor)}pt; /* RESTORED/ADJUSTED font size */
        color: #cccccc; /* Explicit color */
        /* background-color: rgba(255,0,0,0.1); */
        margin-bottom: {scaled_padding // 2}px;
     }}
     QLabel#trackTimeLabel {{
        min-height: {scale_value(22, scale_factor)}px;
        font-size: {scale_value(base_font_size_pt, scale_factor)}pt;
        color: #aaaaaa;
        qproperty-alignment: 'AlignCenter';
        margin-top: {scaled_padding // 3}px;
        margin-bottom: {scaled_padding // 2}px;
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
        padding: {scale_value(base_padding_px * 0.9, scale_factor)}px {scale_value(base_padding_px * 0.9, scale_factor)}px;
        font-size: {scale_value(base_font_size_pt + 2, scale_factor)}pt;
        margin-top: {scaled_padding // 2}px; margin-bottom: {scaled_padding // 2}px;
    }}
    QPushButton#airplayInfoButton {{
        padding: {scale_value(base_padding_px * 0.7, scale_factor)}px {scale_value(base_padding_px * 1.5, scale_factor)}px;
        min-width: {scale_value(180, scale_factor)}px;
        font-size: {scale_value(base_font_size_pt + 1, scale_factor)}pt;
        margin-top: {scaled_padding // 2}px; margin-bottom: {scaled_padding // 2}px;
        background-color: #4a90e2; border-color: #357abd;
    }}
    QPushButton#airplayInfoButton:pressed {{
        background-color: #357abd;
    }}

    /* --- Music Player Screen --- */
    QScrollArea#lyricsScrollArea {{
        border: {scaled_border}px solid #505050;
        border-radius: {scaled_border_radius}px;
        background-color: #383838;
    }}

    /* --- Logs Screen --- */

    QPlainTextEdit#logsText {{
        font-size: {scale_value(base_font_size_pt, scale_factor)}pt;
        padding: {scaled_padding}px;
        line-height: 150%;
        background-color: #383838;
        color: #e0e0e0;
    }}

    QPlainTextEdit#logsText QScrollBar:vertical {{
        width: {scale_value(SCROLL_BAR_WIDTH, scale_factor)}px;
    }}

    /* --- AirPlay Screen (scroll area removed) --- */

    QLabel#lyricsContent {{
        font-size: {scale_value(base_font_size_pt, scale_factor)}pt;
        padding: {scaled_padding}px;
        line-height: 150%;
        background-color: #383838;
        color: #e0e0e0;
    }}

    QLabel#currentTimeLabel, QLabel#totalTimeLabel {{
        font-size: {scale_value(base_font_size_pt, scale_factor)}pt;
        min-width: {scale_value(50, scale_factor)}px;
    }}

    QPushButton#libraryButton, QPushButton#backButton, QPushButton#downloadButton, QPushButton#selectFolderButton {{
        padding: {scale_value(base_padding_px * 0.9, scale_factor)}px {scale_value(base_padding_px * 2.0, scale_factor)}px;
        min-width: {scale_value(150, scale_factor)}px;
        font-size: {scale_value(base_font_size_pt + 1, scale_factor)}pt;
        margin-top: {scaled_padding}px;
    }}

    QLabel#libraryTitle {{
        font-size: {scale_value(base_font_size_pt + 4, scale_factor)}pt;
        font-weight: bold;
        margin-bottom: {scaled_padding}px;
    }}

    /* --- Special Action Buttons --- */
    /* Azioni a livello di APP (Grigio, si integra) */
    QPushButton#appActionButton {{
        background-color: #606060;
        border-color: #787878;
        outline: none;
    }}
    QPushButton#appActionButton:pressed {{
        background-color: #707070;
    }}
    QPushButton#appActionButton:focus {{
        outline: none;
        border-color: #787878;
    }}

    /* Azioni a livello di SISTEMA (Rosso, "pericoloso") */
    QPushButton#systemActionButton {{
        background-color: #a04040; /* Rosso Scuro */
        border-color: #803333;
        outline: none;
    }}
    QPushButton#systemActionButton:pressed {{
        background-color: #b35959; /* Rosso più chiaro quando premuto */
    }}
    QPushButton#systemActionButton:focus {{
        outline: none;
        border-color: #803333;
    }}
    /* ==================== Dialog and Popup Styles ==================== */
    QMessageBox {{
        background-color: #2e2e2e;
        color: #e0e0e0;
        border: {scaled_border}px solid #707070;
        border-radius: {scaled_border_radius}px;
    }}
    QMessageBox QLabel {{
        color: #e0e0e0;
        font-size: {scaled_font_size}pt;
        padding: {scaled_padding}px;
    }}
    QMessageBox QPushButton {{
        background-color: #505050;
        border: {scaled_border}px solid #707070;
        color: #e0e0e0;
        padding: {scale_value(base_padding_px * 0.8, scale_factor)}px {scale_value(base_padding_px * 1.5, scale_factor)}px;
        border-radius: {scaled_border_radius}px;
        min-height: {scaled_button_min_height}px;
        min-width: {scale_value(80, scale_factor)}px;
        outline: none;
    }}
    QMessageBox QPushButton:pressed {{
        background-color: #606060;
    }}
    QMessageBox QPushButton:focus {{
        outline: none;
        border: {scaled_border}px solid #34a4ff;
    }}

    QDialog {{
        background-color: #2e2e2e;
        color: #e0e0e0;
        border: {scaled_border}px solid #707070;
        border-radius: {scaled_border_radius}px;
    }}

    /* ==================== Network Dialog Styles ==================== */
    QDialog#networkDialog {{
        background-color: #2e2e2e;
        color: #e0e0e0;
        border: {scaled_border}px solid #707070;
        border-radius: {scaled_border_radius}px;
    }}
    QLabel#dialogTitle {{
        font-size: {scale_value(base_font_size_pt + 4, scale_factor)}pt;
        font-weight: bold;
        color: #e0e0e0;
        margin-bottom: {scaled_padding}px;
    }}
    QListWidget {{
        background-color: #404040;
        border: {scaled_border}px solid #707070;
        border-radius: {scaled_border_radius}px;
        selection-background-color: #34a4ff;
        selection-color: #ffffff;
        color: #e0e0e0;
        padding: {scaled_padding // 2}px;
    }}
    QListWidget::item {{
        padding: {scaled_padding // 2}px;
        border-bottom: 1px solid #505050;
    }}
    QListWidget::item:selected {{
        background-color: #34a4ff;
        color: #ffffff;
    }}

    /* ==================== Virtual Keyboard Styles ==================== */
    QDialog#virtualKeyboard {{
        background-color: #2e2e2e;
        color: #e0e0e0;
        border: {scaled_border}px solid #707070;
        border-radius: {scaled_border_radius}px;
    }}
    QLineEdit#keyboardTextInput {{
        font-size: {scale_value(base_font_size_pt + 2, scale_factor)}pt;
        padding: {scale_value(base_padding_px, scale_factor)}px;
        min-height: {scale_value(40, scale_factor)}px;
        border: {scaled_border}px solid #707070;
        border-radius: {scaled_border_radius}px;
        background-color: #404040;
        color: #e0e0e0;
    }}
    QPushButton#keyboardKey {{
        background-color: #505050;
        border: {scaled_border}px solid #707070;
        border-radius: {scaled_border_radius}px;
        min-width: {scale_value(40, scale_factor)}px;
        min-height: {scale_value(40, scale_factor)}px;
        font-size: {scale_value(base_font_size_pt, scale_factor)}pt;
        color: #e0e0e0;
        outline: none;
    }}
    QPushButton#keyboardKey:pressed {{
        background-color: #606060;
    }}
    QPushButton#keyboardSpecialKey {{
        background-color: #404040;
        border: {scaled_border}px solid #606060;
        border-radius: {scaled_border_radius}px;
        min-width: {scale_value(50, scale_factor)}px;
        min-height: {scale_value(40, scale_factor)}px;
        font-size: {scale_value(base_font_size_pt, scale_factor)}pt;
        color: #e0e0e0;
        outline: none;
    }}
    QPushButton#keyboardSpecialKey:pressed {{
        background-color: #505050;
    }}
    QPushButton#keyboardSpaceKey {{
        background-color: #505050;
        border: {scaled_border}px solid #707070;
        border-radius: {scaled_border_radius}px;
        min-width: {scale_value(200, scale_factor)}px;
        min-height: {scale_value(40, scale_factor)}px;
        font-size: {scale_value(base_font_size_pt, scale_factor)}pt;
        color: #e0e0e0;
        outline: none;
    }}
    QPushButton#keyboardSpaceKey:pressed {{
        background-color: #606060;
    }}

    QFileDialog {{
        background-color: #2e2e2e;
        color: #e0e0e0;
    }}
    QFileDialog QListView {{
        background-color: #404040;
        border: {scaled_border}px solid #707070;
        color: #e0e0e0;
        selection-background-color: #505050;
        selection-color: #e0e0e0;
    }}
    QFileDialog QTreeView {{
        background-color: #404040;
        border: {scaled_border}px solid #707070;
        color: #e0e0e0;
        selection-background-color: #505050;
        selection-color: #e0e0e0;
    }}
    QFileDialog QPushButton {{
        background-color: #505050;
        border: {scaled_border}px solid #707070;
        color: #e0e0e0;
        padding: {scale_value(base_padding_px * 0.6, scale_factor)}px {scale_value(base_padding_px * 1.2, scale_factor)}px;
        border-radius: {scaled_border_radius}px;
        min-height: {scaled_button_min_height}px;
        outline: none;
    }}
    QFileDialog QPushButton:pressed {{
        background-color: #606060;
    }}
    QFileDialog QLineEdit {{
        background-color: #404040;
        border: {scaled_border}px solid #707070;
        color: #e0e0e0;
        padding: {scale_value(base_padding_px * 0.6, scale_factor)}px;
        border-radius: {scaled_border_radius // 2}px;
    }}
    """


# --- apply_theme function ---
def apply_theme(app, theme_name, scale_factor=1.0):
    """Applies the selected theme stylesheet with the given scale factor."""
    print(
        f"DEBUG: apply_theme called. Theme: {theme_name}, Scale: {scale_factor:.2f}"
    )  # Debug
    if theme_name == "dark":
        # Theme function now gets base thickness from the constant
        style_sheet = get_dark_theme(scale_factor)
    else:  # Default to light
        style_sheet = get_light_theme(scale_factor)

    # Clear the existing stylesheet first to ensure clean application
    app.setStyleSheet("")
    # Apply the new stylesheet
    app.setStyleSheet(style_sheet)

    # Force style update on the application
    app.style().unpolish(app)
    app.style().polish(app)
