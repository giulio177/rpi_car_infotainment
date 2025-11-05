#!/usr/bin/env python3
"""
Test script to verify UI layout changes
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from backend.settings_manager import SettingsManager
from gui.main_window import MainWindow

def test_bottom_bar_layout():
    """Test that Bluetooth and WiFi buttons are positioned next to audio controls"""
    print("🔍 Testing Bottom Bar Layout")
    print("=" * 50)

    # Set platform to offscreen for headless testing
    os.environ["QT_QPA_PLATFORM"] = "offscreen"

    # Create application
    app = QApplication(sys.argv)

    # Create settings manager
    config_path = project_root / 'config.json'
    settings_manager = SettingsManager(str(config_path))

    # Create main window
    main_win = MainWindow(settings_manager)
    main_win.resize(1024, 600)

    # Get bottom bar layout
    bottom_bar_layout = main_win.bottom_bar_layout

    # Get widgets in order
    widgets = []
    for i in range(bottom_bar_layout.count()):
        item = bottom_bar_layout.itemAt(i)
        if item.widget():
            widget = item.widget()
            object_name = widget.objectName()
            if object_name:
                widgets.append(object_name)
        elif item.spacerItem():
            widgets.append("SPACER")

    print("Bottom bar layout order:")
    for i, widget in enumerate(widgets):
        print(f"  {i+1}. {widget}")

    # Expected order after our changes:
    # 1. homeNavButton
    # 2. settingsNavButton
    # 3. SPACER
    # 4. volumeIcon
    # 5. volumeSlider
    # 6. bluetoothNavButton
    # 7. wifiNavButton
    # 8. SPACER
    # 9. restartNavButton
    # 10. powerNavButton

    expected_order = [
        "homeNavButton",
        "settingsNavButton",
        "SPACER",
        "volumeIcon",
        "volumeSlider",
        "bluetoothNavButton",
        "wifiNavButton",
        "SPACER",
        "restartNavButton",
        "powerNavButton"
    ]

    print("\nExpected order:")
    for i, widget in enumerate(expected_order):
        print(f"  {i+1}. {widget}")

    # Check if layout matches expected order
    layout_correct = widgets == expected_order

    if layout_correct:
        print("\n✅ PASS: Bottom bar layout is correct!")
        print("   Bluetooth and WiFi buttons are positioned next to audio controls")
    else:
        print("\n❌ FAIL: Bottom bar layout does not match expected order")
        print("   Expected:", expected_order)
        print("   Actual:  ", widgets)

    # Check specific positioning
    try:
        volume_slider_index = widgets.index("volumeSlider")
        bluetooth_index = widgets.index("bluetoothNavButton")
        wifi_index = widgets.index("wifiNavButton")

        if bluetooth_index == volume_slider_index + 1 and wifi_index == volume_slider_index + 2:
            print("✅ PASS: Bluetooth and WiFi buttons are immediately after volume slider")
        else:
            print("❌ FAIL: Bluetooth and WiFi buttons are not positioned correctly after volume slider")
            layout_correct = False

    except ValueError as e:
        print(f"❌ FAIL: Could not find required widgets: {e}")
        layout_correct = False

    app.quit()
    return layout_correct

def main():
    """Run layout tests"""
    print("🧪 RPi Car Infotainment UI Layout Tests")
    print("=" * 60)

    try:
        layout_test_passed = test_bottom_bar_layout()

        print("\n" + "=" * 60)
        if layout_test_passed:
            print("🎉 All layout tests passed!")
            print("   The UI changes have been successfully applied.")
            return 0
        else:
            print("⚠️  Layout tests failed!")
            print("   Please check the bottom bar layout configuration.")
            return 1

    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
