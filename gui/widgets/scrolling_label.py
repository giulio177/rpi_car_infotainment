# gui/widgets/scrolling_label.py

from PyQt6.QtWidgets import QLabel, QSizePolicy
from PyQt6.QtGui import QPainter, QFontMetrics
from PyQt6.QtCore import Qt, QTimer, pyqtProperty, QRect, QSize

class ScrollingLabel(QLabel):
    def __init__(self, parent=None, scroll_speed=50, padding=40):
        super().__init__(parent)
        self._text = ""
        self._full_text_width = 0
        self._offset = 0
        self._scroll_speed_ms = scroll_speed # Timer interval in ms
        self._padding = padding # Pixels between text repetitions

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._scroll)
        self._timer.setInterval(self._scroll_speed_ms)

        # Prevent label from expanding horizontally beyond its container
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)


    def setText(self, text):
        if self._text == text:
            return # No change

        self._text = str(text) if text is not None else ""
        self._offset = 0 # Reset scroll position
        self._update_text_width()
        self._update_timer_state()
        self.update() # Trigger repaint


    def text(self):
        return self._text


    def _update_text_width(self):
        fm = QFontMetrics(self.font())
        # Calculate width of the text using current font
        self._full_text_width = fm.horizontalAdvance(self._text)


    def _update_timer_state(self):
        # Start timer only if text width is greater than widget width
        if self._full_text_width > self.width() and self.isVisible():
            if not self._timer.isActive():
                self._timer.start()
                # print(f"Starting scroll for '{self._text}' (width {self._full_text_width} > {self.width()})")
        else:
            if self._timer.isActive():
                self._timer.stop()
                self._offset = 0 # Reset offset when stopping
                self.update() # Repaint immediately with static text
                # print(f"Stopping scroll for '{self._text}' (width {self._full_text_width} <= {self.width()})")


    def _scroll(self):
        if not self.isVisible():
            self._timer.stop()
            return

        self._offset += 1
        # Reset offset when it scrolls past the text length + padding
        if self._offset > self._full_text_width + self._padding:
            self._offset = 0
        self.update() # Trigger repaint


    def paintEvent(self, event):
        if not self._timer.isActive() or self._full_text_width <= self.width():
            # If not scrolling, use default QLabel painting centered/aligned
            # Note: Alignment needs to be set on the instance if desired
            # e.g., self.track_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            super().paintEvent(event) # Default painting
            return

        painter = QPainter(self)
        fm = painter.fontMetrics()
        widget_width = self.width()
        text_height = fm.height()
        # Calculate vertical position (simple vertical center)
        y = (self.height() - text_height) // 2 + fm.ascent()

        x = -self._offset # Start drawing from the offset

        # Draw the text - potentially twice for wrap-around effect
        while x < widget_width:
            # Calculate clipping rectangle to avoid drawing outside widget bounds
            clip_rect = QRect(max(0, x), 0, min(widget_width - x, self._full_text_width) , self.height())
            # Draw portion of the text within the clip rectangle
            # painter.setClipRect(clip_rect) # Clipping might be automatic? Test needed.
            painter.drawText(x, y, self._text)
            # painter.setClipping(False) # Disable clipping for next draw

            # Move x for the next potential draw (text + padding)
            x += self._full_text_width + self._padding

            # Optimization: If the first draw already filled the width, no need to loop
            if x >= widget_width and (x - self._full_text_width - self._padding) < 0:
                 break


    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Re-evaluate if scrolling is needed when size changes
        self._update_timer_state()


    def showEvent(self, event):
        super().showEvent(event)
        self._update_timer_state()


    def hideEvent(self, event):
        super().hideEvent(event)
        if self._timer.isActive():
            self._timer.stop()


    # Expose text property for QSS etc. (optional but good practice)
    pyqtProperty(str, text, setText)
