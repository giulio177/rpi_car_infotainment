"""
Symbol Manager - Centralized emoji and Unicode symbol management
Provides consistent symbol rendering across the entire application
"""

from PyQt6.QtGui import QFont, QFontDatabase, QIcon, QPixmap, QPainter, QColor, QBrush, QPen
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, QRect


class SymbolManager:
    """Manages symbols and emoji rendering across the application."""

    def __init__(self):
        self.has_emoji_fonts = None
        self.emoji_font = None
        self._initialized = False
        self._svg_icons = {}  # Cache for SVG icons
        
    def _ensure_initialized(self):
        """Lazy initialization to avoid QFontDatabase access before QApplication."""
        if self._initialized:
            return

        try:
            self.has_emoji_fonts = self._detect_emoji_fonts()
            self.emoji_font = self._get_best_emoji_font()
            self._initialized = True
        except Exception as e:
            print(f"Error initializing SymbolManager: {e}")
            self.has_emoji_fonts = False
            self.emoji_font = QFont("Arial", 18)
            self._initialized = True

    def _detect_emoji_fonts(self):
        """Detect if emoji fonts are available on the system."""
        try:
            available_families = QFontDatabase.families()
            emoji_fonts = [
                "Apple Color Emoji", "Twemoji", "EmojiOne",
                "Noto Color Emoji", "Noto Emoji", "Segoe UI Emoji"
            ]
            return any(font in available_families for font in emoji_fonts)
        except Exception as e:
            print(f"Error detecting emoji fonts: {e}")
            return False
    
    def _get_best_emoji_font(self):
        """Get the best available font for emoji rendering."""
        try:
            available_families = QFontDatabase.families()

            # Debug: Print all available fonts
            print("SymbolManager: Scanning available fonts...")
            emoji_related = [f for f in available_families if any(keyword in f.lower() for keyword in ['emoji', 'apple', 'noto', 'symbol'])]
            print(f"SymbolManager: Found emoji-related fonts: {emoji_related}")

            # Preferred emoji fonts in order (Apple FIRST - highest priority)
            emoji_fonts = [
                "Apple Color Emoji",     # 🍎 Apple's emoji font (PRIORITY #1)
                "Apple Color Emoji.ttc", # Alternative name for Apple font
                ".Apple Color Emoji",    # Hidden file variant
                "Twemoji",              # Twitter emoji (Apple-like style)
                "EmojiOne",             # JoyPixels emoji (Apple-like style)
                "Noto Color Emoji",     # Google's emoji font (fallback)
                "Noto Emoji",           # Google's monochrome emoji
                "Segoe UI Emoji",       # Microsoft's emoji font
                "Symbola"               # Fallback symbol font
            ]

            print(f"SymbolManager: Checking fonts in priority order: {emoji_fonts}")

            for font_name in emoji_fonts:
                if font_name in available_families:
                    print(f"SymbolManager: ✅ FOUND and using emoji font: {font_name}")
                    return QFont(font_name, 20)
                else:
                    print(f"SymbolManager: ❌ Font not available: {font_name}")

            # Fallback to standard font
            print("SymbolManager: ⚠️ No emoji fonts found, using DejaVu Sans fallback")
            return QFont("DejaVu Sans", 18)

        except Exception as e:
            print(f"SymbolManager: Error getting emoji font: {e}")
            return QFont("Arial", 18)
    
    def get_symbol(self, symbol_type):
        """Get the appropriate symbol based on system capabilities."""
        self._ensure_initialized()
        symbols = {
            # Media controls
            "play": ("▶️", "▶"),           # Emoji, Unicode fallback
            "pause": ("⏸️", "⏸"),         # Emoji, Unicode fallback  
            "previous": ("⏮️", "<<"),      # Emoji, Unicode fallback
            "next": ("⏭️", ">>"),          # Emoji, Unicode fallback
            
            # Settings buttons
            "save": ("💾", "⬇"),          # Emoji, Unicode fallback
            "restart": ("🔄", "↻"),       # Emoji, Unicode fallback
            "success": ("✅", "✓"),       # Emoji, Unicode fallback
            "none": ("➖", "−"),           # Emoji, Unicode fallback
            
            # Other common symbols
            "download": ("⬇️", "⬇"),      # Emoji, Unicode fallback
            "library": ("📚", "≡"),       # Emoji, Unicode fallback
            "lyrics": ("🎵", "♪"),        # Emoji, Unicode fallback
            "volume": ("🔊", "♪"),        # Emoji, Unicode fallback
            "mute": ("🔇", "✕"),          # Emoji, Unicode fallback
        }
        
        if symbol_type in symbols:
            emoji_symbol, unicode_fallback = symbols[symbol_type]
            return emoji_symbol if self.has_emoji_fonts else unicode_fallback
        
        return "?"  # Unknown symbol

    def _create_painted_icon(self, symbol_type, size=32):
        """Create a painted icon for the given symbol type using QPainter."""
        if symbol_type in self._svg_icons:
            return self._svg_icons[symbol_type]

        # Color schemes for each symbol type (more emoji-like colors)
        color_schemes = {
            "play": {"bg": QColor(52, 199, 89), "fg": QColor(255, 255, 255)},      # iOS Green
            "pause": {"bg": QColor(255, 149, 0), "fg": QColor(255, 255, 255)},     # iOS Orange
            "previous": {"bg": QColor(0, 122, 255), "fg": QColor(255, 255, 255)},  # iOS Blue
            "next": {"bg": QColor(0, 122, 255), "fg": QColor(255, 255, 255)},      # iOS Blue
            "save": {"bg": QColor(175, 82, 222), "fg": QColor(255, 255, 255)},     # iOS Purple
            "restart": {"bg": QColor(255, 69, 58), "fg": QColor(255, 255, 255)},   # iOS Red
        }

        if symbol_type not in color_schemes:
            return None

        try:
            # Create pixmap
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.GlobalColor.transparent)

            # Use context manager for safer painting
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            colors = color_schemes[symbol_type]
            bg_color = colors["bg"]
            fg_color = colors["fg"]

            # Draw background circle
            painter.setBrush(QBrush(bg_color))
            painter.setPen(QPen(bg_color.darker(120), 2))
            painter.drawEllipse(2, 2, size-4, size-4)

            # Draw symbol
            painter.setBrush(QBrush(fg_color))
            painter.setPen(QPen(fg_color, 2))

            center = size // 2

            if symbol_type == "play":
                # Draw a nice play triangle (like ▶️)
                points = [
                    (center - 5, center - 7),
                    (center - 5, center + 7),
                    (center + 8, center)
                ]
                from PyQt6.QtGui import QPolygon
                from PyQt6.QtCore import QPoint
                polygon = QPolygon([QPoint(x, y) for x, y in points])
                painter.drawPolygon(polygon)

            elif symbol_type == "pause":
                # Draw pause bars (like ⏸️)
                painter.drawRect(center - 5, center - 7, 4, 14)
                painter.drawRect(center + 1, center - 7, 4, 14)

            elif symbol_type == "previous":
                # Draw previous symbol (like ⏮️)
                painter.drawRect(center - 7, center - 7, 3, 14)
                # First triangle
                points1 = [
                    (center + 2, center - 5),
                    (center + 2, center + 5),
                    (center - 3, center)
                ]
                polygon1 = QPolygon([QPoint(x, y) for x, y in points1])
                painter.drawPolygon(polygon1)
                # Second triangle
                points2 = [
                    (center + 7, center - 5),
                    (center + 7, center + 5),
                    (center + 2, center)
                ]
                polygon2 = QPolygon([QPoint(x, y) for x, y in points2])
                painter.drawPolygon(polygon2)

            elif symbol_type == "next":
                # Draw next symbol (like ⏭️)
                painter.drawRect(center + 4, center - 7, 3, 14)
                # First triangle
                points1 = [
                    (center - 7, center - 5),
                    (center - 7, center + 5),
                    (center - 2, center)
                ]
                polygon1 = QPolygon([QPoint(x, y) for x, y in points1])
                painter.drawPolygon(polygon1)
                # Second triangle
                points2 = [
                    (center - 2, center - 5),
                    (center - 2, center + 5),
                    (center + 3, center)
                ]
                polygon2 = QPolygon([QPoint(x, y) for x, y in points2])
                painter.drawPolygon(polygon2)

            elif symbol_type == "save":
                # Draw a better floppy disk (like 💾)
                # Main body
                painter.drawRect(center - 7, center - 7, 14, 14)
                # Top notch
                painter.setBrush(QBrush(bg_color))
                painter.drawRect(center + 2, center - 7, 5, 3)
                # Label area
                painter.setBrush(QBrush(bg_color.lighter(180)))
                painter.drawRect(center - 5, center - 5, 10, 6)
                # Metal slider
                painter.setBrush(QBrush(QColor(200, 200, 200)))
                painter.drawRect(center - 3, center + 3, 6, 3)

            elif symbol_type == "restart":
                # Draw a better restart arrow (like 🔄)
                painter.setBrush(QBrush(Qt.GlobalColor.transparent))
                painter.setPen(QPen(fg_color, 4))
                # Draw circular arrow
                painter.drawArc(center - 8, center - 8, 16, 16, 45 * 16, 270 * 16)
                # Draw arrow head
                points = [
                    (center + 8, center - 3),
                    (center + 5, center - 8),
                    (center + 2, center - 5)
                ]
                from PyQt6.QtGui import QPolygon
                from PyQt6.QtCore import QPoint
                polygon = QPolygon([QPoint(x, y) for x, y in points])
                painter.setBrush(QBrush(fg_color))
                painter.setPen(QPen(fg_color, 1))
                painter.drawPolygon(polygon)

            painter.end()

            icon = QIcon(pixmap)
            self._svg_icons[symbol_type] = icon

            print(f"SymbolManager: Created painted icon for {symbol_type}")
            return icon

        except Exception as e:
            print(f"SymbolManager: Error creating painted icon for {symbol_type}: {e}")
            return None

    def setup_button_symbol(self, button, symbol_type, font_size=None):
        """Setup a button with the appropriate symbol and font."""
        self._ensure_initialized()

        # Use simple symbols that work on all systems
        emoji_map = {
            "play": "▶",
            "pause": "||",  # Simple double bars for pause
            "previous": "◀◀",  # Double left triangles
            "next": "▶▶",     # Double right triangles
            "save": "💾",
            "restart": "🔄",
            "download": "⬇"  # Download arrow
        }

        symbol = emoji_map.get(symbol_type, "?")
        button.setText(symbol)

        # Force large, visible font
        font = QFont("Arial", font_size or 28)
        font.setWeight(QFont.Weight.Bold)
        button.setFont(font)

        # Clean styling without gold
        button.setStyleSheet(f"""
            QPushButton {{
                color: white !important;
                font-size: {font_size or 24}px !important;
                font-weight: bold !important;
                background-color: transparent !important;
                border: 2px solid #606060 !important;
                border-radius: 4px !important;
                padding: 6px !important;
                text-align: center !important;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.1) !important;
                border-color: #808080 !important;
            }}
            QPushButton:pressed {{
                background-color: rgba(255, 255, 255, 0.2) !important;
            }}
        """)

        print(f"SymbolManager: Set {symbol_type} button to '{symbol}' with large font")
        return symbol
    
    def update_button_symbol(self, button, symbol_type):
        """Update an existing button's symbol."""
        self._ensure_initialized()

        # Use simple symbols that work on all systems
        emoji_map = {
            "play": "▶",
            "pause": "||",  # Simple double bars for pause
            "previous": "◀◀",  # Double left triangles
            "next": "▶▶",     # Double right triangles
            "save": "💾",
            "restart": "🔄",
            "download": "⬇"  # Download arrow
        }

        symbol = emoji_map.get(symbol_type, "?")
        button.setText(symbol)

        print(f"SymbolManager: Updated {symbol_type} button to '{symbol}'")
        return symbol


# Global instance for use across the application
symbol_manager = SymbolManager()
