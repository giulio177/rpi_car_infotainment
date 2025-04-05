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
        """
        A QLabel that scrolls its text horizontally if it exceeds the label's width.

        Args:
            parent: Parent widget.
            scroll_speed_ms: Interval in milliseconds for each scroll step. Lower is faster.
            delay_ms: Delay in milliseconds before scrolling starts after text is set.
            padding: Space in pixels between repeated text instances during scrolling.
        """
        super().__init__(parent)
        self._text = ""
        self._full_text_width = 0
        self._offset = 0
        self._scroll_speed_ms = scroll_speed_ms
        self._delay_ms = delay_ms
        self._padding = padding
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
        """Sets the text for the label and manages scrolling state."""
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
        self.update() # Trigger repaint to show new text (or start delay)


    def text(self):
        """Returns the current full text of the label."""
        return self._text


    def _update_text_width(self):
        """Calculates the pixel width of the current text based on the font."""
        fm = QFontMetrics(self.font())
        self._full_text_width = fm.horizontalAdvance(self._text)


    def _evaluate_scrolling(self):
        """Checks if scrolling is needed and manages state/timers accordingly."""
        widget_width = self.width()
        # Scrolling is required only if text is wider than the widget and widget is visible
        needs_scrolling = self._full_text_width > widget_width and self.isVisible()

        if needs_scrolling:
            # If scrolling is needed but we are currently static, start the delay phase
            if self._state == ScrollState.STATIC:
                # print(f"Starting delay for '{self._text}'") # DEBUG
                self._state = ScrollState.DELAYING
                self._delay_timer.start(self._delay_ms)
        else:
            # Scrolling is not needed (text fits, or widget hidden)
            # Stop any active timers and reset state if not already static
            if self._state != ScrollState.STATIC:
                # print(f"Stopping scroll/delay for '{self._text}'") # DEBUG
                self._state = ScrollState.STATIC
                self._scroll_timer.stop()
                self._delay_timer.stop()
                self._offset = 0
                self.update() # Ensure static text is drawn immediately


    def _start_scrolling_after_delay(self):
        """Slot connected to delay_timer timeout. Starts the scroll timer."""
        if self._state == ScrollState.DELAYING and self.isVisible():
            # print(f"Delay finished, starting scroll for '{self._text}'") # DEBUG
            self._state = ScrollState.SCROLLING
            self._scroll_timer.start()
        elif not self.isVisible(): # If hidden during delay, revert to static
             self._state = ScrollState.STATIC
             self._scroll_timer.stop()


    def _scroll_step(self):
        """Slot connected to scroll_timer timeout. Advances scroll offset."""
        if self._state != ScrollState.SCROLLING or not self.isVisible():
            self._scroll_timer.stop() # Safety check
            if self._state != ScrollState.STATIC: # Avoid redundant update if already stopped
                self._state = ScrollState.STATIC
                self._offset = 0
                self.update()
            return

        self._offset += 1
        # Reset offset when it scrolls past the text length + padding, initiating the loop
        if self._offset > self._full_text_width + self._padding:
            self._offset = 0
            # Optional: Re-introduce delay after each full scroll loop
            # self._state = ScrollState.DELAYING
            # self._scroll_timer.stop()
            # self._delay_timer.start(self._delay_ms)

        self.update() # Trigger repaint with new offset


    def paintEvent(self, event):
        """Overrides paintEvent to draw scrolling or static text."""
        painter = QPainter(self)
        fm = painter.fontMetrics()
        widget_width = self.width()
        text_height = fm.height()
        # Calculate y for vertical centering
        y = (self.height() - text_height) // 2 + fm.ascent()

        # If not scrolling or text fits, use default QLabel paint (respects alignment)
        if self._state != ScrollState.SCROLLING or self._full_text_width <= widget_width:
            super().paintEvent(event)
            return

        # --- Scrolling Paint Logic ---
        # Starting x position based on the negative offset
        x = -self._offset

        # Draw text repeatedly until it goes past the right edge of the widget
        while x < widget_width:
            painter.drawText(x, y, self._text)
            # Move x for the next repetition (full text width + padding)
            x += self._full_text_width + self._padding
            # Optimization: Stop drawing if we've already covered the widget width
            if x >= widget_width and (x - self._full_text_width - self._padding) < 0:
                 break


    def resizeEvent(self, event):
        """Handle widget resize events."""
        super().resizeEvent(event)
        # Re-calculate if scrolling is needed when size changes
        self._evaluate_scrolling()


    def showEvent(self, event):
        """Handle widget becoming visible."""
        super().showEvent(event)
        # Re-calculate if scrolling is needed when shown
        self._evaluate_scrolling()


    def hideEvent(self, event):
        """Handle widget becoming hidden."""
        super().hideEvent(event)
        # Stop timers and reset state when hidden
        if self._scroll_timer.isActive():
            self._scroll_timer.stop()
        if self._delay_timer.isActive():
             self._delay_timer.stop()
        self._state = ScrollState.STATIC


    # Expose text property for convenience (e.g., QSS)
    text_content = pyqtProperty(str, lambda self: self.text(), setText)
