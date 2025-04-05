# gui/widgets/scrolling_label.py

from enum import Enum, auto
from PyQt6.QtWidgets import QLabel, QSizePolicy
from PyQt6.QtGui import QPainter, QFontMetrics
from PyQt6.QtCore import Qt, QTimer, pyqtProperty, QRect, QSize

class ScrollState(Enum):
    STATIC = auto()
    DELAYING = auto()
    SCROLLING = auto()

class ScrollingLabel(QLabel):
    def __init__(self, parent=None, scroll_speed_ms=50, delay_ms=3000, padding=40):
        super().__init__(parent)
        self._text = ""
        self._full_text_width = 0
        self._offset = 0
        self._scroll_speed_ms = scroll_speed_ms # Timer interval in ms
        self._delay_ms = delay_ms             # Delay before scrolling starts
        self._padding = padding               # Pixels between text repetitions
        self._state = ScrollState.STATIC

        # Timer for the actual scrolling movement
        self._scroll_timer = QTimer(self)
        self._scroll_timer.timeout.connect(self._scroll_step)
        self._scroll_timer.setInterval(self._scroll_speed_ms)

        # Timer for the initial delay before scrolling
        self._delay_timer = QTimer(self)
        self._delay_timer.setSingleShot(True) # Only fire once
        self._delay_timer.timeout.connect(self._start_scrolling_after_delay)

        # Prevent label from expanding horizontally beyond its container
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

    def setText(self, text):
        new_text = str(text) if text is not None else ""
        if self._text == new_text:
            return # No change

        # Stop any existing timers immediately
        self._scroll_timer.stop()
        self._delay_timer.stop()

        self._text = new_text
        self._offset = 0 # Reset scroll position
        self._state = ScrollState.STATIC # Reset state
        self._update_text_width()
        self._evaluate_scrolling() # Check if scrolling is needed and start delay if so
        self.update() # Trigger repaint


    def text(self):
        return self._text


    def _update_text_width(self):
        fm = QFontMetrics(self.font())
        # Calculate width of the text using current font
        self._full_text_width = fm.horizontalAdvance(self._text)


    def _evaluate_scrolling(self):
        """Checks if scrolling is needed and manages state/timers."""
        widget_width = self.width()

        # Check if scrolling is required
        needs_scrolling = self._full_text_width > widget_width and self.isVisible()

        if needs_scrolling:
            if self._state == ScrollState.STATIC:
                # print(f"Starting delay for '{self._text}'")
                self._state = ScrollState.DELAYING
                self._delay_timer.start(self._delay_ms)
        else:
            # Scrolling is not needed (or widget not visible)
            if self._state != ScrollState.STATIC:
                # print(f"Stopping scroll/delay for '{self._text}'")
                self._state = ScrollState.STATIC
                self._scroll_timer.stop()
                self._delay_timer.stop()
                self._offset = 0
                self.update() # Ensure static text is drawn immediately


    def _start_scrolling_after_delay(self):
        """Called when the initial delay timer finishes."""
        if self._state == ScrollState.DELAYING and self.isVisible():
            # print(f"Delay finished, starting scroll for '{self._text}'")
            self._state = ScrollState.SCROLLING
            self._scroll_timer.start()
        elif not self.isVisible(): # If hidden during delay, stop everything
             self._state = ScrollState.STATIC
             self._scroll_timer.stop()


    def _scroll_step(self):
        """Called by the scroll timer to advance the offset."""
        if self._state != ScrollState.SCROLLING or not self.isVisible():
            self._scroll_timer.stop() # Should not happen if state is managed well, but safety check
            self._state = ScrollState.STATIC
            self._offset = 0
            self.update()
            return

        self._offset += 1
        # Reset offset when it scrolls past the text length + padding
        if self._offset > self._full_text_width + self._padding:
            self._offset = 0
            # --- Optional: Re-trigger delay after one full scroll ---
            # self._state = ScrollState.DELAYING
            # self._scroll_timer.stop()
            # self._delay_timer.start(self._delay_ms)
            # --- Or just loop continuously (current behavior) ---

        self.update() # Trigger repaint


    def paintEvent(self, event):
        painter = QPainter(self)
        fm = painter.fontMetrics()
        widget_width = self.width()
        text_height = fm.height()
        y = (self.height() - text_height) // 2 + fm.ascent() # Vertical center

        if self._state != ScrollState.SCROLLING or self._full_text_width <= widget_width:
            # Paint static text (centered or aligned as per QLabel setting)
            # Use default QLabel painting which respects alignment
            super().paintEvent(event)
            return

        # --- Scrolling Paint Logic ---
        x = -self._offset # Start drawing from the calculated offset

        while x < widget_width:
            # Draw the text at the current position x
            painter.drawText(x, y, self._text)
            # Move x for the next potential draw (text + padding)
            x += self._full_text_width + self._padding
            # Optimization: If the first draw already filled the width, no need to loop
            if x >= widget_width and (x - self._full_text_width - self._padding) < 0:
                 break


    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Re-evaluate scrolling need when size changes
        self._evaluate_scrolling()


    def showEvent(self, event):
        super().showEvent(event)
        # Re-evaluate scrolling need when widget becomes visible
        self._evaluate_scrolling()


    def hideEvent(self, event):
        super().hideEvent(event)
        # Stop timers when widget is hidden
        if self._scroll_timer.isActive():
            self._scroll_timer.stop()
        if self._delay_timer.isActive():
             self._delay_timer.stop()
        self._state = ScrollState.STATIC # Reset state when hidden


    # Expose text property for QSS etc.
    pyqtProperty(str, lambda self: self.text(), self.setText)
