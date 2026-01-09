"""
Sentinel Overlay UI - Premium stealth assistant for real-time sales intelligence.

Features:
- Glassmorphism design with neon accents
- Transparent, borderless window that stays on top
- Stealth Mode: Hidden from screen capture/recording (Windows 10+)
- Live transcript display with speaker identification
- AI Confidence Meter
- Quick Hints with star actions
- Battlecard integration
"""

import sys
import ctypes
from typing import List, Optional
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QFrame, QScrollArea, QProgressBar,
    QGraphicsDropShadowEffect, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QPalette, QLinearGradient, QPainter


# Windows constants for SetWindowDisplayAffinity
WDA_NONE = 0x00000000
WDA_EXCLUDEFROMCAPTURE = 0x00000011  # Windows 10 2004+ (Build 19041+)


# ==================== PREMIUM STYLE CONSTANTS ====================
STYLES = {
    # Colors
    "bg_primary": "rgba(12, 14, 24, 0.94)",
    "bg_secondary": "rgba(22, 27, 42, 0.92)",
    "bg_tertiary": "rgba(32, 38, 58, 0.88)",
    "accent_cyan": "#00D4FF",
    "accent_blue": "#4FACFE",
    "accent_gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00D4FF, stop:1 #4FACFE)",
    "success": "#00E676",
    "warning": "#FF9100",
    "error": "#FF5252",
    "text_primary": "#FFFFFF",
    "text_secondary": "#A0A8C0",
    "text_muted": "#606882",
    "border_glow": "rgba(0, 212, 255, 0.35)",
    "border_subtle": "rgba(80, 100, 140, 0.25)",
    
    # Typography
    "font_family": "Segoe UI, Arial, sans-serif",
    "font_heading": "14px",
    "font_body": "12px",
    "font_small": "11px",
    
    # Spacing
    "radius_lg": "16px",
    "radius_md": "10px",
    "radius_sm": "6px",
}


# ==================== FLOATING PANEL BASE CLASS ====================
class FloatingPanel(QMainWindow):
    """
    Base class for detachable floating panels that can snap to other panels.
    """
    SNAP_THRESHOLD = 30  # Pixels to trigger snap
    DETACH_THRESHOLD = 50  # Pixels to detach
    
    def __init__(self, parent_panel=None, snap_side='right'):
        super().__init__()
        self.parent_panel = parent_panel
        self.snap_side = snap_side
        self.is_snapped = True if parent_panel else False
        self._drag_pos = None
        
        self._setup_window()
        
    def _setup_window(self):
        """Configure frameless, always-on-top window."""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
    def snap_to(self, parent_panel, side='right'):
        """Snap this panel to another panel's edge."""
        self.parent_panel = parent_panel
        self.snap_side = side
        self.is_snapped = True
        self._position_snapped()
        
    def _position_snapped(self):
        """Position panel relative to parent based on snap side."""
        if not self.parent_panel:
            return
            
        parent_geo = self.parent_panel.geometry()
        
        if self.snap_side == 'right':
            x = parent_geo.x() + parent_geo.width() + 5
            y = parent_geo.y()
        elif self.snap_side == 'left':
            x = parent_geo.x() - self.width() - 5
            y = parent_geo.y()
        elif self.snap_side == 'top':
            x = parent_geo.x()
            y = parent_geo.y() - self.height() - 5
        else:  # bottom
            x = parent_geo.x()
            y = parent_geo.y() + parent_geo.height() + 5
            
        self.move(x, y)
        
    def detach(self):
        """Detach from parent panel."""
        self.is_snapped = False
        
    def follow_parent(self):
        """If snapped, follow parent panel movement."""
        if self.is_snapped and self.parent_panel:
            self._position_snapped()
            
    def mousePressEvent(self, event):
        """Start drag operation."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        """Handle dragging and snap detection."""
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            new_pos = event.globalPosition().toPoint() - self._drag_pos
            self.move(new_pos)
            
            # Check if we should detach
            if self.is_snapped and self.parent_panel:
                parent_geo = self.parent_panel.geometry()
                my_geo = self.geometry()
                distance = abs(my_geo.x() - (parent_geo.x() + parent_geo.width()))
                if distance > self.DETACH_THRESHOLD:
                    self.detach()
            event.accept()
            
    def closeEvent(self, event):
        """Clean up on close."""
        self.is_snapped = False
        event.accept()


class InsightDetailPanel(FloatingPanel):
    """Panel showing expanded insight details when a hint is clicked."""
    
    def __init__(self, parent_panel=None, hint_text="", context=""):
        super().__init__(parent_panel, snap_side='left')
        self.hint_text = hint_text
        self.context = context
        self._setup_ui()
        self.resize(280, 200)
        if parent_panel:
            self._position_snapped()
        
    def _setup_ui(self):
        """Build the insight detail UI."""
        container = QWidget()
        container.setObjectName("insightPanel")
        container.setStyleSheet(f"""
            #insightPanel {{
                background-color: {STYLES['bg_primary']};
                border-radius: {STYLES['radius_md']};
                border: 1px solid {STYLES['accent_cyan']};
            }}
        """)
        self.setCentralWidget(container)
        
        # Add glow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 212, 255, 80))
        shadow.setOffset(0, 0)
        container.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        
        # Header
        header_row = QHBoxLayout()
        header = QLabel("INSIGHT DETAILS")
        header.setStyleSheet(f"""
            color: {STYLES['accent_cyan']};
            font-size: 10px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        header_row.addWidget(header)
        header_row.addStretch()
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {STYLES['text_muted']};
                border: none;
                font-size: 16px;
            }}
            QPushButton:hover {{
                color: {STYLES['error']};
            }}
        """)
        close_btn.clicked.connect(self.close)
        header_row.addWidget(close_btn)
        layout.addLayout(header_row)
        
        # Insight text
        self.insight_label = QLabel(self.hint_text)
        self.insight_label.setWordWrap(True)
        self.insight_label.setStyleSheet(f"""
            color: {STYLES['text_primary']};
            font-size: 13px;
            padding: 8px;
            background-color: {STYLES['bg_secondary']};
            border-radius: {STYLES['radius_sm']};
        """)
        layout.addWidget(self.insight_label)
        
        # Context/suggestion
        self.context_label = QLabel("💡 Suggested action: Ask follow-up questions to understand their needs better.")
        self.context_label.setWordWrap(True)
        self.context_label.setStyleSheet(f"""
            color: {STYLES['text_secondary']};
            font-size: 11px;
            padding: 4px;
        """)
        layout.addWidget(self.context_label)
        
        layout.addStretch()
        
    def set_content(self, hint_text, context=""):
        """Update the panel content."""
        self.hint_text = hint_text
        self.insight_label.setText(hint_text)
        if context:
            self.context_label.setText(f"💡 {context}")


class BattlecardPanel(FloatingPanel):
    """Panel showing competitor battlecard information."""
    
    def __init__(self, parent_panel=None, competitor="", counter_points=None):
        super().__init__(parent_panel, snap_side='right')
        self.competitor = competitor or "Competitor"
        self.counter_points = counter_points or []
        self._setup_ui()
        self.resize(300, 250)
        if parent_panel:
            self._position_snapped()
        
    def _setup_ui(self):
        """Build the battlecard UI."""
        container = QWidget()
        container.setObjectName("battlecardPanel")
        container.setStyleSheet(f"""
            #battlecardPanel {{
                background-color: {STYLES['bg_primary']};
                border-radius: {STYLES['radius_md']};
                border: 1px solid {STYLES['warning']};
            }}
        """)
        self.setCentralWidget(container)
        
        # Add glow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(255, 145, 0, 80))
        shadow.setOffset(0, 0)
        container.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        
        # Header
        header_row = QHBoxLayout()
        header = QLabel("⚔ BATTLECARD")
        header.setStyleSheet(f"""
            color: {STYLES['warning']};
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        header_row.addWidget(header)
        header_row.addStretch()
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {STYLES['text_muted']};
                border: none;
                font-size: 16px;
            }}
            QPushButton:hover {{
                color: {STYLES['error']};
            }}
        """)
        close_btn.clicked.connect(self.close)
        header_row.addWidget(close_btn)
        layout.addLayout(header_row)
        
        # Competitor name
        self.competitor_label = QLabel(f"vs {self.competitor}")
        self.competitor_label.setStyleSheet(f"""
            color: {STYLES['text_primary']};
            font-size: 16px;
            font-weight: bold;
            padding: 4px 0;
        """)
        layout.addWidget(self.competitor_label)
        
        # Counter-points container
        self.points_container = QWidget()
        self.points_layout = QVBoxLayout(self.points_container)
        self.points_layout.setContentsMargins(0, 0, 0, 0)
        self.points_layout.setSpacing(6)
        
        # Add sample counter-points
        sample_points = [
            "We offer 24/7 local support vs their offshore team",
            "Our implementation is 2x faster on average",
            "No hidden fees - transparent pricing model"
        ]
        for point in sample_points:
            self._add_counter_point(point)
            
        layout.addWidget(self.points_container)
        layout.addStretch()
        
    def _add_counter_point(self, text):
        """Add a counter-point item."""
        point = QLabel(f"✓ {text}")
        point.setWordWrap(True)
        point.setStyleSheet(f"""
            color: {STYLES['text_secondary']};
            font-size: 11px;
            padding: 4px 8px;
            background-color: {STYLES['bg_secondary']};
            border-radius: {STYLES['radius_sm']};
            border-left: 2px solid {STYLES['success']};
        """)
        self.points_layout.addWidget(point)
        
    def set_content(self, competitor, counter_points):
        """Update battlecard content."""
        self.competitor = competitor
        self.competitor_label.setText(f"vs {competitor}")
        
        # Clear existing points
        while self.points_layout.count():
            child = self.points_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        # Add new points
        for point in counter_points:
            self._add_counter_point(point)


class SignalBridge(QObject):
    """Bridge for thread-safe signal emission."""
    hints_updated = pyqtSignal(list)
    transcript_updated = pyqtSignal(str)
    status_updated = pyqtSignal(str)
    entities_updated = pyqtSignal(list)
    confidence_updated = pyqtSignal(int)  # 0-100 confidence score
    battlecard_updated = pyqtSignal(dict) # {competitor, points}


class StealthOverlay(QMainWindow):
    """
    Stealth overlay window for real-time sales assistance.
    
    Can be hidden from screen capture using Windows API.
    """
    
    def __init__(self):
        super().__init__()
        
        self._stealth_enabled = False
        self._is_recording = False
        self._current_confidence = 0
        
        # Floating panels tracking
        self.insight_panel = None
        self.battlecard_panel = None
        
        # Demo mode state
        self._demo_active = False
        self._demo_timer = None
        
        # Signal bridge for thread-safe updates
        self.signals = SignalBridge()
        self.signals.hints_updated.connect(self._on_hints_updated)
        self.signals.transcript_updated.connect(self._on_transcript_updated)
        self.signals.status_updated.connect(self._on_status_updated)
        self.signals.entities_updated.connect(self._on_entities_updated)
        self.signals.confidence_updated.connect(self._on_confidence_updated)
        
        self._setup_ui()
        self._setup_window()
        
    def _setup_window(self):
        """Configure window properties."""
        self.setWindowTitle("Sentinel - Sales Intelligence")
        
        # Frameless, always on top, tool window (doesn't show in taskbar)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        
        # Transparent background
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Position: Bottom-right corner - larger for better visibility
        self.resize(380, 480)
        self._position_window()
        
    def _position_window(self):
        """Position window in bottom-right corner of screen."""
        screen = QApplication.primaryScreen()
        if screen:
            geometry = screen.availableGeometry()
            x = geometry.width() - self.width() - 20
            y = geometry.height() - self.height() - 20
            self.move(x, y)
    
    def _setup_ui(self):
        """Build the UI components with premium styling."""
        # Main container with glassmorphism effect
        container = QWidget()
        container.setObjectName("container")
        container.setStyleSheet(f"""
            #container {{
                background-color: {STYLES['bg_primary']};
                border-radius: {STYLES['radius_lg']};
                border: 1px solid {STYLES['border_glow']};
            }}
            QLabel {{
                font-family: {STYLES['font_family']};
            }}
            QPushButton {{
                font-family: {STYLES['font_family']};
            }}
        """)
        self.setCentralWidget(container)
        
        # Add drop shadow for depth
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 212, 255, 60))
        shadow.setOffset(0, 0)
        container.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)
        
        # Header with status and stealth toggle
        header = self._create_header()
        layout.addWidget(header)
        
        # Speaker Intelligence Strip
        self.speaker_strip = self._create_speaker_strip()
        layout.addWidget(self.speaker_strip)
        
        # Confidence Meter (AI Closing Probability)
        self.confidence_widget = self._create_confidence_meter()
        layout.addWidget(self.confidence_widget)
        
        # Hints panel
        self.hints_frame = self._create_hints_panel()
        layout.addWidget(self.hints_frame)
        
        # Transcript panel
        self.transcript_panel = self._create_transcript_panel()
        layout.addWidget(self.transcript_panel, stretch=1)
        
        # Entities panel  
        self.entities_label = QLabel("Entities: None detected")
        self.entities_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.entities_label)
        
        # Control buttons
        controls = self._create_controls()
        layout.addWidget(controls)
    
    def _create_header(self) -> QWidget:
        """Create premium header with SENTINEL branding and status indicators."""
        header = QWidget()
        header.setStyleSheet(f"""
            QWidget {{
                background-color: transparent;
            }}
        """)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 8)
        layout.setSpacing(8)
        
        # SENTINEL branding
        brand_container = QWidget()
        brand_layout = QHBoxLayout(brand_container)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(6)
        
        # Logo icon
        logo = QLabel("◆")
        logo.setStyleSheet(f"""
            color: {STYLES['accent_cyan']};
            font-size: 16px;
            font-weight: bold;
        """)
        brand_layout.addWidget(logo)
        
        # Brand name
        title = QLabel("SENTINEL")
        title.setStyleSheet(f"""
            color: {STYLES['text_primary']};
            font-size: 15px;
            font-weight: bold;
            letter-spacing: 2px;
        """)
        brand_layout.addWidget(title)
        
        layout.addWidget(brand_container)
        layout.addStretch()
        
        # LIVE indicator with pulsing animation
        self.live_container = QWidget()
        live_layout = QHBoxLayout(self.live_container)
        live_layout.setContentsMargins(8, 4, 8, 4)
        live_layout.setSpacing(4)
        
        self.live_dot = QLabel("●")
        self.live_dot.setStyleSheet(f"color: {STYLES['text_muted']}; font-size: 10px;")
        live_layout.addWidget(self.live_dot)
        
        self.status_label = QLabel("IDLE")
        self.status_label.setStyleSheet(f"""
            color: {STYLES['text_muted']};
            font-size: 10px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        live_layout.addWidget(self.status_label)
        
        self.live_container.setStyleSheet(f"""
            background-color: {STYLES['bg_tertiary']};
            border-radius: 10px;
        """)
        layout.addWidget(self.live_container)
        
        # Vision awareness indicator
        self.vision_indicator = QLabel("👁")
        self.vision_indicator.setStyleSheet(f"""
            font-size: 14px;
            padding: 2px 4px;
        """)
        self.vision_indicator.setToolTip("Vision: Inactive")
        layout.addWidget(self.vision_indicator)
        
        # Stealth indicator
        self.stealth_indicator = QLabel("[V]")
        self.stealth_indicator.setStyleSheet(f"font-size: 11px; padding: 2px 4px; color: {STYLES['text_muted']};")
        self.stealth_indicator.setToolTip("Stealth Mode: OFF (Visible)")
        layout.addWidget(self.stealth_indicator)
        
        # Setup pulsing animation timer
        self._pulse_state = False
        self._pulse_timer = QTimer()
        self._pulse_timer.timeout.connect(self._pulse_live_indicator)
        
        return header
    
    def _create_speaker_strip(self) -> QWidget:
        """Create Speaker Intelligence Strip showing talk-time balance."""
        widget = QWidget()
        widget.setObjectName("speakerStrip")
        widget.setStyleSheet(f"""
            #speakerStrip {{
                background-color: {STYLES['bg_secondary']};
                border-radius: {STYLES['radius_sm']};
                border: 1px solid {STYLES['border_subtle']};
            }}
        """)
        
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(10)
        
        # Left: Speaker 1 indicator
        self.speaker1_label = QLabel("S1")
        self.speaker1_label.setStyleSheet(f"""
            color: {STYLES['accent_cyan']};
            font-size: 10px;
            font-weight: bold;
            padding: 2px 6px;
            background-color: rgba(0, 212, 255, 0.15);
            border-radius: 4px;
        """)
        layout.addWidget(self.speaker1_label)
        
        # Talk-time balance bar
        balance_container = QWidget()
        balance_layout = QVBoxLayout(balance_container)
        balance_layout.setContentsMargins(0, 0, 0, 0)
        balance_layout.setSpacing(2)
        
        # Percentage label
        self.talk_balance_label = QLabel("50% / 50%")
        self.talk_balance_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.talk_balance_label.setStyleSheet(f"""
            color: {STYLES['text_secondary']};
            font-size: 9px;
        """)
        balance_layout.addWidget(self.talk_balance_label)
        
        # Balance bar
        self.talk_balance_bar = QProgressBar()
        self.talk_balance_bar.setRange(0, 100)
        self.talk_balance_bar.setValue(50)
        self.talk_balance_bar.setFixedHeight(6)
        self.talk_balance_bar.setTextVisible(False)
        self.talk_balance_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: rgba(255, 215, 0, 0.3);
                border-radius: 3px;
                border: none;
            }}
            QProgressBar::chunk {{
                background-color: {STYLES['accent_cyan']};
                border-radius: 3px;
            }}
        """)
        balance_layout.addWidget(self.talk_balance_bar)
        
        layout.addWidget(balance_container, stretch=1)
        
        # Right: Speaker 2 indicator
        self.speaker2_label = QLabel("S2")
        self.speaker2_label.setStyleSheet(f"""
            color: #FFD700;
            font-size: 10px;
            font-weight: bold;
            padding: 2px 6px;
            background-color: rgba(255, 215, 0, 0.15);
            border-radius: 4px;
        """)
        layout.addWidget(self.speaker2_label)
        
        # Warning indicator (hidden by default)
        self.talk_warning = QLabel("⚠ Talking too much!")
        self.talk_warning.setStyleSheet(f"""
            color: {STYLES['warning']};
            font-size: 9px;
            font-weight: bold;
            padding: 2px 6px;
            background-color: rgba(255, 145, 0, 0.2);
            border-radius: 4px;
        """)
        self.talk_warning.setVisible(False)
        layout.addWidget(self.talk_warning)
        
        # Initialize tracking
        self._speaker1_time = 0
        self._speaker2_time = 0
        
        return widget
    
    def update_talk_balance(self, speaker1_percent: int):
        """Update the talk-time balance indicator."""
        speaker1_percent = max(0, min(100, speaker1_percent))
        speaker2_percent = 100 - speaker1_percent
        
        self.talk_balance_bar.setValue(speaker1_percent)
        self.talk_balance_label.setText(f"{speaker1_percent}% / {speaker2_percent}%")
        
        # Show warning if talking > 70%
        if speaker1_percent > 70:
            self.talk_warning.setVisible(True)
            self.talk_warning.setText("⚠ Talking too much!")
            self.talk_balance_bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: rgba(255, 215, 0, 0.3);
                    border-radius: 3px;
                    border: none;
                }}
                QProgressBar::chunk {{
                    background-color: {STYLES['warning']};
                    border-radius: 3px;
                }}
            """)
        elif speaker1_percent < 30:
            self.talk_warning.setVisible(True)
            self.talk_warning.setText("⚠ Let them speak!")
            self.talk_balance_bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: rgba(255, 215, 0, 0.3);
                    border-radius: 3px;
                    border: none;
                }}
                QProgressBar::chunk {{
                    background-color: {STYLES['warning']};
                    border-radius: 3px;
                }}
            """)
        else:
            self.talk_warning.setVisible(False)
            self.talk_balance_bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: rgba(255, 215, 0, 0.3);
                    border-radius: 3px;
                    border: none;
                }}
                QProgressBar::chunk {{
                    background-color: {STYLES['accent_cyan']};
                    border-radius: 3px;
                }}
            """)
    
    def _pulse_live_indicator(self):
        """Animate the LIVE indicator with a pulsing effect."""
        if self._is_recording:
            self._pulse_state = not self._pulse_state
            if self._pulse_state:
                self.live_dot.setStyleSheet(f"color: {STYLES['success']}; font-size: 10px;")
            else:
                self.live_dot.setStyleSheet(f"color: rgba(0, 230, 118, 0.5); font-size: 10px;")
    
    def set_vision_state(self, state: str):
        """Update vision indicator state: 'inactive', 'active', 'detected'."""
        states = {
            "inactive": ("👁", f"color: {STYLES['text_muted']};", "Vision: Inactive"),
            "active": ("👁", f"color: {STYLES['accent_cyan']};", "Vision: Scanning"),
            "detected": ("👁", f"color: {STYLES['success']};", "Vision: Entity Detected"),
        }
        emoji, style, tooltip = states.get(state, states["inactive"])
        self.vision_indicator.setText(emoji)
        self.vision_indicator.setStyleSheet(f"{style} font-size: 14px; padding: 2px 4px;")
        self.vision_indicator.setToolTip(tooltip)
    
    def _create_confidence_meter(self) -> QWidget:
        """Create the AI Confidence Meter with animated progress bar."""
        widget = QWidget()
        widget.setStyleSheet(f"""
            QWidget {{
                background-color: {STYLES['bg_secondary']};
                border-radius: {STYLES['radius_md']};
                border: 1px solid {STYLES['border_subtle']};
            }}
        """)
        
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)
        
        # Left side: Label and percentage
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        label = QLabel("AI CONFIDENCE")
        label.setStyleSheet(f"""
            color: {STYLES['text_secondary']};
            font-size: 9px;
            font-weight: bold;
            letter-spacing: 1px;
            background: transparent;
            border: none;
        """)
        info_layout.addWidget(label)
        
        self.confidence_value = QLabel("0%")
        self.confidence_value.setStyleSheet(f"""
            color: {STYLES['text_primary']};
            font-size: 24px;
            font-weight: bold;
            background: transparent;
            border: none;
        """)
        info_layout.addWidget(self.confidence_value)
        
        layout.addLayout(info_layout)
        
        # Right side: Progress bar
        bar_container = QWidget()
        bar_container.setStyleSheet("background: transparent; border: none;")
        bar_layout = QVBoxLayout(bar_container)
        bar_layout.setContentsMargins(0, 0, 0, 0)
        bar_layout.setSpacing(4)
        
        # Status text
        self.confidence_status = QLabel("Analyzing...")
        self.confidence_status.setStyleSheet(f"""
            color: {STYLES['text_muted']};
            font-size: 10px;
            background: transparent;
            border: none;
        """)
        self.confidence_status.setAlignment(Qt.AlignmentFlag.AlignRight)
        bar_layout.addWidget(self.confidence_status)
        
        # Progress bar
        self.confidence_bar = QProgressBar()
        self.confidence_bar.setRange(0, 100)
        self.confidence_bar.setValue(0)
        self.confidence_bar.setTextVisible(False)
        self.confidence_bar.setFixedHeight(8)
        self.confidence_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {STYLES['bg_tertiary']};
                border-radius: 4px;
                border: none;
            }}
            QProgressBar::chunk {{
                background-color: {STYLES['text_muted']};
                border-radius: 4px;
            }}
        """)
        bar_layout.addWidget(self.confidence_bar)
        
        layout.addWidget(bar_container, stretch=1)
        
        return widget
    
    def _get_confidence_color(self, value: int) -> str:
        """Get color based on confidence value (0-100)."""
        if value < 30:
            return STYLES['error']  # Red
        elif value < 60:
            return STYLES['warning']  # Orange
        elif value < 80:
            return "#FFD700"  # Gold
        else:
            return STYLES['success']  # Green
    
    def _get_confidence_status(self, value: int) -> str:
        """Get status text based on confidence value."""
        if value < 20:
            return "Low Interest"
        elif value < 40:
            return "Needs Work"
        elif value < 60:
            return "Warming Up"
        elif value < 80:
            return "Good Progress"
        else:
            return "High Confidence!"
    
    def _create_hints_panel(self) -> QFrame:
        """Create the Quick Hints display panel with pill-style cards."""
        frame = QFrame()
        frame.setObjectName("hintsFrame")
        frame.setStyleSheet(f"""
            #hintsFrame {{
                background-color: {STYLES['bg_secondary']};
                border-radius: {STYLES['radius_md']};
                border: 1px solid {STYLES['border_subtle']};
            }}
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        
        # Header row
        header_row = QHBoxLayout()
        header_row.setSpacing(6)
        
        header_icon = QLabel("💡")
        header_icon.setStyleSheet("font-size: 14px; background: transparent;")
        header_row.addWidget(header_icon)
        
        header = QLabel("INSIGHTS")
        header.setStyleSheet(f"""
            color: {STYLES['accent_cyan']};
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 1px;
            background: transparent;
        """)
        header_row.addWidget(header)
        header_row.addStretch()
        
        layout.addLayout(header_row)
        
        # Hint cards container
        self.hint_cards = []
        self.hint_star_buttons = []
        
        for i in range(3):
            card = self._create_hint_card(i)
            self.hint_cards.append(card)
            layout.addWidget(card)
        
        return frame
    
    def _create_hint_card(self, index: int) -> QWidget:
        """Create a single pill-style hint card with star button."""
        card = QWidget()
        card.setObjectName(f"hintCard{index}")
        card.setStyleSheet(f"""
            #hintCard{index} {{
                background-color: {STYLES['bg_tertiary']};
                border-radius: {STYLES['radius_sm']};
                border: 1px solid transparent;
            }}
            #hintCard{index}:hover {{
                border: 1px solid {STYLES['border_glow']};
            }}
        """)
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(10, 8, 8, 8)
        layout.setSpacing(8)
        
        # Hint text - make clickable
        label = QLabel("Waiting for analysis...")
        label.setObjectName(f"hintLabel{index}")
        label.setStyleSheet(f"""
            color: {STYLES['text_muted']};
            font-size: 12px;
            background: transparent;
            border: none;
        """)
        label.setWordWrap(True)
        label.setCursor(Qt.CursorShape.PointingHandCursor)
        label.mousePressEvent = lambda event, idx=index: self._show_insight_detail(idx)
        layout.addWidget(label, stretch=1)
        
        # Store reference
        if not hasattr(self, 'hint_labels'):
            self.hint_labels = []
        self.hint_labels.append(label)
        
        # Star button
        star_btn = QPushButton("☆")
        star_btn.setObjectName(f"starBtn{index}")
        star_btn.setFixedSize(28, 28)
        star_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        star_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {STYLES['text_muted']};
                border: 1px solid {STYLES['border_subtle']};
                border-radius: 14px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 215, 0, 0.15);
                color: #FFD700;
                border-color: #FFD700;
            }}
            QPushButton:pressed {{
                background-color: rgba(255, 215, 0, 0.25);
            }}
        """)
        star_btn.setToolTip("Star this hint for CRM")
        star_btn.clicked.connect(lambda checked, idx=index: self._star_hint(idx))
        self.hint_star_buttons.append(star_btn)
        layout.addWidget(star_btn)
        
        return card
    
    def _star_hint(self, index: int):
        """Star a hint - save it for CRM sync."""
        if index < len(self.hint_labels):
            hint_text = self.hint_labels[index].text()
            if hint_text and hint_text != "Waiting for analysis..." and hint_text != "...":
                # Visual feedback - fill the star
                btn = self.hint_star_buttons[index]
                btn.setText("★")
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: rgba(255, 215, 0, 0.2);
                        color: #FFD700;
                        border: 1px solid #FFD700;
                        border-radius: 14px;
                        font-size: 14px;
                    }}
                """)
                btn.setToolTip("Starred!")
                
                # Call API to save hint
                import threading
                def save_hint():
                    try:
                        import requests
                        response = requests.post(
                            f"{self.API_BASE_URL}/star-hint",
                            json={"hint_text": hint_text},
                            timeout=5
                        )
                        if response.status_code == 200:
                            print(f"[Sentinel] Starred hint: {hint_text[:30]}...")
                    except Exception as e:
                        print(f"[Sentinel] Failed to star hint: {e}")
                
                threading.Thread(target=save_hint, daemon=True).start()
    
    def _show_insight_detail(self, index: int):
        """Show insight detail panel for the clicked hint."""
        if index < len(self.hint_labels):
            hint_text = self.hint_labels[index].text()
            if hint_text and hint_text not in ["Waiting for analysis...", "..."]:
                # Close existing panel if different hint clicked
                if self.insight_panel and self.insight_panel.isVisible():
                    self.insight_panel.close()
                
                # Create new insight panel
                self.insight_panel = InsightDetailPanel(
                    parent_panel=self,
                    hint_text=hint_text,
                    context="Consider asking follow-up questions to explore this topic further."
                )
                self.insight_panel.show()
                print(f"[Sentinel] Showing insight: {hint_text[:30]}...")
    
    def _create_transcript_panel(self) -> QWidget:
        """Create enhanced transcript display with speaker indicators."""
        panel = QWidget()
        panel.setObjectName("transcriptPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        # Header row with speaker indicator
        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        
        header_icon = QLabel("📝")
        header_icon.setStyleSheet("font-size: 12px;")
        header_row.addWidget(header_icon)
        
        header = QLabel("TRANSCRIPT")
        header.setStyleSheet(f"""
            color: {STYLES['text_secondary']};
            font-size: 10px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        header_row.addWidget(header)
        
        header_row.addStretch()
        
        # Current speaker indicator
        self.speaker_indicator = QLabel("—")
        self.speaker_indicator.setStyleSheet(f"""
            color: {STYLES['text_muted']};
            font-size: 10px;
            padding: 2px 8px;
            background-color: {STYLES['bg_tertiary']};
            border-radius: 8px;
        """)
        header_row.addWidget(self.speaker_indicator)
        
        layout.addLayout(header_row)
        
        # Transcript text area with premium styling
        self.transcript_text = QTextEdit()
        self.transcript_text.setReadOnly(True)
        self.transcript_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {STYLES['bg_secondary']};
                color: {STYLES['text_primary']};
                border: 1px solid {STYLES['border_subtle']};
                border-radius: {STYLES['radius_sm']};
                font-size: 11px;
                font-family: {STYLES['font_family']};
                padding: 8px;
                selection-background-color: {STYLES['accent_cyan']};
            }}
            QScrollBar:vertical {{
                background-color: {STYLES['bg_tertiary']};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {STYLES['text_muted']};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {STYLES['accent_cyan']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        self.transcript_text.setMaximumHeight(140)
        self.transcript_text.setPlaceholderText("Waiting for transcript...")
        layout.addWidget(self.transcript_text)
        
        return panel
    
    def _format_speaker_text(self, text: str) -> str:
        """Format transcript text with colored speaker labels."""
        # Replace speaker tags with HTML colored versions
        formatted = text
        
        # Speaker 1 - cyan
        formatted = formatted.replace(
            "[SALES_REP]", 
            f'<span style="color: {STYLES["accent_cyan"]}; font-weight: bold;">[Speaker 1]</span>'
        )
        formatted = formatted.replace(
            "[SPEAKER_00]", 
            f'<span style="color: {STYLES["accent_cyan"]}; font-weight: bold;">[Speaker 1]</span>'
        )
        
        # Speaker 2 - gold
        formatted = formatted.replace(
            "[CLIENT]", 
            f'<span style="color: #FFD700; font-weight: bold;">[Speaker 2]</span>'
        )
        formatted = formatted.replace(
            "[SPEAKER_01]", 
            f'<span style="color: #FFD700; font-weight: bold;">[Speaker 2]</span>'
        )
        
        return formatted
    
    def update_speaker(self, speaker: str):
        """Update the current speaker indicator."""
        if "SALES" in speaker.upper() or "SPEAKER_00" in speaker or "1" in speaker:
            self.speaker_indicator.setText("🎤 Speaker 1")
            self.speaker_indicator.setStyleSheet(f"""
                color: {STYLES['accent_cyan']};
                font-size: 10px;
                font-weight: bold;
                padding: 2px 8px;
                background-color: rgba(0, 212, 255, 0.15);
                border: 1px solid rgba(0, 212, 255, 0.3);
                border-radius: 8px;
            """)
        elif "CLIENT" in speaker.upper() or "SPEAKER_01" in speaker or "2" in speaker:
            self.speaker_indicator.setText("👤 Speaker 2")
            self.speaker_indicator.setStyleSheet(f"""
                color: #FFD700;
                font-size: 10px;
                font-weight: bold;
                padding: 2px 8px;
                background-color: rgba(255, 215, 0, 0.15);
                border: 1px solid rgba(255, 215, 0, 0.3);
                border-radius: 8px;
            """)
        else:
            self.speaker_indicator.setText("—")
            self.speaker_indicator.setStyleSheet(f"""
                color: {STYLES['text_muted']};
                font-size: 10px;
                padding: 2px 8px;
                background-color: {STYLES['bg_tertiary']};
                border-radius: 8px;
            """)
    
    def _create_controls(self) -> QWidget:
        """Create premium control buttons with demo mode and battlecard."""
        controls = QWidget()
        main_layout = QVBoxLayout(controls)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)
        
        # Row 1: Primary actions
        row1 = QHBoxLayout()
        row1.setSpacing(8)
        
        # Start/Stop button - Gradient style
        self.start_btn = QPushButton("▶ Start Session")
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background: {STYLES['accent_gradient']};
                color: white;
                border: none;
                border-radius: {STYLES['radius_sm']};
                padding: 10px 20px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #33DDFF, stop:1 #66BFFF);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00AACC, stop:1 #3399CC);
            }}
        """)
        self.start_btn.clicked.connect(self._on_start_clicked)
        row1.addWidget(self.start_btn, stretch=1)
        
        # Battlecard button
        self.battlecard_btn = QPushButton("⚔")
        self.battlecard_btn.setFixedSize(36, 36)
        self.battlecard_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.battlecard_btn.setToolTip("Get Battlecard")
        self.battlecard_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {STYLES['bg_tertiary']};
                color: {STYLES['text_secondary']};
                border: 1px solid {STYLES['border_subtle']};
                border-radius: 18px;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 145, 0, 0.2);
                color: {STYLES['warning']};
                border-color: {STYLES['warning']};
            }}
        """)
        self.battlecard_btn.clicked.connect(self._show_battlecard)
        row1.addWidget(self.battlecard_btn)
        
        main_layout.addLayout(row1)
        
        # Row 2: Secondary actions
        row2 = QHBoxLayout()
        row2.setSpacing(8)
        
        # Demo Mode toggle
        self.demo_btn = QPushButton("🎬 Demo Mode")
        self.demo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.demo_btn.setCheckable(True)
        self.demo_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {STYLES['bg_tertiary']};
                color: {STYLES['text_secondary']};
                border: 1px solid {STYLES['border_subtle']};
                border-radius: {STYLES['radius_sm']};
                padding: 6px 12px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: rgba(79, 172, 254, 0.15);
                border-color: {STYLES['accent_blue']};
            }}
            QPushButton:checked {{
                background-color: rgba(79, 172, 254, 0.2);
                color: {STYLES['accent_cyan']};
                border-color: {STYLES['accent_cyan']};
            }}
        """)
        self.demo_btn.clicked.connect(self._toggle_demo_mode)
        row2.addWidget(self.demo_btn)
        
        # Audio Upload button
        self.upload_btn = QPushButton("🎤 Audio")
        self.upload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.upload_btn.setToolTip("Upload audio file")
        self.upload_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {STYLES['bg_tertiary']};
                color: {STYLES['text_secondary']};
                border: 1px solid {STYLES['border_subtle']};
                border-radius: {STYLES['radius_sm']};
                padding: 6px 12px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 230, 118, 0.15);
                border-color: {STYLES['success']};
                color: {STYLES['success']};
            }}
        """)
        self.upload_btn.clicked.connect(self._upload_audio)
        row2.addWidget(self.upload_btn)
        
        # Stealth toggle
        self.stealth_btn = QPushButton("[H] Stealth")
        self.stealth_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stealth_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {STYLES['bg_tertiary']};
                color: {STYLES['text_secondary']};
                border: 1px solid {STYLES['border_subtle']};
                border-radius: {STYLES['radius_sm']};
                padding: 6px 12px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 212, 255, 0.15);
                border-color: {STYLES['accent_cyan']};
            }}
        """)
        self.stealth_btn.clicked.connect(self._toggle_stealth)
        row2.addWidget(self.stealth_btn)
        
        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {STYLES['text_muted']};
                border: 1px solid {STYLES['border_subtle']};
                border-radius: 14px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 82, 82, 0.2);
                color: {STYLES['error']};
                border-color: {STYLES['error']};
            }}
        """)
        close_btn.clicked.connect(self.close)
        row2.addWidget(close_btn)
        
        main_layout.addLayout(row2)
        
        return controls
    
    def _toggle_demo_mode(self):
        """Toggle demo simulation mode."""
        is_demo = self.demo_btn.isChecked()
        if is_demo:
            self.demo_btn.setText("🎬 Demo ON")
            print("[Sentinel] Demo mode ENABLED")
            # Could trigger demo transcript playback here
        else:
            self.demo_btn.setText("🎬 Demo Mode")
            print("[Sentinel] Demo mode DISABLED")
    
    def _show_battlecard(self):
        """Show battlecard panel for competitor."""
        print("[Sentinel] Battlecard requested")
        
        # Close existing panel if open
        if self.battlecard_panel and self.battlecard_panel.isVisible():
            self.battlecard_panel.close()
        
        # Create new battlecard panel with sample data
        self.battlecard_panel = BattlecardPanel(
            parent_panel=self,
            competitor="Salesforce",
            counter_points=[
                "We offer 24/7 local support vs their offshore team",
                "Our implementation is 2x faster on average",
                "No hidden fees - transparent pricing model"
            ]
        )
        self.battlecard_panel.show()
        
        self.signals.battlecard_updated.connect(self._on_battlecard_updated)
        
        # Also try to fetch from API in background
        import threading
        def fetch_battlecard():
            try:
                import requests
                response = requests.post(
                    f"{self.API_BASE_URL}/battlecard",
                    json={"competitor_name": "Salesforce", "context": ""},
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    print(f"[Sentinel] Got battlecard from API: {data}")
                    
                    # Emit signal to update UI
                    # Expected format: {"competitor": "X", "points": ["A", "B"]}
                    self.signals.battlecard_updated.emit(data)
                    
            except Exception as e:
                print(f"[Sentinel] Battlecard API error: {e}")
        threading.Thread(target=fetch_battlecard, daemon=True).start()

    def _on_battlecard_updated(self, data: dict):
        """Update battlecard panel with API data."""
        if self.battlecard_panel:
            competitor = data.get("competitor", "Competitor")
            points = data.get("points", [])
            if points:
                self.battlecard_panel.set_content(competitor, points)
    
    def _upload_audio(self):
        """Open file dialog to upload audio."""
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Audio File",
            "",
            "Audio Files (*.wav *.mp3 *.m4a *.flac);;All Files (*)"
        )
        if file_path:
            print(f"[Sentinel] Selected audio: {file_path}")
            # Could trigger audio processing here
    
    def _toggle_demo_mode(self):
        """Toggle authenticated demo simulation."""
        self._demo_active = not self._demo_active
        
        if self._demo_active:
            print("[Sentinel] Demo Mode: STARTED")
            self.demo_btn.setText("🎬 Demo ON")
            self.demo_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(0, 230, 118, 0.2);
                    color: {STYLES['success']};
                    border: 1px solid {STYLES['success']};
                    border-radius: {STYLES['radius_sm']};
                    padding: 6px 12px;
                    font-size: 11px;
                }}
            """)
            
            # Start simulation timer
            if not self._demo_timer:
                self._demo_timer = QTimer()
                self._demo_timer.timeout.connect(self._run_demo_simulation)
            self._demo_timer.start(200) # Fast updates for smoothness
            
            # Initial state
            self.update_status("demo_active")
            
        else:
            print("[Sentinel] Demo Mode: STOPPED")
            self.demo_btn.setText("🎬 Demo Mode")
            self.demo_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {STYLES['bg_tertiary']};
                    color: {STYLES['text_secondary']};
                    border: 1px solid {STYLES['border_subtle']};
                    border-radius: {STYLES['radius_sm']};
                    padding: 6px 12px;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background-color: rgba(0, 212, 255, 0.15);
                    border-color: {STYLES['accent_cyan']};
                    color: {STYLES['accent_cyan']};
                }}
            """)
            
            if self._demo_timer:
                self._demo_timer.stop()
            
            self.update_status("idle")
            self.update_confidence(0)

    def _run_demo_simulation(self):
        """Run a simulation loop for demo purposes."""
        import random
        import time
        
        # 1. Animate Confidence
        if not hasattr(self, '_demo_conf'): self._demo_conf = 50
        if not hasattr(self, '_demo_conf_dir'): self._demo_conf_dir = 1
        
        self._demo_conf += self._demo_conf_dir
        if self._demo_conf >= 95: self._demo_conf_dir = -1
        if self._demo_conf <= 40: self._demo_conf_dir = 1
        
        self.update_confidence(int(self._demo_conf))
        
        # 2. Animate Talk Balance
        if not hasattr(self, '_demo_bal'): self._demo_bal = 50
        if not hasattr(self, '_demo_bal_dir'): self._demo_bal_dir = 1
        
        # Change direction randomly
        if random.random() < 0.05: 
            self._demo_bal_dir *= -1
            
        self._demo_bal += self._demo_bal_dir * 0.5
        self._demo_bal = max(20, min(80, self._demo_bal))
        
        self.update_talk_balance(int(self._demo_bal))
        
        # 3. Simulate Hints (every few seconds)
        if not hasattr(self, '_last_hint_time'): self._last_hint_time = 0
        current_time = time.time()
        
        if current_time - self._last_hint_time > 5:
            hints = [
                "Competitor Mentioned: Salesforce",
                "Pricing objection detected - emphasize ROI",
                "Ask about decision timeline",
                "Highlight 24/7 support availability",
                "Mention case study from similar industry",
                "Client seems interested in security features"
            ]
            
            new_hints = random.sample(hints, 3)
            self.update_hints(new_hints)
            self._last_hint_time = current_time
    
    # ==================== STEALTH MODE ====================
    
    def set_stealth_mode(self, enabled: bool):
        """
        Enable or disable stealth mode (hidden from screen capture).
        
        Uses Windows SetWindowDisplayAffinity API.
        Only works on Windows 10 version 2004+ (Build 19041+).
        """
        if sys.platform != 'win32':
            print("[Overlay] Stealth mode only supported on Windows")
            return False
        
        try:
            hwnd = int(self.winId())
            
            # Get function from user32
            user32 = ctypes.windll.user32
            
            affinity = WDA_EXCLUDEFROMCAPTURE if enabled else WDA_NONE
            result = user32.SetWindowDisplayAffinity(hwnd, affinity)
            
            if result:
                self._stealth_enabled = enabled
                self.stealth_indicator.setText("[H]" if enabled else "[V]")
                self.stealth_indicator.setStyleSheet(
                    f"color: {STYLES['success']}; font-size: 14px; padding: 2px 4px;" if enabled 
                    else "font-size: 14px; padding: 2px 4px;"
                )
                self.stealth_indicator.setToolTip(
                    "Stealth: ON (Hidden from capture)" if enabled 
                    else "Stealth: OFF"
                )
                self.stealth_btn.setText("[V] Visible" if enabled else "[H] Stealth")
                print(f"[Sentinel] Stealth mode: {'ENABLED' if enabled else 'DISABLED'}")
                return True
            else:
                print("[Overlay] SetWindowDisplayAffinity failed. May require Windows 10 2004+")
                return False
                
        except Exception as e:
            print(f"[Overlay] Stealth mode error: {e}")
            return False
    
    def _toggle_stealth(self):
        """Toggle stealth mode."""
        self.set_stealth_mode(not self._stealth_enabled)
    
    # ==================== UPDATE METHODS ====================
    
    def update_hints(self, hints: List[str]):
        """Thread-safe hint update via signal."""
        self.signals.hints_updated.emit(hints)
    
    def _on_hints_updated(self, hints: List[str]):
        """Update hint cards with new data."""
        for i, label in enumerate(self.hint_labels):
            if i < len(hints):
                current_text = label.text()
                new_text = hints[i]
                
                # Update text
                label.setText(new_text)
                label.setStyleSheet(f"""
                    color: {STYLES['text_primary']};
                    font-size: 12px;
                    background: transparent;
                    border: none;
                """)
                
                # Check if text changed to trigger pulse
                if current_text != new_text:
                    self._pulse_hint_card(i)
                    
                    # Reset star button for new hint
                    if i < len(self.hint_star_buttons):
                        btn = self.hint_star_buttons[i]
                        btn.setText("☆")
                        btn.setStyleSheet(f"""
                            QPushButton {{
                                background-color: transparent;
                                color: {STYLES['text_muted']};
                                border: 1px solid {STYLES['border_subtle']};
                                border-radius: 14px;
                                font-size: 14px;
                            }}
                            QPushButton:hover {{
                                background-color: rgba(255, 215, 0, 0.15);
                                color: #FFD700;
                                border-color: #FFD700;
                            }}
                        """)
                        btn.setToolTip("Star this hint for CRM")
            else:
                label.setText("...")
                label.setStyleSheet(f"""
                    color: {STYLES['text_muted']};
                    font-size: 12px;
                    background: transparent;
                    border: none;
                """)

    def _pulse_hint_card(self, index: int):
        """Temporarily highlight a hint card to show it updated."""
        if index < len(self.hint_cards):
            card = self.hint_cards[index]
            # Pulse style
            card.setStyleSheet(f"""
                #hintCard{index} {{
                    background-color: {STYLES['bg_tertiary']};
                    border-radius: {STYLES['radius_sm']};
                    border: 1px solid {STYLES['border_glow']};
                    border-bottom: 2px solid {STYLES['accent_cyan']};
                }}
            """)
            
            # Revert after 800ms
            QTimer.singleShot(800, lambda: card.setStyleSheet(f"""
                #hintCard{index} {{
                    background-color: {STYLES['bg_tertiary']};
                    border-radius: {STYLES['radius_sm']};
                    border: 1px solid transparent;
                }}
                #hintCard{index}:hover {{
                    border: 1px solid {STYLES['border_glow']};
                }}
            """))
    
    def update_confidence(self, value: int):
        """Thread-safe confidence update via signal."""
        self.signals.confidence_updated.emit(max(0, min(100, value)))
    
    def _on_confidence_updated(self, value: int):
        """Update confidence meter with animation."""
        self._current_confidence = value
        color = self._get_confidence_color(value)
        status = self._get_confidence_status(value)
        
        # Update value label with color
        self.confidence_value.setText(f"{value}%")
        self.confidence_value.setStyleSheet(f"""
            color: {color};
            font-size: 24px;
            font-weight: bold;
            background: transparent;
            border: none;
        """)
        
        # Update status text
        self.confidence_status.setText(status)
        self.confidence_status.setStyleSheet(f"""
            color: {color};
            font-size: 10px;
            background: transparent;
            border: none;
        """)
        
        # Update progress bar
        self.confidence_bar.setValue(value)
        self.confidence_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {STYLES['bg_tertiary']};
                border-radius: 4px;
                border: none;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 4px;
            }}
        """)
    
    def update_transcript(self, text: str):
        """Thread-safe transcript update via signal."""
        self.signals.transcript_updated.emit(text)
    
    def _on_transcript_updated(self, text: str):
        """Append to transcript display with speaker formatting."""
        # Detect speaker from text
        if "[SALES_REP]" in text or "[SPEAKER_00]" in text:
            self.update_speaker("SALES_REP")
        elif "[CLIENT]" in text or "[SPEAKER_01]" in text:
            self.update_speaker("CLIENT")
        
        # Format text with colored speaker labels
        formatted_text = self._format_speaker_text(text)
        
        # Append as HTML
        current_html = self.transcript_text.toHtml()
        if "Waiting for transcript" in current_html or not self.transcript_text.toPlainText():
            self.transcript_text.setHtml(formatted_text)
        else:
            # Append to existing content
            self.transcript_text.append(formatted_text)
        
        # Smooth auto-scroll to bottom
        QTimer.singleShot(50, self._scroll_transcript_to_bottom)
    
    def _scroll_transcript_to_bottom(self):
        """Scroll transcript to bottom."""
        scrollbar = self.transcript_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def update_status(self, status: str):
        """Thread-safe status update via signal."""
        self.signals.status_updated.emit(status)
    
    def _on_status_updated(self, status: str):
        """Update status indicator with premium styling."""
        status_lower = status.lower()
        
        if status_lower == "running":
            # Start pulsing animation
            self._pulse_timer.start(500)  # Pulse every 500ms
            self.status_label.setText("LIVE")
            self.status_label.setStyleSheet(f"""
                color: {STYLES['success']};
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 1px;
            """)
            self.live_dot.setStyleSheet(f"color: {STYLES['success']}; font-size: 10px;")
            self.live_container.setStyleSheet(f"""
                background-color: rgba(0, 230, 118, 0.15);
                border: 1px solid rgba(0, 230, 118, 0.3);
                border-radius: 10px;
            """)
            self.start_btn.setText("⏹ Stop")
            self.start_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {STYLES['error']};
                    color: white;
                    border: none;
                    border-radius: {STYLES['radius_sm']};
                    padding: 10px 20px;
                    font-weight: bold;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: #FF6B6B;
                }}
            """)
            self.set_vision_state("active")
            
        elif status_lower == "processing":
            self._pulse_timer.stop()
            self.status_label.setText("PROCESSING")
            self.status_label.setStyleSheet(f"""
                color: {STYLES['warning']};
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 1px;
            """)
            self.live_dot.setStyleSheet(f"color: {STYLES['warning']}; font-size: 10px;")
            self.live_container.setStyleSheet(f"""
                background-color: rgba(255, 145, 0, 0.15);
                border: 1px solid rgba(255, 145, 0, 0.3);
                border-radius: 10px;
            """)
            
        elif status_lower == "completed":
            self._pulse_timer.stop()
            self.status_label.setText("COMPLETE")
            self.status_label.setStyleSheet(f"""
                color: {STYLES['accent_cyan']};
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 1px;
            """)
            self.live_dot.setStyleSheet(f"color: {STYLES['accent_cyan']}; font-size: 10px;")
            self.live_container.setStyleSheet(f"""
                background-color: rgba(0, 212, 255, 0.15);
                border: 1px solid rgba(0, 212, 255, 0.3);
                border-radius: 10px;
            """)
            self._reset_start_button()
            self.set_vision_state("inactive")
            
        else:
            self._pulse_timer.stop()
            self.status_label.setText(status.upper() if status else "IDLE")
            self.status_label.setStyleSheet(f"""
                color: {STYLES['text_muted']};
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 1px;
            """)
            self.live_dot.setStyleSheet(f"color: {STYLES['text_muted']}; font-size: 10px;")
            self.live_container.setStyleSheet(f"""
                background-color: {STYLES['bg_tertiary']};
                border-radius: 10px;
            """)
            self._reset_start_button()
            self.set_vision_state("inactive")
    
    def _reset_start_button(self):
        """Reset start button to initial state."""
        self.start_btn.setText("▶ Start Session")
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background: {STYLES['accent_gradient']};
                color: white;
                border: none;
                border-radius: {STYLES['radius_sm']};
                padding: 10px 20px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #33DDFF, stop:1 #66BFFF);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00AACC, stop:1 #3399CC);
            }}
        """)
    
    def update_entities(self, entities: List[str]):
        """Thread-safe entities update via signal."""
        self.signals.entities_updated.emit(entities)
    
    def _on_entities_updated(self, entities: List[str]):
        """Update entities label."""
        if entities:
            text = "Entities: " + ", ".join(entities[:5])
            if len(entities) > 5:
                text += f" (+{len(entities)-5} more)"
            self.entities_label.setText(text)
            self.entities_label.setStyleSheet("color: #8BC34A; font-size: 11px;")
        else:
            self.entities_label.setText("Entities: None detected")
            self.entities_label.setStyleSheet("color: #888; font-size: 11px;")
    
    # ==================== EVENT HANDLERS ====================
    
    # API Configuration
    API_BASE_URL = "http://10.119.65.34:8000/api/v1"
    
    def _on_start_clicked(self):
        """Handle start/stop button click."""
        if self._is_recording:
            self._stop_session()
        else:
            self._start_session()
    
    def _start_session(self):
        """Start the capture session via API."""
        import requests
        import threading
        
        self.update_status("starting")
        self.transcript_text.clear()
        print("[Overlay] Starting session via API...")
        
        def call_api():
            try:
                response = requests.post(
                    f"{self.API_BASE_URL}/start-session",
                    json={},
                    timeout=30
                )
                if response.status_code == 200:
                    self._is_recording = True
                    self.update_status("running")
                    print(f"[Overlay] Session started: {response.json()}")
                    # Start WebSocket connection for updates
                    self._connect_websocket()
                else:
                    print(f"[Overlay] Start failed: {response.status_code} - {response.text}")
                    self.update_status("error")
            except Exception as e:
                print(f"[Overlay] API error: {e}")
                self.update_status("error")
        
        # Run API call in background thread
        threading.Thread(target=call_api, daemon=True).start()
    
    def _stop_session(self):
        """Stop the capture session via API."""
        import requests
        import threading
        
        self.update_status("processing")
        print("[Overlay] Stopping session via API...")
        
        def call_api():
            try:
                response = requests.post(
                    f"{self.API_BASE_URL}/stop-session",
                    timeout=60  # May take time to process
                )
                self._is_recording = False
                if response.status_code == 200:
                    result = response.json()
                    print(f"[Overlay] Session stopped: {result}")
                    self.update_status("completed")
                else:
                    print(f"[Overlay] Stop failed: {response.status_code}")
                    self.update_status("idle")
            except Exception as e:
                print(f"[Overlay] API error: {e}")
                self._is_recording = False
                self.update_status("idle")
        
        threading.Thread(target=call_api, daemon=True).start()
    
    def _connect_websocket(self):
        """Connect to WebSocket for real-time updates."""
        import threading
        import json
        
        def ws_thread():
            try:
                import websocket
                
                ws_url = self.API_BASE_URL.replace("http://", "ws://") + "/session-stream"
                
                reconnect_count = 0
                max_reconnects = 5
                
                while self._is_recording and reconnect_count < max_reconnects:
                    print(f"[Overlay] Connecting to WebSocket: {ws_url}")
                    
                    ws_connected = False
                    
                    def on_message(ws, message):
                        try:
                            data = json.loads(message)
                            msg_type = data.get("type")
                            
                            if msg_type == "hints":
                                print(f"[Overlay DEBUG] Received hints: {data.get('hints')}")
                                self.update_hints(data.get("hints", []))
                            elif msg_type == "transcript":
                                print(f"[Overlay DEBUG] Received transcript: {len(data.get('text', ''))} chars")
                                self.update_transcript(data.get("text", ""))
                            elif msg_type == "status":
                                status = data.get("status", "")
                                print(f"[Overlay DEBUG] Received status: {status}")
                                if status and status != "ping":
                                    self.update_status(status)
                            elif msg_type == "entities":
                                self.update_entities(data.get("entities", []))
                            elif msg_type == "ping":
                                # Server keep-alive, ignore
                                pass
                        except Exception as e:
                            print(f"[Overlay] WS message error: {e}")
                    
                    def on_error(ws, error):
                        print(f"[Overlay] WS error: {error}")
                    
                    def on_close(ws, close_status_code=None, close_msg=None):
                        nonlocal ws_connected
                        ws_connected = False
                        print("[Overlay] WS closed")
                    
                    def on_open(ws):
                        nonlocal ws_connected, reconnect_count
                        ws_connected = True
                        reconnect_count = 0  # Reset on successful connect
                        print("[Overlay] WS connected!")
                        # Send initial ping to test connection
                        try:
                            ws.send("ping")
                        except:
                            pass
                    
                    ws = websocket.WebSocketApp(
                        ws_url,
                        on_message=on_message,
                        on_error=on_error,
                        on_close=on_close,
                        on_open=on_open
                    )
                    
                    # Run with ping interval
                    ws.run_forever(
                        ping_interval=20,
                        ping_timeout=10
                    )
                    
                    # If we get here, connection closed
                    if self._is_recording:
                        reconnect_count += 1
                        print(f"[Overlay] Reconnecting ({reconnect_count}/{max_reconnects})...")
                        import time
                        time.sleep(2)  # Reconnect delay
                        
            except ImportError:
                print("[Overlay] websocket-client not installed, using polling instead")
                self._poll_for_updates()
            except Exception as e:
                print(f"[Overlay] WebSocket error: {e}")
                import traceback
                traceback.print_exc()
        
        threading.Thread(target=ws_thread, daemon=True).start()
    
    def _poll_for_updates(self):
        """Fallback: Poll API for updates if WebSocket unavailable."""
        import requests
        import time
        
        print("[Overlay] Polling for updates...")
        while self._is_recording:
            try:
                response = requests.get(f"{self.API_BASE_URL}/session-status", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    hints = data.get("hints", [])
                    if hints:
                        self.update_hints(hints)
                    entities = data.get("entities", [])
                    if entities:
                        self.update_entities(entities)
            except:
                pass
            time.sleep(2)
    
    def mousePressEvent(self, event):
        """Enable window dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle window dragging and notify snapped panels."""
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, '_drag_pos'):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            
            # Make snapped panels follow
            if self.insight_panel and self.insight_panel.is_snapped:
                self.insight_panel.follow_parent()
            if self.battlecard_panel and self.battlecard_panel.is_snapped:
                self.battlecard_panel.follow_parent()
                
            event.accept()


def run_overlay():
    """Run the overlay as a standalone application."""
    app = QApplication(sys.argv)
    
    # Set app-wide dark theme
    app.setStyle("Fusion")
    
    overlay = StealthOverlay()
    overlay.show()
    
    # Demo: Update with sample data
    QTimer.singleShot(1000, lambda: overlay.update_hints([
        "Client mentioned Salesforce - prepare battlecard",
        "Ask about current pain points",
        "Listen for budget signals"
    ]))
    
    sys.exit(app.exec())


if __name__ == "__main__":
    run_overlay()
