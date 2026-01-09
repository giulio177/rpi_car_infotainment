import os
import subprocess
import pygame
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QSlider, QMessageBox, QWidget
)
from PyQt6.QtCore import Qt, QTimer

class AudioEditorDialog(QDialog):
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.duration = 0
        self.start_time = 0
        self.end_time = 0
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self.check_preview_end)
        
        self.setWindowTitle(f"Edit: {os.path.basename(file_path)}")
        self.resize(600, 400)
        self.setStyleSheet("""
            QDialog { background-color: #f0f0f0; }
            QLabel { font-size: 16px; color: #333; }
            QPushButton { 
                font-size: 16px; padding: 10px; 
                background-color: #ddd; border: 1px solid #bbb; border-radius: 5px;
            }
            QPushButton:pressed { background-color: #bbb; }
            QSlider::groove:horizontal { height: 10px; background: #ddd; border-radius: 5px; }
            QSlider::handle:horizontal { width: 30px; margin: -10px 0; background: #007AFF; border-radius: 15px; }
        """)
        
        self.init_audio()
        self.setup_ui()

    def init_audio(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            sound = pygame.mixer.Sound(self.file_path)
            self.duration = sound.get_length()
            self.end_time = self.duration
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load audio: {e}")
            self.reject()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Info
        layout.addWidget(QLabel(f"Editing: {os.path.basename(self.file_path)}"))
        layout.addWidget(QLabel(f"Total Duration: {self.format_time(self.duration)}"))
        
        # Start Trim Control
        layout.addWidget(QLabel("Start Time (Cut from beginning):"))
        start_layout = QHBoxLayout()
        self.start_label = QLabel("00:00")
        self.start_slider = QSlider(Qt.Orientation.Horizontal)
        self.start_slider.setRange(0, int(self.duration * 10)) # 0.1s steps
        self.start_slider.valueChanged.connect(self.on_start_changed)
        
        start_minus = QPushButton("-")
        start_minus.setFixedSize(50, 50)
        start_minus.clicked.connect(lambda: self.adjust_start(-1))
        start_plus = QPushButton("+")
        start_plus.setFixedSize(50, 50)
        start_plus.clicked.connect(lambda: self.adjust_start(1))
        
        start_layout.addWidget(start_minus)
        start_layout.addWidget(self.start_slider)
        start_layout.addWidget(start_plus)
        start_layout.addWidget(self.start_label)
        layout.addLayout(start_layout)

        # End Trim Control
        layout.addWidget(QLabel("End Time (Cut from end):"))
        end_layout = QHBoxLayout()
        self.end_label = QLabel(self.format_time(self.duration))
        self.end_slider = QSlider(Qt.Orientation.Horizontal)
        self.end_slider.setRange(0, int(self.duration * 10))
        self.end_slider.setValue(int(self.duration * 10))
        self.end_slider.valueChanged.connect(self.on_end_changed)
        
        end_minus = QPushButton("-")
        end_minus.setFixedSize(50, 50)
        end_minus.clicked.connect(lambda: self.adjust_end(-1))
        end_plus = QPushButton("+")
        end_plus.setFixedSize(50, 50)
        end_plus.clicked.connect(lambda: self.adjust_end(1))
        
        end_layout.addWidget(end_minus)
        end_layout.addWidget(self.end_slider)
        end_layout.addWidget(end_plus)
        end_layout.addWidget(self.end_label)
        layout.addLayout(end_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        
        self.preview_btn = QPushButton("Preview Trim")
        self.preview_btn.setStyleSheet("background-color: #FF9500; color: white; font-weight: bold;")
        self.preview_btn.clicked.connect(self.toggle_preview)
        
        save_btn = QPushButton("Save & Overwrite")
        save_btn.setStyleSheet("background-color: #34C759; color: white; font-weight: bold;")
        save_btn.clicked.connect(self.save_audio)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(self.preview_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def format_time(self, seconds):
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        # show tenths?
        return f"{mins:02d}:{secs:02d}"

    def on_start_changed(self, val):
        self.start_time = val / 10.0
        # Constraint: start < end
        if self.start_time >= self.end_time:
            self.start_time = max(0, self.end_time - 1.0)
            self.start_slider.blockSignals(True)
            self.start_slider.setValue(int(self.start_time * 10))
            self.start_slider.blockSignals(False)
            
        self.start_label.setText(self.format_time(self.start_time))

    def on_end_changed(self, val):
        self.end_time = val / 10.0
        # Constraint: end > start
        if self.end_time <= self.start_time:
            self.end_time = min(self.duration, self.start_time + 1.0)
            self.end_slider.blockSignals(True)
            self.end_slider.setValue(int(self.end_time * 10))
            self.end_slider.blockSignals(False)
            
        self.end_label.setText(self.format_time(self.end_time))

    def adjust_start(self, seconds):
        new_val = self.start_slider.value() + int(seconds * 10)
        self.start_slider.setValue(new_val)

    def adjust_end(self, seconds):
        new_val = self.end_slider.value() + int(seconds * 10)
        self.end_slider.setValue(new_val)

    def toggle_preview(self):
        if pygame.mixer.music.get_busy() and self.preview_btn.text() == "Stop Preview":
            pygame.mixer.music.stop()
            self.preview_timer.stop()
            self.preview_btn.setText("Preview Trim")
        else:
            try:
                # Play from start_time
                pygame.mixer.music.load(self.file_path)
                pygame.mixer.music.play(start=self.start_time)
                self.preview_btn.setText("Stop Preview")
                
                # Set timer to stop at end_time
                duration_ms = int((self.end_time - self.start_time) * 1000)
                if duration_ms > 0:
                    self.preview_timer.start(duration_ms)
                else:
                    self.check_preview_end()
            except Exception as e:
                print(f"Preview error: {e}")

    def check_preview_end(self):
        pygame.mixer.music.stop()
        self.preview_timer.stop()
        self.preview_btn.setText("Preview Trim")

    def save_audio(self):
        # Stop preview
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            
        # Confirm
        if QMessageBox.question(self, "Confirm", "Overwrite original file? This cannot be undone.") != QMessageBox.StandardButton.Yes:
            return
            
        temp_file = self.file_path + ".temp" + os.path.splitext(self.file_path)[1]
        
        try:
            # Unload file from pygame so we can overwrite it
            pygame.mixer.music.unload() 
        except:
            pass # Some pygame versions don't have unload, but load(None) works or just stop.
            # Actually pygame mixer keeps file open? `music.load` keeps it open.
            # We must verify if we can overwrite.
            # Using temp file and then os.replace works on Linux (atomic rename).
            pass

        try:
            # We use re-encoding to ensure precise cuts, especially for MP3s where copy might be inaccurate at frames.
            # -ss before -i is faster seeking
            cmd = [
                "ffmpeg", "-y",
                "-i", self.file_path,
                "-ss", str(self.start_time),
                "-to", str(self.end_time),
                "-c:a", "libmp3lame" if self.file_path.lower().endswith(".mp3") else "copy",
                temp_file
            ]
            
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Replace
            os.replace(temp_file, self.file_path)
            
            QMessageBox.information(self, "Success", "File saved.")
            self.accept()
            
        except subprocess.CalledProcessError:
            QMessageBox.critical(self, "Error", "Processing failed. Is FFmpeg installed?")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
