import sys
import os
import math
import random
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRectF
from PyQt6.QtGui import QPainter, QColor, QFont, QPainterPath, QRadialGradient, QPen

# ==============================================================================
# 3D PARTICLE SPHERE ENGINE (V2 POLISHED)
# ==============================================================================

class ParticlePoint:
    def __init__(self, x, y, z):
        self.base_x = x
        self.base_y = y
        self.base_z = z

class AuraSphereWidget(QWidget):
    """ Renders thousands of dots on a 3D sphere with an energy core and bounding rings. """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(450, 450)
        self.phase = 0.0
        self.rot_x = 0.0
        self.rot_y = 0.0
        self.state = "IDLE" 
        
        # Generate 1200 particles using the Golden Ratio (Fibonacci sphere) 
        self.particles = []
        num_particles = 1200 
        phi = math.pi * (3.0 - math.sqrt(5.0))

        for i in range(num_particles):
            y = 1 - (i / float(num_particles - 1)) * 2 
            r = math.sqrt(1 - y * y)  
            theta = phi * i  

            x = math.cos(theta) * r
            z = math.sin(theta) * r
            self.particles.append(ParticlePoint(x, y, z))

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(16) 

    def animate(self):
        self.phase += 0.1
        # Slowly spin the 3D sphere
        if self.state == "PROCESSING":
            self.rot_y -= 0.08 
            self.rot_x += 0.04
        elif self.state == "SPEAKING":
            self.rot_y -= 0.04 
            self.rot_x += 0.02
        else:
            self.rot_y -= 0.01
            self.rot_x += 0.005
            
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Deep space background for the widget array
        rect = QRectF(self.rect().adjusted(2, 2, -2, -2))
        path = QPainterPath()
        path.addRoundedRect(rect, 30, 30)
        p.fillPath(path, QColor(8, 10, 14, 240))
        
        cx, cy = self.width() / 2, self.height() / 2
        
        # Base Sphere Radius
        sphere_radius = 110
        global_shake = 0
        
        if self.state == "SPEAKING":
            sphere_radius += math.sin(self.phase * 3.5) * 15
            global_shake = 8 
        elif self.state == "LISTENING":
            sphere_radius += math.sin(self.phase * 1.0) * 8
        elif self.state == "PROCESSING":
            sphere_radius += math.sin(self.phase * 0.8) * 3
        else:
            sphere_radius += math.sin(self.phase * 0.3) * 3

        # --- NEW POLISH: Pulsing Energy Nebula Core ---
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Screen)
        core_grad = QRadialGradient(cx, cy, sphere_radius * 1.5)
        core_grad.setColorAt(0, QColor(0, 100, 255, 60))    # Deep Blue center
        core_grad.setColorAt(0.5, QColor(150, 40, 255, 30)) # Purple corona
        core_grad.setColorAt(1, QColor(0, 0, 0, 0))         # Falloff
        p.setBrush(core_grad)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(int(cx - sphere_radius*2), int(cy - sphere_radius*2), int(sphere_radius*4), int(sphere_radius*4))
            
        # --- NEW POLISH: Geometric Containment Rings ---
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        ring_pen = QPen(QColor(0, 210, 255, 50))
        ring_pen.setWidthF(1.5)
        p.setPen(ring_pen)
        p.setBrush(Qt.GlobalColor.transparent)
        
        # Static subtle outer boundary
        ring_radius = sphere_radius * 1.7
        p.drawEllipse(int(cx - ring_radius), int(cy - ring_radius), int(ring_radius*2), int(ring_radius*2))
        
        # Rotating inner fragmented ring
        ring_pen.setColor(QColor(200, 50, 255, 80))
        ring_pen.setWidthF(2.0)
        p.setPen(ring_pen)
        span = 60 * 16 # 60 degree sweeps
        start_angle = int((math.degrees(self.phase * -0.5)) % 360 * 16)
        p.drawArc(int(cx - ring_radius*0.9), int(cy - ring_radius*0.9), int(ring_radius*1.8), int(ring_radius*1.8), start_angle, span)
        p.drawArc(int(cx - ring_radius*0.9), int(cy - ring_radius*0.9), int(ring_radius*1.8), int(ring_radius*1.8), start_angle + (180*16), span)


        # --- 3D PARTICLE RENDERER ---
        cos_x = math.cos(self.rot_x)
        sin_x = math.sin(self.rot_x)
        cos_y = math.cos(self.rot_y)
        sin_y = math.sin(self.rot_y)
        
        projected = []
        
        for pt in self.particles:
            jx = random.uniform(-global_shake, global_shake) if global_shake else 0
            jy = random.uniform(-global_shake, global_shake) if global_shake else 0
            jz = random.uniform(-global_shake, global_shake) if global_shake else 0

            scaled_x = (pt.base_x * sphere_radius) + jx
            scaled_y = (pt.base_y * sphere_radius) + jy
            scaled_z = (pt.base_z * sphere_radius) + jz

            y1 = scaled_y * cos_x - scaled_z * sin_x
            z1 = scaled_y * sin_x + scaled_z * cos_x
            
            x2 = scaled_x * cos_y + z1 * sin_y
            z2 = -scaled_x * sin_y + z1 * cos_y
            
            screen_x = cx + x2
            screen_y = cy + y1
            depth = z2
            
            projected.append((screen_x, screen_y, depth))
            
        projected.sort(key=lambda p: p[2])
        p.setPen(Qt.PenStyle.NoPen)
        
        for screen_x, screen_y, depth in projected:
            depth_ratio = (depth + sphere_radius) / (sphere_radius * 2) 
            depth_ratio = max(0.01, min(1.0, depth_ratio)) 
            
            alpha = int(50 + (205 * depth_ratio))
            p.setBrush(QColor(0, 210, 255, alpha))
            
            dot_size = 1.6 + (depth_ratio * 1.5)
            p.drawEllipse(QRectF(screen_x - dot_size/2, screen_y - dot_size/2, dot_size, dot_size))


# ==============================================================================
# MINIMALIST DESKTOP FRAME
# ==============================================================================

class AuraDashboard(QMainWindow):
    status_signal = pyqtSignal(str)
    log_signal = pyqtSignal(str, str) 

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AURA SPHERE CORE")
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setGeometry(100, 100, 500, 600)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(15, 15, 15, 15)

        self.sphere_core = AuraSphereWidget()
        layout.addWidget(self.sphere_core, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.status_label = QLabel("SYSTEM ONLINE")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont("Inter", 12, QFont.Weight.Bold)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 5)
        self.status_label.setFont(font)
        self.status_label.setStyleSheet("color: #00d2ff;")
        
        layout.addWidget(self.status_label)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 200))
        shadow.setOffset(0, 15)
        self.sphere_core.setGraphicsEffect(shadow)

        self.status_signal.connect(self.update_status)

    def keyPressEvent(self, event):
        """ INSTANT EMERGENCY ABORT: Bypasses Audio transcription wait """
        if event.key() == Qt.Key.Key_Escape:
            print("\n[AURA]: Emergency Abort triggered via ESC. Terminating.")
            os._exit(0)

    def update_status(self, text):
        raw = text.upper()
        self.status_label.setText(raw)
        
        if "LISTENING" in raw:
            self.sphere_core.state = "LISTENING"
        elif "PROCESSING" in raw:
            self.sphere_core.state = "PROCESSING"
        elif "SPEAKING" in raw:
            self.sphere_core.state = "SPEAKING"
        else:
            self.sphere_core.state = "IDLE"

    def append_log(self, sender, message):
        pass 