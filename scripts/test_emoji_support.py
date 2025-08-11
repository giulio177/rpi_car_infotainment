#!/usr/bin/env python3

"""
Test script to check emoji rendering support in Qt on Raspberry Pi OS Lite
Run this script to verify emoji fonts are working before running the main app.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtCore import Qt

class EmojiTestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Emoji Font Test")
        self.setGeometry(100, 100, 400, 300)
        
        layout = QVBoxLayout()
        
        # Test label with emoji
        self.test_label = QLabel("Testing emoji rendering:")
        layout.addWidget(self.test_label)
        
        # List available fonts
        font_db = QFontDatabase()
        available_families = font_db.families()
        
        emoji_fonts = [f for f in available_families if any(keyword in f.lower() for keyword in ['emoji', 'symbol', 'noto'])]
        
        if emoji_fonts:
            font_info = QLabel(f"Emoji fonts found: {', '.join(emoji_fonts[:3])}")
        else:
            font_info = QLabel("No emoji fonts found!")
        layout.addWidget(font_info)
        
        # Test buttons with different fonts
        test_emoji = ["💾", "🔄", "✅", "➖"]
        
        for i, emoji in enumerate(test_emoji):
            btn = QPushButton(emoji)
            btn.setFixedSize(50, 50)
            
            # Try different fonts
            if emoji_fonts:
                font = QFont(emoji_fonts[0], 20)
                btn.setFont(font)
                btn.setToolTip(f"Using font: {emoji_fonts[0]}")
            else:
                font = QFont("DejaVu Sans", 18)
                btn.setFont(font)
                btn.setToolTip("Using DejaVu Sans fallback")
            
            layout.addWidget(btn)
        
        # Test with Unicode alternatives
        unicode_label = QLabel("Unicode alternatives:")
        layout.addWidget(unicode_label)
        
        unicode_symbols = ["⬇", "↻", "✓", "−"]
        for symbol in unicode_symbols:
            btn = QPushButton(symbol)
            btn.setFixedSize(50, 50)
            font = QFont("DejaVu Sans", 20)
            btn.setFont(font)
            layout.addWidget(btn)
        
        self.setLayout(layout)

def main():
    app = QApplication(sys.argv)
    
    # Print font information
    print("=== Font Database Information ===")
    font_db = QFontDatabase()
    all_families = font_db.families()
    
    print(f"Total fonts available: {len(all_families)}")
    
    emoji_fonts = [f for f in all_families if any(keyword in f.lower() for keyword in ['emoji', 'symbol', 'noto'])]
    print(f"Emoji-related fonts: {emoji_fonts}")
    
    # Test emoji in console
    print("\n=== Console Emoji Test ===")
    test_emoji = "💾 🔄 ✅ ➖"
    print(f"Emoji test: {test_emoji}")
    
    # Create and show test window
    window = EmojiTestWindow()
    window.show()
    
    print("\n=== Instructions ===")
    print("1. Look at the test window")
    print("2. If you see emoji (not rectangles), emoji support is working")
    print("3. If you see rectangles, try installing fonts with:")
    print("   sudo bash scripts/install_emoji_fonts.sh")
    print("4. Then reboot and test again")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
