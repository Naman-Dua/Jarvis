import sys
import os
import math
import random
import time
import psutil
from html import escape
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QGraphicsDropShadowEffect, QTextEdit,
    QLineEdit, QPushButton, QSizePolicy, QFrame,
    QSystemTrayIcon, QMenu, QScrollArea, QTabWidget,
    QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRectF, QEvent, QPoint, QEasingCurve, QPropertyAnimation
from PyQt6.QtGui import QPainter, QColor, QFont, QPainterPath, QRadialGradient, QPen, QTextCursor, QIcon, QAction, QPixmap, QBrush, QLinearGradient, QShortcut, QKeySequence
from themes import get_active_theme
from datetime import datetime

# ══════════════════════════════════════════════════════════════════════════════
#  SETTINGS DIALOG
# ══════════════════════════════════════════════════════════════════════════════
from settings import load_settings, save_settings
from PyQt6.QtWidgets import QDialog, QGridLayout, QCheckBox, QComboBox, QFormLayout, QDialogButtonBox

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kora Settings")
        self.setFixedSize(460, 460)
        self.theme = get_active_theme()
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme.get('main_bg', '#0f1423')}; color: white; }}
            QLabel {{ color: white; font-family: Outfit; font-size: 14px; }}
            QCheckBox {{ color: white; font-family: Outfit; }}
            QComboBox {{ background: #1a2235; color: white; border: 1px solid {self.theme['border']}; border-radius: 5px; padding: 5px; }}
            QPushButton {{ background: {self.theme['accent']}; color: black; border-radius: 5px; padding: 5px 15px; font-weight: bold; }}
            QPushButton:hover {{ background: #ffffff; }}
        """)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.settings = load_settings()
        
        self.wake_word_cb = QCheckBox("Enable Wake Word")
        self.wake_word_cb.setChecked(self.settings.get("enable_wake_word", False))
        
        self.speak_replies_cb = QCheckBox("Speak Text Replies")
        self.speak_replies_cb.setChecked(self.settings.get("speak_text_replies", False))
        
        self.confirmations_cb = QCheckBox("Require Action Confirmations")
        self.confirmations_cb.setChecked(self.settings.get("require_action_confirmation", True))

        self.live_eye_cb = QCheckBox("Enable Proactive Live Eye")
        self.live_eye_cb.setChecked(self.settings.get("enable_live_eye", False))

        self.routing_cb = QCheckBox("Enable Multi-Model Routing")
        self.routing_cb.setChecked(self.settings.get("enable_model_routing", True))
        
        self.model_combo = QComboBox()
        self.model_combo.addItems(["llama3.1:8b", "llama3:latest", "mistral:latest", "phi3:latest"])
        self.model_combo.setCurrentText(self.settings.get("model_name", "llama3.1:8b"))

        self.fast_model_combo = QComboBox()
        self.fast_model_combo.addItems(["llama3.1:8b", "llama3:latest", "mistral:latest", "phi3:latest"])
        self.fast_model_combo.setCurrentText(self.settings.get("fast_model_name", self.settings.get("model_name", "llama3.1:8b")))

        self.deep_model_combo = QComboBox()
        self.deep_model_combo.addItems(["llama3.1:8b", "llama3:latest", "mistral:latest", "phi3:latest"])
        self.deep_model_combo.setCurrentText(self.settings.get("deep_model_name", self.settings.get("model_name", "llama3.1:8b")))
        
        from themes import THEMES
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        from themes import load_setting
        self.theme_combo.setCurrentText(load_setting("active_theme", "neon"))
        
        form.addRow(self.wake_word_cb)
        form.addRow(self.speak_replies_cb)
        form.addRow(self.confirmations_cb)
        form.addRow(self.live_eye_cb)
        form.addRow(self.routing_cb)
        form.addRow("Default Model:", self.model_combo)
        form.addRow("Fast Model:", self.fast_model_combo)
        form.addRow("Deep Model:", self.deep_model_combo)
        form.addRow("Theme:", self.theme_combo)
        
        layout.addLayout(form)
        
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(self.save_and_close)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def save_and_close(self):
        updates = {
            "enable_wake_word": self.wake_word_cb.isChecked(),
            "speak_text_replies": self.speak_replies_cb.isChecked(),
            "require_action_confirmation": self.confirmations_cb.isChecked(),
            "enable_live_eye": self.live_eye_cb.isChecked(),
            "enable_model_routing": self.routing_cb.isChecked(),
            "model_name": self.model_combo.currentText(),
            "fast_model_name": self.fast_model_combo.currentText(),
            "deep_model_name": self.deep_model_combo.currentText(),
        }
        save_settings(updates)
        from storage import save_setting
        save_setting("active_theme", self.theme_combo.currentText())
        self.accept()


class CommandPalette(QDialog):
    COMMANDS = [
        ("Memory Summary", "what do you remember about me"),
        ("Game Mode On", "game mode on"),
        ("Pick Entertainment", "pick something fun"),
        ("Auto Debug", "auto-debug"),
        ("Auto Debug Mode On", "auto-debug mode on"),
        ("Knowledge Packs", "list offline knowledge packs"),
        ("Ingest Knowledge Packs", "ingest all knowledge packs"),
        ("List Plugins", "list plugins"),
        ("List Tasks", "show tasks"),
        ("Analyze Screen", "analyze screen"),
        ("Morning Briefing", "morning briefing"),
        ("System Status", "system status"),
        ("Sleep Mode", "go to sleep"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_dashboard = parent
        self.setWindowTitle("Command Palette")
        self.setFixedSize(520, 420)
        theme = get_active_theme()
        self.setStyleSheet(f"""
            QDialog {{ background: #0a0f1e; color: #ffffff; }}
            QLineEdit {{
                background: #111a2e;
                border: 1px solid {theme['border']};
                border-radius: 10px;
                padding: 10px 14px;
                color: #ffffff;
                font-size: 14px;
            }}
            QListWidget {{
                background: rgba(255, 255, 255, 6);
                border: 1px solid {theme['border']};
                border-radius: 12px;
                color: #dbe7f5;
                padding: 8px;
            }}
            QListWidget::item {{ padding: 10px; border-radius: 8px; }}
            QListWidget::item:selected {{ background: {theme['accent']}; color: #061018; }}
        """)
        layout = QVBoxLayout(self)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Type a command...")
        self.list_widget = QListWidget()
        layout.addWidget(self.search)
        layout.addWidget(self.list_widget)
        self.search.textChanged.connect(self._populate)
        self.search.returnPressed.connect(self._submit)
        self.list_widget.itemDoubleClicked.connect(lambda _: self._submit())
        self._populate("")

    def _populate(self, query):
        self.list_widget.clear()
        q = str(query).lower().strip()
        for title, command in self.COMMANDS:
            if not q or q in title.lower() or q in command.lower():
                item = QListWidgetItem(f"{title}  -  {command}")
                item.setData(Qt.ItemDataRole.UserRole, command)
                self.list_widget.addItem(item)
        if self.list_widget.count():
            self.list_widget.setCurrentRow(0)

    def _submit(self):
        item = self.list_widget.currentItem()
        command = item.data(Qt.ItemDataRole.UserRole) if item else self.search.text().strip()
        if command and self.parent_dashboard:
            self.parent_dashboard.text_input_signal.emit(command)
        self.accept()

# ══════════════════════════════════════════════════════════════════════════════
#  PREMIUM DYNAMIC BACKGROUND (Nebula)
# ══════════════════════════════════════════════════════════════════════════════

class KoraNebulaBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.points = []
        for _ in range(3):
            self.points.append({
                "x": random.random(),
                "y": random.random(),
                "vx": (random.random() - 0.5) * 0.0002, # Slower, smoother velocity
                "vy": (random.random() - 0.5) * 0.0002,
                "size": 200 + random.random() * 200,
                "opacity": 0.04 + random.random() * 0.04
            })
        
        self.theme = get_active_theme()
        self.accent = QColor(self.theme['accent'])
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_nebula)
        self.timer.start(50)
        
        self.is_processing = False

    def _update_nebula(self):
        for p in self.points:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            if p["x"] < 0 or p["x"] > 1: p["vx"] *= -1
            if p["y"] < 0 or p["y"] > 1: p["vy"] *= -1
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        w, h = self.width(), self.height()
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Screen)
        
        for pt in self.points:
            px, py = pt["x"] * w, pt["y"] * h
            grad = QRadialGradient(px, py, pt["size"])
            c = self.accent
            grad.setColorAt(0, QColor(c.red(), c.green(), c.blue(), int(pt["opacity"] * 255)))
            grad.setColorAt(1, QColor(0, 0, 0, 0))
            p.setBrush(grad)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(int(px - pt["size"]), int(py - pt["size"]), int(pt["size"] * 2), int(pt["size"] * 2))
            
        # 2. Holographic Scanlines & Glitch
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        
        # Digital Flicker if processing
        if self.is_processing and random.random() > 0.8:
            p.setBrush(QColor(255, 255, 255, 10))
            p.drawRect(self.rect())

        p.setPen(QColor(255, 255, 255, 5))
        for y in range(0, h, 4):
            p.drawLine(0, y, w, y)


# ══════════════════════════════════════════════════════════════════════════════
#  SYSTEM HUD COMPONENTS
# ══════════════════════════════════════════════════════════════════════════════

class StatusIndicator(QWidget):
    def __init__(self, label, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 80)
        self.label = label
        self.active = False
        self.glow_phase = 0.0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(16) # Smooth 60fps pulse

    def _tick(self):
        if self.active:
            self.glow_phase += 0.1
            self.update()

    def set_active(self, state):
        if self.active != state:
            self.active = state
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        accent = QColor(get_active_theme()["accent"])
        base_color = accent if self.active else QColor(80, 90, 110, 100)
        
        # Glow (Smoother pulsing)
        if self.active:
            alpha = int(120 + math.sin(self.glow_phase) * 60)
            glow = QRadialGradient(30, 30, 28)
            glow.setColorAt(0, QColor(accent.red(), accent.green(), accent.blue(), alpha))
            glow.setColorAt(1, QColor(0, 0, 0, 0))
            p.setBrush(glow)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(2, 2, 56, 56)
            
        # Icon Circle (Premium Ring)
        pen = QPen(base_color, 1.5)
        if not self.active:
            pen.setStyle(Qt.PenStyle.DashLine)
        p.setPen(pen)
        p.setBrush(QColor(255, 255, 255, 5))
        p.drawEllipse(15, 15, 30, 30)
        
        # Text
        p.setPen(base_color)
        p.setFont(QFont("Outfit", 8, QFont.Weight.Bold))
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter, self.label)


class SystemHudWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(220)
        self.setFixedWidth(340)
        theme = get_active_theme()
        self.setStyleSheet(f"""
            QFrame {{
                background: rgba(10, 15, 30, 180);
                border: 1px solid {theme['border']};
                border-radius: 24px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("MISSION STATUS")
        title.setFont(QFont("Outfit", 10, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {theme['accent']}; letter-spacing: 2px;")
        layout.addWidget(title)
        
        # Module indicators
        icons_row = QHBoxLayout()
        self.brain_ic = StatusIndicator("BRAIN")
        self.eye_ic   = StatusIndicator("EYE")
        self.ear_ic   = StatusIndicator("EARS")
        icons_row.addWidget(self.brain_ic)
        icons_row.addWidget(self.eye_ic)
        icons_row.addWidget(self.ear_ic)
        layout.addLayout(icons_row)
        
        # Bars
        self.cpu_bar = self._create_bar("CPU LOAD")
        self.ram_bar = self._create_bar("RAM USAGE")
        layout.addLayout(self.cpu_bar["layout"])
        layout.addLayout(self.ram_bar["layout"])
        
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._refresh)
        self.update_timer.start(1000)

    def _create_bar(self, label):
        l = QVBoxLayout()
        txt = QLabel(label)
        txt.setStyleSheet("color: #5c6b8c; font-size: 9px; font-weight: bold;")
        bar_bg = QFrame()
        bar_bg.setFixedHeight(6)
        bar_bg.setStyleSheet("background: rgba(255,255,255,10); border-radius: 3px; border: none;")
        fill = QFrame(bar_bg)
        fill.setFixedHeight(6)
        accent = get_active_theme()["accent"]
        fill.setStyleSheet(f"background: {accent}; border-radius: 3px; border: none;")
        fill.setFixedWidth(0)
        
        anim = QPropertyAnimation(fill, b"minimumWidth")
        anim.setDuration(600)
        anim.setEasingCurve(QEasingCurve.Type.OutExpo)
        
        l.addWidget(txt)
        l.addWidget(bar_bg)
        return {"layout": l, "fill": fill, "width": 300, "anim": anim}

    def _refresh(self):
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        
        self.cpu_bar["anim"].setEndValue(int(3.0 * cpu))
        self.cpu_bar["anim"].start()
        
        self.ram_bar["anim"].setEndValue(int(3.0 * ram))
        self.ram_bar["anim"].start()
        
    def set_module_states(self, brain=False, eye=False, ears=False):
        self.brain_ic.set_active(brain)
        self.eye_ic.set_active(eye)
        self.ear_ic.set_active(ears)


# ══════════════════════════════════════════════════════════════════════════════
#  PREMIUM KORA ORB (Visual Personality)
# ══════════════════════════════════════════════════════════════════════════════

class ParticlePoint:
    def __init__(self, x, y, z):
        self.base_x = x
        self.base_y = y
        self.base_z = z
        self.noise_offset = random.random() * 100
        self.size_mult = 1.0 + random.random() * 0.8
        self.speed_mult = 0.5 + random.random() * 1.5


class KoraSphereWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(400, 400)
        self.setMouseTracking(True)
        
        self.phase  = 0.0
        self.rot_x  = 0.0
        self.rot_y  = 0.0
        self.state  = "IDLE"
        self.vibration = 0.0
        self.pulse_scale = 1.0
        self.amplitude = 0.0 # Virtual audio amplitude
        
        # Mouse interaction
        self.mouse_target = QPoint(200, 200)
        self.mouse_current = QPoint(200, 200)
        
        # Sentiment-based colors
        theme = get_active_theme()
        self.base_color = QColor(theme["accent"])
        self.current_color = QColor(self.base_color)
        self.target_color = QColor(self.base_color)
        self.color_lerp = 1.0

        self.particles = []
        n = 360
        phi = math.pi * (3.0 - math.sqrt(5.0))
        for i in range(n):
            y = 1 - (i / float(n - 1)) * 2
            r = math.sqrt(max(0, 1 - y * y))
            t = phi * i
            self.particles.append(ParticlePoint(math.cos(t) * r, y, math.sin(t) * r))

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(33)

    def _tick(self):
        self.phase += 0.025
        
        # Smooth mouse movement
        dx = (self.mouse_target.x() - self.mouse_current.x()) * 0.1
        dy = (self.mouse_target.y() - self.mouse_current.y()) * 0.1
        self.mouse_current += QPoint(int(dx), int(dy))

        # State-based logic
        if self.state == "PROCESSING":
            speed_y, speed_x = 0.075, 0.04
            self.vibration = 3.0
            self.amplitude = 0.3 + abs(math.sin(self.phase * 8)) * 0.4
        elif self.state == "SPEAKING":
            speed_y, speed_x = 0.025, 0.01
            self.vibration = 1.0
            # Simulate speech amplitude
            self.amplitude = 0.2 + abs(math.sin(self.phase * 24)) * 0.8
        elif self.state == "LISTENING":
            speed_y, speed_x = 0.01, 0.005
            self.vibration = 0.5
            self.amplitude = 0.1 + abs(math.sin(self.phase * 16)) * 0.5
        else:
            speed_y, speed_x = 0.005, 0.0025
            self.vibration = 0.0
            self.amplitude = 0.0

        self.rot_y -= speed_y
        self.rot_x += speed_x
        
        # Breathing pulse
        idle_pulse = 1.0 + math.sin(self.phase * 0.5) * 0.03
        active_pulse = 1.0 + self.amplitude * 0.15
        self.pulse_scale = active_pulse if self.state != "IDLE" else idle_pulse
        
        # Color lerping
        if self.color_lerp < 1.0:
            self.color_lerp += 0.03
            r = int(self.current_color.red() + (self.target_color.red() - self.current_color.red()) * self.color_lerp)
            g = int(self.current_color.green() + (self.target_color.green() - self.current_color.green()) * self.color_lerp)
            b = int(self.current_color.blue() + (self.target_color.blue() - self.current_color.blue()) * self.color_lerp)
            self.current_color = QColor(r, g, b)
            if self.color_lerp >= 1.0:
                self.current_color = QColor(self.target_color)

        self.update()

    def mouseMoveEvent(self, event):
        self.mouse_target = event.position().toPoint()

    def leaveEvent(self, event):
        self.mouse_target = QPoint(200, 200)

    def set_mood(self, mood):
        moods = {
            "IDLE":      self.base_color,
            "POSITIVE":  QColor("#ff00ff"), # Pink
            "NEGATIVE":  QColor("#ff4444"), # Red
            "URGENT":    QColor("#ffaa00"), # Orange
            "PROCESSING": QColor("#00ffcc"), # Teal/Green
        }
        new_color = moods.get(mood.upper(), self.base_color)
        if new_color != self.target_color:
            self.current_color = QColor(self.target_color)
            self.target_color = QColor(new_color)
            self.color_lerp = 0.0

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx, cy = 200, 200
        # Offset center slightly by mouse position for parallax
        mx = (self.mouse_current.x() - 200) * 0.05
        my = (self.mouse_current.y() - 200) * 0.05
        cx += mx
        cy += my

        base_r = 115 * self.pulse_scale
        accent = self.current_color
        
        # 1. Background Nebula (Simplified)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Screen)
        glow_r = base_r * 2.2
        g = QRadialGradient(cx, cy, glow_r)
        g.setColorAt(0, QColor(accent.red(), accent.green(), accent.blue(), 40))
        g.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(g)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(int(cx - glow_r), int(cy - glow_r), int(glow_r * 2), int(glow_r * 2))

        # 2. The Core Heart
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        core_r = base_r * (0.35 + self.amplitude * 0.1)
        core_grad = QRadialGradient(cx, cy, core_r)
        core_grad.setColorAt(0, QColor(255, 255, 255, 180))
        core_grad.setColorAt(1, QColor(accent.red(), accent.green(), accent.blue(), 0))
        p.setBrush(core_grad)
        p.drawEllipse(int(cx - core_r), int(cy - core_r), int(core_r * 2), int(core_r * 2))

        # 3. Dynamic Arcs (Waveform Ring - Simplified)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Screen)
        ring_r = base_r * 1.45
        pen = QPen(QColor(accent.red(), accent.green(), accent.blue(), 140))
        pen.setWidthF(2.0 + self.amplitude * 2)
        p.setPen(pen)
        start_ang = int((math.degrees(self.phase * 0.6)) % 360 * 16)
        span_ang = int((60 + self.amplitude * 100) * 16)
        p.drawArc(int(cx - ring_r), int(cy - ring_r), int(ring_r * 2), int(ring_r * 2), start_ang, span_ang)
        p.drawArc(int(cx - ring_r), int(cy - ring_r), int(ring_r * 2), int(ring_r * 2), start_ang + 180 * 16, span_ang)

        # 4. 3D Particles (Simplified rendering)
        cos_x, sin_x = math.cos(self.rot_x), math.sin(self.rot_x)
        cos_y, sin_y = math.cos(self.rot_y), math.sin(self.rot_y)
        
        proj = []
        for pt in self.particles:
            # Noise + Vibration
            nx = (math.sin(self.phase * 5 + pt.noise_offset) * self.vibration)
            ny = (math.cos(self.phase * 7 + pt.noise_offset) * self.vibration)
            
            sx = pt.base_x * base_r + nx
            sy = pt.base_y * base_r + ny
            sz = pt.base_z * base_r
            
            # Rotation
            y1 = sy * cos_x - sz * sin_x
            z1 = sy * sin_x + sz * cos_x
            x2 = sx * cos_y + z1 * sin_y
            z2 = -sx * sin_y + z1 * cos_y
            
            proj.append((cx + x2, cy + y1, z2, pt.size_mult))

        proj.sort(key=lambda q: q[2])
        p.setPen(Qt.PenStyle.NoPen)
        for px, py, dz, sm in proj:
            # Depth-based visuals
            depth = (dz + base_r) / (base_r * 2) 
            alpha = int(30 + 225 * depth)
            size = (1.1 + depth * 2.2) * sm
            
            # Glint effect for front particles
            if depth > 0.8:
                p.setBrush(QColor(255, 255, 255, alpha))
            else:
                p.setBrush(QColor(accent.red(), accent.green(), accent.blue(), alpha))
                
            p.drawEllipse(QRectF(px - size/2, py - size/2, size, size))



# ══════════════════════════════════════════════════════════════════════════════
#  MODERN LOG VIEW (Rich Chat)
# ══════════════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════════
#  THINKING INDICATOR
# ══════════════════════════════════════════════════════════════════════════════

class ThinkingIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(100, 30)
        self.dots = [0.0, 0.0, 0.0]
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(70)
        self.phase = 0.0
        self.hide()

    def _animate(self):
        self.phase += 0.2
        for i in range(3):
            self.dots[i] = (math.sin(self.phase + i * 1.5) + 1) / 2
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        accent = QColor(get_active_theme()["accent"])
        for i in range(3):
            size = 6 + self.dots[i] * 4
            alpha = int(100 + self.dots[i] * 155)
            p.setBrush(QColor(accent.red(), accent.green(), accent.blue(), alpha))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(int(10 + i * 25), int(15 - size/2), int(size), int(size))


class KoraDashboard(QMainWindow):
    status_signal      = pyqtSignal(str)
    log_signal         = pyqtSignal(str, str)
    text_input_signal  = pyqtSignal(str)
    mood_signal        = pyqtSignal(str)
    telemetry_signal   = pyqtSignal(dict)
    re_enable_input_signal = pyqtSignal()

    LOG_COLORS = {
        "USER":         "#ffffff",
        "KORA":         "#00d2ff",
        "SYSTEM":       "#5c6b8c",
        "SYSTEM ERROR": "#ff5555",
        "REMINDER":     "#ffbb33",
    }

    def __init__(self, input_mode: str = "both"):
        super().__init__()
        self.input_mode = input_mode
        self.setWindowTitle("KORA")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(60, 60, 1040, 700) # Slightly larger for shadow
        self._drag_pos = QPoint()
        self.overlay_mode = False
        self._normal_geometry = None
        self.theme = get_active_theme()

        # Main background frame
        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("MainFrame")
        self.main_frame.setGeometry(20, 20, 1000, 660)
        
        # Window Shadow
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(40)
        self.shadow.setColor(QColor(0, 0, 0, 150))
        self.shadow.setOffset(0, 5)
        self.main_frame.setGraphicsEffect(self.shadow)
        
        # Subtle gradient background for the whole app
        self.main_frame.setStyleSheet(f"""
            #MainFrame {{
                background-color: {self.theme['main_bg']};
                border: 1px solid {self.theme['border']};
                border-radius: 32px;
            }}
        """)

        # Add Nebula Background as the bottom layer
        self.nebula = KoraNebulaBackground(self.main_frame)
        self.nebula.setGeometry(0, 0, 1000, 660)
        self.nebula.lower()

        layout_container = QVBoxLayout(self.main_frame)
        layout_container.setContentsMargins(0, 0, 0, 0)
        layout_container.setSpacing(0)

        # ── HEADER ────────────────────────────────────────────────────────────
        self.header = QFrame()
        self.header.setFixedHeight(60)
        self.header.setObjectName("Header")
        self.header.setStyleSheet(f"""
            #Header {{
                background: rgba(15, 20, 35, 120);
                border-bottom: 1px solid {self.theme['border']};
                border-top-left-radius: 32px;
                border-top-right-radius: 32px;
            }}
        """)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(30, 0, 20, 0)

        title_label = QLabel("KORA AI")
        tf = QFont("Outfit", 12, QFont.Weight.Bold)
        tf.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 4)
        title_label.setFont(tf)
        title_label.setStyleSheet(f"color: {self.theme['accent']};")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        self.min_btn = QPushButton("—")
        self.min_btn.setFixedSize(32, 32)
        self.min_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.min_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 10);
                color: #8899aa;
                font-weight: bold;
                border-radius: 16px;
                border: none;
            }
            QPushButton:hover { background: rgba(255, 255, 255, 20); color: white; }
        """)
        self.min_btn.clicked.connect(self._enter_overlay)
        header_layout.addWidget(self.min_btn)

        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(32, 32)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 10);
                color: #8899aa;
                font-weight: bold;
                border-radius: 16px;
                border: none;
            }
            QPushButton:hover { background: #551122; color: #ff5577; }
        """)
        self.close_btn.clicked.connect(self._close_app)
        header_layout.addWidget(self.close_btn)

        layout_container.addWidget(self.header)

        # ── CONTENT ───────────────────────────────────────────────────────────
        content_wrap = QWidget()
        root = QHBoxLayout(content_wrap)
        root.setContentsMargins(25, 20, 25, 25)
        root.setSpacing(25)

        # ── LEFT: Sphere + Info ───────────────────────────────────────────────
        left = QWidget()
        left.setFixedWidth(380)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(15)

        self.sphere_core = KoraSphereWidget()
        left_layout.addWidget(self.sphere_core, alignment=Qt.AlignmentFlag.AlignCenter)

        self.status_label = QLabel("SYSTEM ONLINE")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sf = QFont("Outfit", 14, QFont.Weight.Bold)
        sf.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 6)
        self.status_label.setFont(sf)
        self.status_label.setStyleSheet(f"color: {self.theme['accent']}; background: transparent;")
        left_layout.addWidget(self.status_label)

        self.mode_label = QLabel(self._get_mode_text())
        self.mode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mf = QFont("Outfit", 10)
        self.mode_label.setFont(mf)
        self.mode_label.setStyleSheet("color: #6a7b9c; background: transparent;")
        left_layout.addWidget(self.mode_label)
        
        left_layout.addStretch()
        
        left_layout.addStretch()
        
        # New System HUD
        self.hud_widget = SystemHudWidget()
        left_layout.addWidget(self.hud_widget)

        root.addWidget(left)

        # ── RIGHT: Chat ───────────────────────────────────────────────────────
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(15)

        self.workspace_tabs = QTabWidget()
        self.workspace_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {self.theme['border']};
                border-radius: 20px;
                background: rgba(6, 8, 14, 120);
            }}
            QTabBar::tab {{
                background: rgba(255,255,255,8);
                color: #8fa4bd;
                padding: 9px 14px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 4px;
                font-weight: 700;
                font-size: 11px;
            }}
            QTabBar::tab:selected {{
                background: {self.theme['accent']};
                color: #061018;
            }}
        """)

        chat_tab = QWidget()
        chat_layout = QVBoxLayout(chat_tab)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(8)

        # Log View
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.theme['log_bg']};
                border: 1px solid {self.theme['border']};
                border-radius: 24px;
                padding: 20px;
                color: #e0e6f0;
                font-family: 'Inter', sans-serif;
                font-size: 14px;
                selection-background-color: {self.theme['accent']};
                selection-color: #000;
            }}
            QScrollBar:vertical {{
                background: transparent; width: 6px;
                margin: 10px 4px 10px 0;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(255, 255, 255, 20); border-radius: 3px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {self.theme['accent']};
            }}
        """)

        # Thinking Indicator
        self.thinking_indicator = ThinkingIndicator()
        chat_layout.addWidget(self.log_view)
        chat_layout.addWidget(self.thinking_indicator, alignment=Qt.AlignmentFlag.AlignLeft)
        self.workspace_tabs.addTab(chat_tab, "Chat")

        self.memory_list = self._create_list_tab("Memory")
        self.task_list = self._create_list_tab("Tasks")
        self.plugin_list = self._create_list_tab("Plugins")
        self.settings_list = self._create_list_tab("Settings")
        right_layout.addWidget(self.workspace_tabs)

        # Input Area
        input_row = QHBoxLayout()
        input_row.setSpacing(12)

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Message Kora...")
        self.text_input.setFixedHeight(50)
        self.text_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: #0a0f1e;
                border: 1px solid {self.theme['border']};
                border-radius: 15px;
                padding: 0 20px;
                color: #ffffff;
                font-family: 'Inter', sans-serif;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 1px solid {self.theme['accent']};
                background-color: #0d1428;
            }}
        """)
        self.text_input.returnPressed.connect(self._submit_text)
        input_row.addWidget(self.text_input)

        self.send_btn = QPushButton("➤")
        self.send_btn.setFixedSize(50, 50)
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {self.theme['accent']}, stop:1 #0099cc);
                border: none;
                border-radius: 15px;
                color: #000;
                font-size: 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{ 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #55eeff, stop:1 {self.theme['accent']});
            }}
            QPushButton:disabled {{ background: #1a2233; color: #445566; }}
        """)
        self.send_btn.clicked.connect(self._submit_text)
        input_row.addWidget(self.send_btn)

        right_layout.addLayout(input_row)

        # Quick Action Bar
        self.action_bar = QFrame()
        self.action_bar.setFixedHeight(50)
        self.action_bar.setStyleSheet(f"""
            QFrame {{
                background: rgba(255, 255, 255, 5);
                border-radius: 15px;
                border: 1px solid rgba(255, 255, 255, 10);
            }}
        """)
        action_layout = QHBoxLayout(self.action_bar)
        action_layout.setContentsMargins(10, 0, 10, 0)
        
        actions = [
            ("📸", "Vision Analysis", "analyze screen"),
            ("🧹", "Clear Conversation", "reset conversation"),
            ("🧠", "Memory Summary", "what do you remember about me"),
            ("⌘", "Command Palette", "__palette__"),
            ("🌙", "Sleep Mode", "go to sleep"),
            ("⚙️", "Settings", "settings"),
            ("📁", "File Ops", "show my files")
        ]
        
        for icon, tooltip, command in actions:
            btn = QPushButton(icon)
            btn.setFixedSize(36, 36)
            btn.setToolTip(tooltip)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            accent = self.theme['accent']
            btn.setStyleSheet(f"""
                QPushButton {{ 
                    background: transparent; 
                    border: none; 
                    font-size: 18px; 
                    color: rgba(255,255,255,150);
                }} 
                QPushButton:hover {{ 
                    background: rgba(255,255,255,15); 
                    color: {accent};
                    border-radius: 10px; 
                }}
            """)
            if command == "settings":
                btn.clicked.connect(self._open_settings_dialog)
            elif command == "__palette__":
                btn.clicked.connect(self._open_command_palette)
            else:
                btn.clicked.connect(lambda checked, c=command: self.text_input_signal.emit(c))
            action_layout.addWidget(btn)
        
        action_layout.addStretch()
        right_layout.addWidget(self.action_bar)

        if input_mode == "voice":
            self.text_input.hide()
            self.send_btn.hide()

        root.addWidget(right, stretch=1)
        layout_container.addWidget(content_wrap)

        self._init_overlay()

        # Tray & Signals
        self._init_tray()
        self.status_signal.connect(self.update_status)
        self.log_signal.connect(self.append_log)
        self.mood_signal.connect(self.sphere_core.set_mood)
        self.telemetry_signal.connect(self.update_telemetry)
        self.re_enable_input_signal.connect(self._re_enable_input_on_main_thread)
        self.palette_shortcut = QShortcut(QKeySequence("Ctrl+K"), self)
        self.palette_shortcut.activated.connect(self._open_command_palette)

        # Small Thing: Quick clipboard monitor timer
        self.last_clip = ""
        self.clip_timer = QTimer(self)
        self.clip_timer.timeout.connect(self._check_clipboard)
        self.clip_timer.start(2000)

        self._load_past_logs()
        self._load_telemetry_snapshot()
        self._refresh_dashboard_panels()
        self.panel_refresh_timer = QTimer(self)
        self.panel_refresh_timer.timeout.connect(self._refresh_dashboard_panels)
        self.panel_refresh_timer.start(5000)

    def _create_list_tab(self, title):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        refresh = QPushButton("Refresh")
        refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,255,255,12);
                border: 1px solid {self.theme['border']};
                border-radius: 10px;
                color: #dbe7f5;
                padding: 8px 12px;
                font-weight: 700;
            }}
            QPushButton:hover {{ background: {self.theme['accent']}; color: #061018; }}
        """)
        listing = QListWidget()
        listing.setStyleSheet(f"""
            QListWidget {{
                background: rgba(4, 8, 16, 165);
                border: 1px solid {self.theme['border']};
                border-radius: 14px;
                color: #dbe7f5;
                padding: 8px;
                font-size: 13px;
            }}
            QListWidget::item {{ padding: 9px; border-bottom: 1px solid rgba(255,255,255,8); }}
        """)
        refresh.clicked.connect(self._refresh_dashboard_panels)
        layout.addWidget(refresh, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addWidget(listing)
        self.workspace_tabs.addTab(tab, title)
        return listing

    def _set_list_items(self, widget, rows):
        widget.clear()
        for row in rows:
            widget.addItem(QListWidgetItem(str(row)))

    def _refresh_dashboard_panels(self):
        try:
            from storage import load_all_settings, search_memories
            memories = search_memories(limit=12)
            self._set_list_items(
                self.memory_list,
                [f"{category}: {content}" for _id, category, content, _ts in memories] or ["No saved memories yet."],
            )
        except Exception as e:
            self._set_list_items(self.memory_list, [f"Memory panel unavailable: {e}"])

        try:
            from task_memory import load_task_memory
            tasks = load_task_memory(limit=12)
            self._set_list_items(
                self.task_list,
                [f"{task['status'].upper()} - {task['title']} {task['notes']}".strip() for task in tasks] or ["No tracked tasks yet."],
            )
        except Exception as e:
            self._set_list_items(self.task_list, [f"Task panel unavailable: {e}"])

        try:
            from plugin_loader import get_loaded_plugins
            plugins = get_loaded_plugins()
            rows = [
                f"{name}: {getattr(mod, 'DESCRIPTION', 'No description')}"
                for name, mod in sorted(plugins.items())
            ]
            self._set_list_items(self.plugin_list, rows or ["No plugins loaded."])
        except Exception as e:
            self._set_list_items(self.plugin_list, [f"Plugin panel unavailable: {e}"])

        try:
            from storage import load_all_settings
            settings = load_all_settings()
            rows = [f"{key}: {value}" for key, value in sorted(settings.items())]
            self._set_list_items(self.settings_list, rows or ["No custom settings saved."])
        except Exception as e:
            self._set_list_items(self.settings_list, [f"Settings panel unavailable: {e}"])

    def _open_command_palette(self):
        palette = CommandPalette(self)
        palette.exec()

    def _init_overlay(self):
        self.overlay_frame = QFrame(self)
        self.overlay_frame.hide()
        self.overlay_frame.setObjectName("OverlayFrame")
        self.overlay_frame.setCursor(Qt.CursorShape.PointingHandCursor)
        self.overlay_frame.setStyleSheet(f"""
            #OverlayFrame {{
                background: rgba(8, 12, 22, 235);
                border: 1px solid {self.theme['border']};
                border-radius: 22px;
            }}
            QLabel {{
                background: transparent;
                color: #e8f2ff;
                font-family: 'Inter', sans-serif;
            }}
            QPushButton {{
                background: rgba(255, 255, 255, 14);
                border: none;
                border-radius: 12px;
                color: #e8f2ff;
                font-weight: bold;
                padding: 6px 10px;
            }}
            QPushButton:hover {{
                background: {self.theme['accent']};
                color: #061018;
            }}
        """)

        layout = QHBoxLayout(self.overlay_frame)
        layout.setContentsMargins(16, 12, 12, 12)
        layout.setSpacing(12)

        self.overlay_orb = QLabel()
        self.overlay_orb.setFixedSize(42, 42)
        orb = QPixmap(42, 42)
        orb.fill(Qt.GlobalColor.transparent)
        painter = QPainter(orb)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(self.theme["accent"]))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(4, 4, 34, 34)
        painter.setBrush(QColor(255, 255, 255, 180))
        painter.drawEllipse(15, 15, 12, 12)
        painter.end()
        self.overlay_orb.setPixmap(orb)
        layout.addWidget(self.overlay_orb)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        self.overlay_title = QLabel("KORA")
        self.overlay_title.setFont(QFont("Outfit", 11, QFont.Weight.Bold))
        self.overlay_title.setStyleSheet(f"color: {self.theme['accent']}; letter-spacing: 2px;")
        self.overlay_status = QLabel("SYSTEM ONLINE")
        self.overlay_status.setFont(QFont("Inter", 9))
        self.overlay_status.setStyleSheet("color: #8fa4bd;")
        text_col.addWidget(self.overlay_title)
        text_col.addWidget(self.overlay_status)
        layout.addLayout(text_col, stretch=1)

        open_btn = QPushButton("Open")
        open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_btn.clicked.connect(self._exit_overlay)
        layout.addWidget(open_btn)

    def _enter_overlay(self):
        if self.overlay_mode:
            return
        self.overlay_mode = True
        self._normal_geometry = self.geometry()
        self.main_frame.hide()
        self.overlay_frame.show()
        self.setFixedSize(286, 92)
        screen = self.screen().availableGeometry() if self.screen() else None
        if screen:
            self.move(screen.right() - self.width() - 24, screen.bottom() - self.height() - 36)
        self.setWindowOpacity(0.96)
        self.overlay_frame.setGeometry(0, 0, self.width(), self.height())
        self.show()
        self.raise_()

    def _exit_overlay(self):
        if not self.overlay_mode:
            self.showNormal()
            self.activateWindow()
            return
        self.overlay_mode = False
        self.overlay_frame.hide()
        self.main_frame.show()
        self.setWindowOpacity(1.0)
        self.setMinimumSize(0, 0)
        self.setMaximumSize(16777215, 16777215)
        if self._normal_geometry:
            self.setGeometry(self._normal_geometry)
        else:
            self.setGeometry(60, 60, 1040, 700)
        self.main_frame.setGeometry(20, 20, self.width() - 40, self.height() - 40)
        self.nebula.setGeometry(0, 0, self.main_frame.width(), self.main_frame.height())
        self.showNormal()
        self.activateWindow()

    def _get_mode_text(self):
        modes = {
            "voice": "VOICE ACTIVE",
            "text": "TEXT ACTIVE",
            "both": "VOICE + TEXT ACTIVE"
        }
        return modes.get(self.input_mode, "SYSTEM ACTIVE")

    def _init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(self.theme['accent']))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(8, 8, 48, 48)
        painter.end()
        self.tray_icon.setIcon(QIcon(pixmap))
        menu = QMenu()
        show_action = QAction("Open Kora", self)
        show_action.triggered.connect(self._exit_overlay)
        menu.addAction(show_action)
        exit_action = QAction("Shutdown", self)
        exit_action.triggered.connect(self._close_app)
        menu.addAction(exit_action)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self._tray_activated)
        self.tray_icon.show()

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.overlay_mode:
                self._exit_overlay()
            elif self.isVisible(): self._enter_overlay()
            else: 
                self._exit_overlay()
                self._greet_user()

    def _greet_user(self):
        """Small Thing: Smart Time-Aware Greeting."""
        hour = datetime.now().hour
        if 5 <= hour < 12:    greeting = "Good morning"
        elif 12 <= hour < 18: greeting = "Good afternoon"
        else:                 greeting = "Good evening"
        
        # Only greet if the log is empty or after a long break
        self.log_signal.emit("SYSTEM", f"{greeting}! Kora is ready to assist.")

    def _close_app(self):
        os._exit(0)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def _submit_text(self):
        text = self.text_input.text().strip()
        if not text: return
        self.text_input.clear()
        self.send_btn.setEnabled(False)
        self.thinking_indicator.show()
        self.text_input_signal.emit(text)

    def re_enable_input(self):
        self.re_enable_input_signal.emit()

    def _re_enable_input_on_main_thread(self):
        self.send_btn.setEnabled(True)
        self.text_input.setFocus()

    def update_status(self, text):
        raw = text.upper()
        self.status_label.setText(raw)
        if hasattr(self, "overlay_status"):
            self.overlay_status.setText(raw[:28])
        
        # Big Impact: Dynamic Window Title
        self.setWindowTitle(f"KORA | {raw}")
        
        brain_on = "PROCESSING" in raw
        self.nebula.is_processing = brain_on # Trigger glitch effect
        
        eye_on   = "VISION" in raw or "EYE" in raw
        ears_on  = "LISTENING" in raw
        
        self.hud_widget.set_module_states(brain=brain_on, eye=eye_on, ears=ears_on)

        if   "LISTENING"   in raw: self.sphere_core.state = "LISTENING"
        elif "PROCESSING"  in raw: self.sphere_core.state = "PROCESSING"
        elif "SPEAKING"    in raw: self.sphere_core.state = "SPEAKING"
        else:                      self.sphere_core.state = "IDLE"

    def _check_clipboard(self):
        """Small Thing: Proactive clipboard interaction."""
        try:
            from clipboard_ops import read_clipboard
            current = read_clipboard()
            if current and current != self.last_clip:
                self.last_clip = current
                # Only react to 'interesting' things like URLs or long text
                if current.startswith(("http://", "https://")):
                    self.log_signal.emit("SYSTEM", f"URL detected in clipboard: {current[:40]}...")
                    # We don't speak, just show a subtle log.
        except Exception: pass

    def append_log(self, sender, message):
        # Hide thinking indicator when a reply arrives
        if sender.upper() == "KORA":
            self.thinking_indicator.hide()
            
        color = self.LOG_COLORS.get(sender.upper(), "#aaaaaa")
        accent = self.theme['accent']
        
        # Determine bubble style
        is_user = sender.upper() == "USER"
        
        align = "right" if is_user else "left"
        bg_color = "rgba(40, 50, 80, 150)" if is_user else "rgba(20, 25, 45, 220)"
        border_color = accent if not is_user else "rgba(255, 255, 255, 30)"
        
        # Clean relevant memory prefix from LLM replies for cleaner UI
        display = message
        if message.startswith("[Relevant memory:") and "\n\nUser says:" in message:
            display = message.split("\n\nUser says:", 1)[1].strip()
        
        safe_sender = escape(str(sender).upper())
        safe_display = escape(str(display)).replace("\n", "<br/>")
        
        # Premium Bubble HTML
        avatar = "👤" if is_user else "💠"
        html = f"""
        <div style="margin: 14px 0; text-align: {align}; font-family: 'Inter', sans-serif;">
            <div style="color: {color}; font-weight: 700; font-size: 11px; margin-bottom: 6px; letter-spacing: 1px; opacity: 0.9; text-transform: uppercase;">
                {avatar} {safe_sender}
            </div>
            <div style="
                background: {bg_color};
                border: 1px solid {border_color};
                border-radius: 18px;
                border-bottom-{align}-radius: 4px;
                padding: 16px 22px;
                display: inline-block;
                max-width: 85%;
                text-align: left;
                color: #f0f4f8;
                font-size: 15px;
                line-height: 1.6;
                box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.2);
            ">
                {safe_display}
            </div>
        </div>
        """
        self.log_view.append(html)
        self.log_view.moveCursor(QTextCursor.MoveOperation.End)

    def _open_settings_dialog(self):
        dlg = SettingsDialog(self)
        if dlg.exec():
            self.log_signal.emit("SYSTEM", "Settings saved. Restart Kora to fully apply theme and hardware changes.")

    def _load_past_logs(self):
        try:
            from storage import load_all_logs
            entries = load_all_logs()
            if not entries: return
            self.log_view.append('<div style="color: #3a4b6c; font-size: 10px; text-align: center; margin: 20px 0;">─── ARCHIVED SESSIONS ───</div>')
            for ts, role, content in entries:
                self.append_log(role, content)
            self.log_view.append('<div style="color: #3a4b6c; font-size: 10px; text-align: center; margin: 20px 0;">─── NEW SESSION ───</div>')
        except Exception as e:
            print(f"[GUI] Log restore error: {e}")

    def _load_telemetry_snapshot(self):
        try:
            from storage import load_telemetry_summary
            self.update_telemetry(load_telemetry_summary())
        except Exception: pass

    def update_telemetry(self, summary):
        # The HUD handles real-time metrics now, but we can still use this for event logs
        pass

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self._enter_overlay()

    def mouseDoubleClickEvent(self, event):
        if self.overlay_mode and event.button() == Qt.MouseButton.LeftButton:
            self._exit_overlay()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "overlay_frame") and self.overlay_mode:
            self.overlay_frame.setGeometry(0, 0, self.width(), self.height())
        elif hasattr(self, "main_frame"):
            self.main_frame.setGeometry(20, 20, max(1, self.width() - 40), max(1, self.height() - 40))
            if hasattr(self, "nebula"):
                self.nebula.setGeometry(0, 0, self.main_frame.width(), self.main_frame.height())
