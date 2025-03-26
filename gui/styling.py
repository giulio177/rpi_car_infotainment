# Qt Style Sheets (QSS) - similar to CSS

def get_light_theme():
    return """
    QWidget {
        background-color: #f0f0f0;
        color: #333;
        font-size: 18pt; /* Base font size for touch */
    }
    QPushButton {
        background-color: #dcdcdc;
        border: 1px solid #b0b0b0;
        padding: 10px 15px;
        border-radius: 5px;
        min-height: 40px; /* Ensure buttons are tappable */
    }
    QPushButton:pressed {
        background-color: #c0c0c0;
    }
    QLabel {
        padding: 5px;
    }
    QLineEdit, QComboBox {
        background-color: white;
        border: 1px solid #b0b0b0;
        padding: 8px;
        border-radius: 3px;
    }
    /* Add specific styles for gauges, sliders etc. */
    """

def get_dark_theme():
    return """
    QWidget {
        background-color: #2e2e2e;
        color: #e0e0e0;
        font-size: 18pt;
    }
    QPushButton {
        background-color: #505050;
        border: 1px solid #707070;
        color: #e0e0e0;
        padding: 10px 15px;
        border-radius: 5px;
        min-height: 40px;
    }
    QPushButton:pressed {
        background-color: #606060;
    }
    QLabel {
        padding: 5px;
    }
    QLineEdit, QComboBox {
        background-color: #404040;
        border: 1px solid #707070;
        color: #e0e0e0;
        padding: 8px;
        border-radius: 3px;
    }
     /* Add specific styles for gauges, sliders etc. */
    """

def apply_theme(app, theme_name):
    if theme_name == "dark":
        app.setStyleSheet(get_dark_theme())
    else: # Default to light
        app.setStyleSheet(get_light_theme())