# gui/virtual_keyboard.py

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QGridLayout, QWidget, QLabel, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class VirtualKeyboard(QDialog):
    """Virtual keyboard for touchscreen text input."""

    def __init__(self, initial_text="", parent=None):
        super().__init__(parent)
        self.current_text = initial_text
        self.caps_lock = False
        self.shift_pressed = False

        self.setWindowTitle("Virtual Keyboard")
        self.setModal(True)
        self.resize(800, 400)

        # Apply consistent theming
        self.setObjectName("virtualKeyboard")

        self.setup_ui()
        self.text_input.setText(initial_text)
        self.text_input.setFocus()

    def setup_ui(self):
        """Setup the virtual keyboard UI."""
        layout = QVBoxLayout(self)

        # Text input area
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Text:"))

        self.text_input = QLineEdit()
        self.text_input.setObjectName("keyboardTextInput")
        font = QFont()
        font.setPointSize(14)
        self.text_input.setFont(font)
        self.text_input.textChanged.connect(self.on_text_changed)
        input_layout.addWidget(self.text_input)

        layout.addLayout(input_layout)

        # Keyboard area
        keyboard_widget = QWidget()
        keyboard_layout = QVBoxLayout(keyboard_widget)

        # Number row
        self.create_number_row(keyboard_layout)

        # Letter rows
        self.letter_buttons = []  # Store letter buttons for updating
        self.create_letter_rows(keyboard_layout)

        # Space and control row
        self.create_control_row(keyboard_layout)

        layout.addWidget(keyboard_widget)

        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.addStretch()

        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_text)
        action_layout.addWidget(clear_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        action_layout.addWidget(cancel_button)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        ok_button.setDefault(True)
        action_layout.addWidget(ok_button)

        layout.addLayout(action_layout)

    def create_number_row(self, parent_layout):
        """Create the number row."""
        number_layout = QHBoxLayout()

        numbers = "1234567890"
        symbols = "!@#$%^&*()"

        for i, (num, sym) in enumerate(zip(numbers, symbols)):
            btn = QPushButton(num)
            btn.setObjectName("keyboardKey")
            btn.clicked.connect(lambda checked, char=num, alt=sym: self.key_pressed(char, alt))
            number_layout.addWidget(btn)

        # Backspace
        backspace_btn = QPushButton("⌫")
        backspace_btn.setObjectName("keyboardSpecialKey")
        backspace_btn.clicked.connect(self.backspace)
        number_layout.addWidget(backspace_btn)

        parent_layout.addLayout(number_layout)

    def create_letter_rows(self, parent_layout):
        """Create the letter rows."""
        # Row 1: QWERTYUIOP
        row1_layout = QHBoxLayout()
        row1 = "qwertyuiop"
        row1_symbols = "QWERTYUIOP"

        for char, upper in zip(row1, row1_symbols):
            btn = QPushButton(char.upper() if self.caps_lock else char)
            btn.setObjectName("keyboardKey")
            btn.clicked.connect(lambda checked, c=char, u=upper: self.key_pressed(c, u))
            btn.char = char  # Store original character
            btn.upper = upper  # Store uppercase character
            self.letter_buttons.append(btn)
            row1_layout.addWidget(btn)

        parent_layout.addLayout(row1_layout)

        # Row 2: ASDFGHJKL
        row2_layout = QHBoxLayout()
        row2 = "asdfghjkl"
        row2_symbols = "ASDFGHJKL"

        for char, upper in zip(row2, row2_symbols):
            btn = QPushButton(char.upper() if self.caps_lock else char)
            btn.setObjectName("keyboardKey")
            btn.clicked.connect(lambda checked, c=char, u=upper: self.key_pressed(c, u))
            btn.char = char  # Store original character
            btn.upper = upper  # Store uppercase character
            self.letter_buttons.append(btn)
            row2_layout.addWidget(btn)

        parent_layout.addLayout(row2_layout)

        # Row 3: ZXCVBNM
        row3_layout = QHBoxLayout()

        # Shift key
        self.shift_btn = QPushButton("⇧")
        self.shift_btn.setObjectName("keyboardSpecialKey")
        self.shift_btn.setCheckable(True)
        self.shift_btn.clicked.connect(self.toggle_shift)
        row3_layout.addWidget(self.shift_btn)

        row3 = "zxcvbnm"
        row3_symbols = "ZXCVBNM"

        for char, upper in zip(row3, row3_symbols):
            btn = QPushButton(char.upper() if self.caps_lock else char)
            btn.setObjectName("keyboardKey")
            btn.clicked.connect(lambda checked, c=char, u=upper: self.key_pressed(c, u))
            btn.char = char  # Store original character
            btn.upper = upper  # Store uppercase character
            self.letter_buttons.append(btn)
            row3_layout.addWidget(btn)

        # Caps Lock
        self.caps_btn = QPushButton("⇪")
        self.caps_btn.setObjectName("keyboardSpecialKey")
        self.caps_btn.setCheckable(True)
        self.caps_btn.clicked.connect(self.toggle_caps)
        row3_layout.addWidget(self.caps_btn)

        parent_layout.addLayout(row3_layout)

    def create_control_row(self, parent_layout):
        """Create the control row with space and punctuation."""
        control_layout = QHBoxLayout()

        # Common punctuation
        punctuation = [
            (",", "<"), (".", ">"), ("/", "?"), (";", ":"),
            ("'", '"'), ("[", "{"), ("]", "}"), ("\\", "|"),
            ("-", "_"), ("=", "+")
        ]

        for char, alt in punctuation[:3]:  # First 3
            btn = QPushButton(char)
            btn.setObjectName("keyboardKey")
            btn.clicked.connect(lambda checked, c=char, a=alt: self.key_pressed(c, a))
            control_layout.addWidget(btn)

        # Space bar
        space_btn = QPushButton("Space")
        space_btn.setObjectName("keyboardSpaceKey")
        space_btn.clicked.connect(lambda: self.key_pressed(" "))
        control_layout.addWidget(space_btn)

        # More punctuation
        for char, alt in punctuation[3:6]:  # Next 3
            btn = QPushButton(char)
            btn.setObjectName("keyboardKey")
            btn.clicked.connect(lambda checked, c=char, a=alt: self.key_pressed(c, a))
            control_layout.addWidget(btn)

        parent_layout.addLayout(control_layout)

        # Additional symbols row
        symbols_layout = QHBoxLayout()

        for char, alt in punctuation[6:]:  # Remaining
            btn = QPushButton(char)
            btn.setObjectName("keyboardKey")
            btn.clicked.connect(lambda checked, c=char, a=alt: self.key_pressed(c, a))
            symbols_layout.addWidget(btn)

        # @ symbol for emails
        at_btn = QPushButton("@")
        at_btn.setObjectName("keyboardKey")
        at_btn.clicked.connect(lambda: self.key_pressed("@"))
        symbols_layout.addWidget(at_btn)

        parent_layout.addLayout(symbols_layout)

    def key_pressed(self, char, alt_char=None):
        """Handle key press."""
        # Determine which character to use
        if self.shift_pressed or self.caps_lock:
            if alt_char and not char.isalpha():
                # Use alt character for symbols when shift is pressed
                insert_char = alt_char if self.shift_pressed else char
            else:
                # Use uppercase for letters
                insert_char = char.upper()
        else:
            insert_char = char

        # Insert character at cursor position
        cursor_pos = self.text_input.cursorPosition()
        current_text = self.text_input.text()
        new_text = current_text[:cursor_pos] + insert_char + current_text[cursor_pos:]
        self.text_input.setText(new_text)
        self.text_input.setCursorPosition(cursor_pos + 1)

        # Reset shift if it was pressed (but not caps lock)
        if self.shift_pressed and not self.caps_lock:
            self.shift_pressed = False
            self.shift_btn.setChecked(False)
            self.update_key_labels()

    def backspace(self):
        """Handle backspace."""
        cursor_pos = self.text_input.cursorPosition()
        if cursor_pos > 0:
            current_text = self.text_input.text()
            new_text = current_text[:cursor_pos-1] + current_text[cursor_pos:]
            self.text_input.setText(new_text)
            self.text_input.setCursorPosition(cursor_pos - 1)

    def toggle_shift(self):
        """Toggle shift state."""
        self.shift_pressed = self.shift_btn.isChecked()
        self.update_key_labels()

    def toggle_caps(self):
        """Toggle caps lock state."""
        self.caps_lock = self.caps_btn.isChecked()
        self.update_key_labels()

    def update_key_labels(self):
        """Update key labels based on shift/caps state."""
        for btn in self.letter_buttons:
            if self.shift_pressed or self.caps_lock:
                btn.setText(btn.upper)
            else:
                btn.setText(btn.char)

    def clear_text(self):
        """Clear all text."""
        self.text_input.clear()

    def on_text_changed(self, text):
        """Handle text change."""
        self.current_text = text

    def get_text(self):
        """Get the current text."""
        return self.text_input.text()
