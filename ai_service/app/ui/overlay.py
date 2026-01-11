"""
TF Overlay UI - Premium stealth assistant for real-time sales intelligence.

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

# Audio capture imports for distributed deployment
import threading
import time
import io
import wave
import numpy as np
import sounddevice as sd


class ClientAudioCapture:
    """
    Client-side audio capture for distributed deployment.
    Captures audio from local Stereo Mix and streams to backend.
    """
    
    def __init__(self, api_base_url: str, chunk_duration: float = 10.0):
        self.api_base_url = api_base_url
        self.chunk_duration = chunk_duration
        self._running = False
        self._audio_thread = None
        self._audio_buffer = []
        self._buffer_start_time = 0
        self._sample_rate = 16000
        self._ws = None
        
    def _get_loopback_device(self):
        """Find Stereo Mix or loopback device."""
        try:
            devices = sd.query_devices()
            
            # Priority: Stereo Mix
            for i, device in enumerate(devices):
                name = device['name'].lower()
                if 'stereo mix' in name and device['max_input_channels'] > 0:
                    rate = int(device['default_samplerate'])
                    print(f"[ClientAudio] Found Stereo Mix: {device['name']} ({rate}Hz)")
                    return (i, rate)
            
            # Fallback: Default input
            default = sd.query_devices(kind='input')
            rate = int(default['default_samplerate'])
            print(f"[ClientAudio] Using default input: {default['name']} ({rate}Hz)")
            return (None, rate)
            
        except Exception as e:
            print(f"[ClientAudio] Device error: {e}")
            return (None, 44100)
    
    def start(self):
        """Start audio capture and streaming."""
        if self._running:
            return
        
        self._running = True
        self._audio_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._audio_thread.start()
        print("[ClientAudio] Started")
    
    def stop(self):
        """Stop audio capture."""
        self._running = False
        if self._ws:
            try:
                self._ws.close()
            except:
                pass
        print("[ClientAudio] Stopped")
    
    def _capture_loop(self):
        """Main audio capture loop."""
        import websocket
        
        # Connect to backend audio stream endpoint
        ws_url = self.api_base_url.replace("http://", "ws://") + "/audio-stream"
        
        while self._running:
            stream = None
            try:
                print(f"[ClientAudio] Connecting to {ws_url}...")
                # Simple connection with longer timeout
                # Note: ping_interval/ping_timeout only work with WebSocketApp, not create_connection
                self._ws = websocket.create_connection(
                    ws_url, 
                    timeout=60,  # Longer timeout for slow networks
                    skip_utf8_validation=True  # We're sending binary audio data
                )
                print("[ClientAudio] Connected to backend")
                
                # Track connection health
                self._last_send_time = time.time()
                self._send_error_count = 0
                
                # Get audio device
                device_id, native_rate = self._get_loopback_device()
                self._sample_rate = native_rate
                self._audio_buffer = []
                self._buffer_start_time = time.time()
                
                def audio_callback(indata, frames, time_info, status):
                    if status:
                        print(f"[ClientAudio] Status: {status}")
                    
                    self._audio_buffer.append(indata.copy())
                    
                    # Check if we have enough for a chunk
                    total_samples = sum(len(chunk) for chunk in self._audio_buffer)
                    chunk_samples = int(self.chunk_duration * self._sample_rate)
                    
                    if total_samples >= chunk_samples:
                        self._send_chunk()
                
                # Open audio stream with fallback
                try:
                    print(f"[ClientAudio] Opening stream on device {device_id} at {native_rate}Hz...")
                    stream = sd.InputStream(
                        device=device_id,
                        samplerate=native_rate,
                        channels=1,
                        dtype=np.float32,
                        callback=audio_callback,
                        blocksize=1024
                    )
                except Exception as e:
                    if device_id is not None:
                        print(f"[ClientAudio] Failed to open preferred device ({e}). Falling back to default input...")
                        device_id = None
                        # Query default rate
                        default = sd.query_devices(kind='input')
                        native_rate = int(default['default_samplerate'])
                        self._sample_rate = native_rate
                        
                        stream = sd.InputStream(
                            device=None,
                            samplerate=native_rate,
                            channels=1,
                            dtype=np.float32,
                            callback=audio_callback,
                            blocksize=1024
                        )
                    else:
                        raise e  # Already on default, just fail
                
                stream.start()
                print("[ClientAudio] Audio stream active")
                
                # Keep alive while running
                while self._running and stream.active:
                    time.sleep(1.0)
                    
                    # Check if too many send errors occurred
                    if self._send_error_count >= 3:
                        print("[ClientAudio] Too many send errors, reconnecting...")
                        break
                    
                    # Check for server messages (ACK/ping) periodically
                    try:
                        self._ws.settimeout(0.1)
                        msg = self._ws.recv()
                        if msg in ("ACK", "ping"):
                            # Server is alive, reset last send time
                            self._last_send_time = time.time()
                    except websocket.WebSocketTimeoutException:
                        pass  # Normal - no message
                    except Exception:
                        pass
                    finally:
                        self._ws.settimeout(60)
                    
                    # Check if we haven't sent anything in 90s (increased from 30s)
                    if time.time() - self._last_send_time > 90:
                        print(f"[ClientAudio] Connection idle for 90s, reconnecting...")
                        break
                
            except websocket.WebSocketConnectionClosedException:
                print("[ClientAudio] Connection closed by server, reconnecting in 2s...")
                time.sleep(2)
            except Exception as e:
                print(f"[ClientAudio] Error (retrying in 3s): {e}")
                time.sleep(3)
            
            finally:
                if stream:
                    try:
                        stream.stop()
                        stream.close()
                    except:
                        pass
                if self._ws:
                    try:
                        self._ws.close()
                    except:
                        pass
                    self._ws = None
    
    def _send_chunk(self):
        """Send accumulated audio to backend."""
        if not self._audio_buffer or not self._ws:
            return
        
        try:
            # Concatenate audio
            audio_data = np.concatenate(self._audio_buffer, axis=0)
            
            # Convert to WAV bytes
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self._sample_rate)
                # Convert float32 to int16
                audio_int16 = (audio_data * 32767).astype(np.int16)
                wf.writeframes(audio_int16.tobytes())
            
            # Send binary data
            self._ws.send_binary(wav_buffer.getvalue())
            
            # Update tracking on success
            self._last_send_time = time.time()
            self._send_error_count = 0  # Reset on success
            print(f"[ClientAudio] Sent {len(audio_data)/self._sample_rate:.1f}s chunk")
            
        except Exception as e:
            self._send_error_count = getattr(self, '_send_error_count', 0) + 1
            print(f"[ClientAudio] Send error ({self._send_error_count}/3): {e}")
        
        # Reset buffer regardless of success/failure
        self._audio_buffer = []
        self._buffer_start_time = time.time()




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
    "font_heading": "18px",
    "font_body": "16px",
    "font_small": "14px",
    
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
        self.resize(340, 260)
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
            font-size: 12px;
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
            font-size: 15px;
            padding: 8px;
            background-color: {STYLES['bg_secondary']};
            border-radius: {STYLES['radius_sm']};
        """)
        layout.addWidget(self.insight_label)
        
        # Context/suggestion - use provided context or placeholder
        context_text = f"► {self.context}" if self.context else "► Analyzing conversation for suggested actions..."
        self.context_label = QLabel(context_text)
        self.context_label.setWordWrap(True)
        self.context_label.setStyleSheet(f"""
            color: {STYLES['text_secondary']};
            font-size: 14px;
            padding: 4px;
        """)
        layout.addWidget(self.context_label)
        
        layout.addStretch()
        
    def set_content(self, hint_text, context=""):
        """Update the panel content."""
        self.hint_text = hint_text
        self.insight_label.setText(hint_text)
        if context:
            self.context_label.setText(f"► {context}")


class BattlecardPanel(FloatingPanel):
    """Panel showing competitor battlecard information."""
    
    def __init__(self, parent_panel=None, competitor="", counter_points=None):
        super().__init__(parent_panel, snap_side='right')
        self.competitor = competitor or "Competitor"
        self.counter_points = counter_points or []
        self._setup_ui()
        self.resize(360, 320)
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
        header = QLabel("BATTLECARD")
        header.setStyleSheet(f"""
            color: {STYLES['warning']};
            font-size: 12px;
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
            font-size: 18px;
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
        point = QLabel(f"• {text}")
        point.setWordWrap(True)
        point.setStyleSheet(f"""
            color: {STYLES['text_secondary']};
            font-size: 14px;
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
    connection_updated = pyqtSignal(str)  # 'connecting', 'connected', 'disconnected', 'error'
    error_updated = pyqtSignal(str)       # Error message to display
    face_sentiment_updated = pyqtSignal(dict)  # {happy: int, negative: int}


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
        
        # Battlecard state: track if dismissed and if there's pending data
        self._battlecard_dismissed = False  # User closed it manually
        self._battlecard_shown_once = False  # Has been shown at least once
        self._pending_battlecard_data = None  # Store latest data for button click
        
        # Demo mode state
        self._demo_active = False
        self._demo_timer = None
        
        # Client-side audio capture for distributed deployment
        self._audio_capture = None
        
        # Client-side face sentiment state
        self._face_sentiment_running = False
        self._face_sentiment_happy = 0
        self._face_sentiment_negative = 0
        
        # Signal bridge for thread-safe updates
        self.signals = SignalBridge()
        self.signals.hints_updated.connect(self._on_hints_updated)
        self.signals.transcript_updated.connect(self._on_transcript_updated)
        self.signals.status_updated.connect(self._on_status_updated)
        self.signals.entities_updated.connect(self._on_entities_updated)
        self.signals.confidence_updated.connect(self._on_confidence_updated)
        self.signals.connection_updated.connect(self.update_connection_status)
        self.signals.error_updated.connect(self.show_error)
        self.signals.face_sentiment_updated.connect(self._on_face_sentiment_updated)
        self.signals.battlecard_updated.connect(self._on_battlecard_updated)
        
        self._setup_ui()
        self._setup_window()
        
    def _setup_window(self):
        """Configure window properties."""
        self.setWindowTitle("TW-Assistant - Sales Intelligence")
        
        # Frameless, always on top, tool window (doesn't show in taskbar)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        
        # Transparent background
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Position: Bottom-right corner - larger for better visibility
        self.resize(380, 700)
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
        
        # Speaker Intelligence Strip (removed)
        # self.speaker_strip = self._create_speaker_strip()
        # layout.addWidget(self.speaker_strip)
        
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
        
        # Face Sentiment Counters (😊 happy / 😠 negative)
        sentiment_row = QHBoxLayout()
        sentiment_row.setSpacing(12)
        
        self.happy_label = QLabel("😊 0")
        self.happy_label.setStyleSheet(f"""
            color: {STYLES['success']};
            background: rgba(0, 230, 118, 0.15);
            font-size: 13px;
            font-weight: bold;
            padding: 4px 10px;
            border-radius: 8px;
        """)
        self.happy_label.setToolTip("Happy/Neutral Faces Detected")
        sentiment_row.addWidget(self.happy_label)
        
        self.negative_label = QLabel("😠 0")
        self.negative_label.setStyleSheet(f"""
            color: {STYLES['error']};
            background: rgba(255, 82, 82, 0.15);
            font-size: 13px;
            font-weight: bold;
            padding: 4px 10px;
            border-radius: 8px;
        """)
        self.negative_label.setToolTip("Negative Faces Detected")
        sentiment_row.addWidget(self.negative_label)
        
        # Sentiment Indicator Box (inline with emojis)
        self.sentiment_box = QLabel("Analyzing...")
        self.sentiment_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sentiment_box.setStyleSheet(f"""
            QLabel {{
                color: {STYLES['text_secondary']};
                background: {STYLES['bg_tertiary']};
                font-size: 11px;
                font-weight: bold;
                padding: 4px 8px;
                border-radius: 8px;
                border: 1px solid {STYLES['border_subtle']};
            }}
        """)
        self.sentiment_box.setToolTip("Client engagement indicator based on facial sentiment")
        sentiment_row.addWidget(self.sentiment_box)
        
        sentiment_row.addStretch()
        layout.addLayout(sentiment_row)
        
        # Track last sentiment state for animation
        self._last_sentiment_state = "neutral"
        
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
        logo = QLabel("")
        logo.setStyleSheet(f"""
            color: {STYLES['accent_cyan']};
            font-size: 16px;
            font-weight: bold;
        """)
        brand_layout.addWidget(logo)
        
        # Brand name
        title = QLabel("TW-Assistant")
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
        
        self.live_dot = QLabel("LIVE")
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
        self.vision_indicator = QLabel("VISION")
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
        
        # WebSocket connection status indicator
        self.connection_indicator = QLabel("CONN")
        self.connection_indicator.setStyleSheet(f"font-size: 12px; padding: 2px 4px; color: {STYLES['text_muted']};")
        self.connection_indicator.setToolTip("Backend: Not Connected")
        layout.addWidget(self.connection_indicator)
        
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
        self.talk_balance_bar.setMinimumWidth(100)  # Ensure bar has width to render
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
        """Update the talk-time balance indicator (disabled - widget removed)."""
        pass  # Speaker strip removed from UI
    
    def update_connection_status(self, status: str):
        """Update WebSocket connection status indicator.
        
        Args:
            status: 'connecting', 'connected', 'disconnected', or 'error'
        """
        states = {
            "connecting": ("CONN", STYLES['warning'], "Backend: Connecting..."),
            "connected": ("CONN", STYLES['success'], "Backend: Connected"),
            "disconnected": ("CONN", STYLES['text_muted'], "Backend: Disconnected"),
            "error": ("ERROR", STYLES['error'], "Backend: Connection Error"),
        }
        emoji, color, tooltip = states.get(status, states["disconnected"])
        self.connection_indicator.setText(emoji)
        self.connection_indicator.setStyleSheet(f"font-size: 10px; font-weight: bold; padding: 2px 4px; color: {color};")
        self.connection_indicator.setToolTip(tooltip)
    
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
            "inactive": ("VISION", f"color: {STYLES['text_muted']};", "Vision: Inactive"),
            "active": ("VISION", f"color: {STYLES['accent_cyan']};", "Vision: Scanning"),
            "detected": ("VISION", f"color: {STYLES['success']};", "Vision: Entity Detected"),
        }
        emoji, style, tooltip = states.get(state, states["inactive"])
        self.vision_indicator.setText(emoji)
        self.vision_indicator.setStyleSheet(f"{style} font-size: 10px; font-weight: bold; padding: 2px 4px;")
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
        
        header_icon = QLabel("")
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
        label = QLabel("Waiting for AI insights...")
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
        star_btn = QPushButton("Save")
        star_btn.setObjectName(f"starBtn{index}")
        star_btn.setFixedSize(40, 20)
        star_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        star_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {STYLES['text_muted']};
                border: 1px solid {STYLES['border_subtle']};
                border-radius: 4px;
                font-size: 9px;
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
            if hint_text and hint_text != "Waiting for AI insights..." and hint_text != "...":
                # Visual feedback - fill the star
                btn = self.hint_star_buttons[index]
                btn.setText("Saved")
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
                            print(f"[TF] Starred hint: {hint_text[:30]}...")
                    except Exception as e:
                        print(f"[TF] Failed to star hint: {e}")
                
                threading.Thread(target=save_hint, daemon=True).start()
    
    def _show_insight_detail(self, index: int):
        """Show insight detail panel for the clicked hint."""
        if index < len(self.hint_labels):
            hint_text = self.hint_labels[index].text()
            if hint_text and hint_text not in ["Waiting for AI insights...", "..."]:
                # Close existing panel if different hint clicked
                if self.insight_panel and self.insight_panel.isVisible():
                    self.insight_panel.close()
                
                # Use demo context if available (demo mode), otherwise generate dynamically
                if hasattr(self, '_demo_context') and self._demo_context:
                    context = self._demo_context
                else:
                    context = self._get_insight_context(hint_text)
                
                # Create new insight panel
                self.insight_panel = InsightDetailPanel(
                    parent_panel=self,
                    hint_text=hint_text,
                    context=context
                )
                self.insight_panel.show()
                # Apply stealth mode if enabled
                if self._stealth_enabled:
                    self._apply_stealth_to_window(self.insight_panel, True)
                print(f"[TF] Showing insight: {hint_text[:30]}...")
    
    def _get_insight_context(self, hint_text: str) -> str:
        """Generate contextual suggestion based on hint content."""
        hint_lower = hint_text.lower()
        
        if "discount" in hint_lower or "price" in hint_lower or "%" in hint_text:
            return "Use this pricing leverage to close the deal. Ask about their budget timeline."
        elif "competitor" in hint_lower or "salesforce" in hint_lower:
            return "Highlight our key differentiators. Focus on faster implementation and better support."
        elif "budget" in hint_lower:
            return "Probe for budget flexibility. Offer flexible payment options if needed."
        elif "decision" in hint_lower or "roadmap" in hint_lower or "timeline" in hint_lower:
            return "Establish clear next steps and timeline. Schedule a follow-up meeting."
        elif "pain" in hint_lower or "problem" in hint_lower or "challenge" in hint_lower:
            return "Dig deeper into their pain points. Show empathy and relate to similar customer stories."
        elif "demo" in hint_lower or "trial" in hint_lower:
            return "Offer a personalized demo or trial period to let them experience the value firsthand."
        else:
            return "Explore this topic further with clarifying questions. Listen for buying signals."
    
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
        
        header_icon = QLabel("")
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
        
        # Current speaker indicator (removed)
        # self.speaker_indicator = QLabel("—")
        # self.speaker_indicator.setStyleSheet(f"""
        #     color: {STYLES['text_muted']};
        #     font-size: 10px;
        #     padding: 2px 8px;
        #     background-color: {STYLES['bg_tertiary']};
        #     border-radius: 8px;
        # """)
        # header_row.addWidget(self.speaker_indicator)
        
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
                font-size: 16px;
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
        self.transcript_text.setMaximumHeight(400)
        self.transcript_text.setPlaceholderText("Waiting for transcript...")
        layout.addWidget(self.transcript_text)
        
        return panel
    
    def _format_speaker_text(self, text: str) -> str:
        """Format transcript text with colored speaker labels on separate lines."""
        # Replace speaker tags with HTML colored versions (with line break before)
        formatted = text
        
        # Speaker 1 - cyan (add line break before for separation)
        formatted = formatted.replace(
            "[SALES_REP]", 
            f'<br><span style="color: {STYLES["accent_cyan"]}; font-weight: bold;">[Speaker 1]</span>'
        )
        formatted = formatted.replace(
            "[SPEAKER_00]", 
            f'<br><span style="color: {STYLES["accent_cyan"]}; font-weight: bold;">[Speaker 1]</span>'
        )
        formatted = formatted.replace(
            "[Speaker 1]", 
            f'<br><span style="color: {STYLES["accent_cyan"]}; font-weight: bold;">[Speaker 1]</span>'
        )
        
        # Speaker 2 - gold (add line break before for separation)
        formatted = formatted.replace(
            "[CLIENT]", 
            f'<br><span style="color: #FFD700; font-weight: bold;">[Speaker 2]</span>'
        )
        formatted = formatted.replace(
            "[SPEAKER_01]", 
            f'<br><span style="color: #FFD700; font-weight: bold;">[Speaker 2]</span>'
        )
        formatted = formatted.replace(
            "[Speaker 2]", 
            f'<br><span style="color: #FFD700; font-weight: bold;">[Speaker 2]</span>'
        )
        
        # Clean up any leading <br> at the start
        if formatted.startswith('<br>'):
            formatted = formatted[4:]
        
        return formatted
    
    def update_speaker(self, speaker: str):
        """Update the current speaker indicator (disabled - widget removed)."""
        pass  # Speaker indicator removed from UI
    
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
        self.start_btn = QPushButton("Start")
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background: {STYLES['accent_gradient']};
                color: white;
                border: none;
                border-radius: {STYLES['radius_sm']};
                padding: 10px 20px;
                font-weight: bold;
                font-size: 11px;
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
        self.battlecard_btn = QPushButton("Battlecard")
        self.battlecard_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.battlecard_btn.setToolTip("Show Battlecard")
        
        # Store normal and highlight styles for battlecard button
        self._battlecard_btn_normal_style = f"""
            QPushButton {{
                background-color: {STYLES['bg_tertiary']};
                color: {STYLES['text_secondary']};
                border: 1px solid {STYLES['border_subtle']};
                border-radius: {STYLES['radius_sm']};
                padding: 10px 16px;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 145, 0, 0.2);
                color: {STYLES['warning']};
                border-color: {STYLES['warning']};
            }}
        """
        self._battlecard_btn_highlight_style = f"""
            QPushButton {{
                background-color: rgba(255, 145, 0, 0.3);
                color: {STYLES['warning']};
                border: 2px solid {STYLES['warning']};
                border-radius: {STYLES['radius_sm']};
                padding: 10px 16px;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 145, 0, 0.4);
                color: white;
                border-color: {STYLES['warning']};
            }}
        """
        self.battlecard_btn.setStyleSheet(self._battlecard_btn_normal_style)
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
            print("[TF] Demo mode ENABLED")
            # Could trigger demo transcript playback here
        else:
            self.demo_btn.setText("🎬 Demo Mode")
            print("[TF] Demo mode DISABLED")
    
    def _show_battlecard(self):
        """Show battlecard panel for competitor with dynamic API data."""
        print("[TF] Battlecard requested")
        
        # Reset button to normal style when clicked
        if hasattr(self, '_battlecard_btn_normal_style'):
            self.battlecard_btn.setStyleSheet(self._battlecard_btn_normal_style)
            self.battlecard_btn.setToolTip("Show Battlecard")
        
        # Close existing panel if open
        if self.battlecard_panel and self.battlecard_panel.isVisible():
            self.battlecard_panel.close()
        
        # Mark as shown
        self._battlecard_shown_once = True
        
        # If we have pending data, use it immediately
        if self._pending_battlecard_data:
            self.battlecard_panel = BattlecardPanel(
                parent_panel=self,
                competitor=self._pending_battlecard_data["competitor"],
                counter_points=self._pending_battlecard_data["points"]
            )
            self.battlecard_panel.show()
            # Apply stealth mode if enabled
            if self._stealth_enabled:
                self._apply_stealth_to_window(self.battlecard_panel, True)
            print(f"[TF] Battlecard panel opened with pending data: {self._pending_battlecard_data['competitor']}")
            return
        
        # Create battlecard panel with LOADING state (no hardcoded data)
        self.battlecard_panel = BattlecardPanel(
            parent_panel=self,
            competitor="Loading...",
            counter_points=["Fetching competitive intelligence from API..."]
        )
        self.battlecard_panel.show()
        # Apply stealth mode if enabled
        if self._stealth_enabled:
            self._apply_stealth_to_window(self.battlecard_panel, True)
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
                    print(f"[TF] Got battlecard from API: {data}")
                    # Emit signal to update UI with real data
                    self.signals.battlecard_updated.emit(data)
                else:
                    # API returned error - show fallback
                    print(f"[TF] Battlecard API error: {response.status_code}")
                    self.signals.battlecard_updated.emit({
                        "competitor": "Competitor",
                        "points": ["Unable to fetch data - API returned error"]
                    })
                    
            except Exception as e:
                print(f"[TF] Battlecard API error: {e}")
                # Show error state in UI
                self.signals.battlecard_updated.emit({
                    "competitor": "Competitor",
                    "points": [f"Unable to connect to backend: {str(e)[:50]}"]
                })
        threading.Thread(target=fetch_battlecard, daemon=True).start()

    def _on_battlecard_updated(self, data: dict):
        """Update battlecard panel with API data. Only auto-opens once, then highlights button for updates."""
        print(f"[TF DEBUG] Battlecard data received: {data}")
        
        # Handle different field names from API
        competitor = data.get("competitor") or data.get("competitor_name") or "Competitor"
        points = data.get("points") or data.get("counter_points") or data.get("talking_points") or []
        
        # If points is a string, convert to list
        if isinstance(points, str):
            points = [points]
        
        # Skip if just loading placeholder
        if competitor == "Loading...":
            return
        
        # Always store the latest data for button click
        self._pending_battlecard_data = {
            "competitor": competitor,
            "points": points if points else ["No competitive insights available"]
        }
        
        # If panel is currently visible, update it
        if self.battlecard_panel and self.battlecard_panel.isVisible():
            self.battlecard_panel.set_content(competitor, points if points else ["No competitive insights available"])
            print(f"[TF] Battlecard panel updated for: {competitor}")
        # If never shown before, auto-open it once
        elif not self._battlecard_shown_once:
            self._battlecard_shown_once = True
            self.battlecard_panel = BattlecardPanel(
                parent_panel=self,
                competitor=competitor,
                counter_points=points if points else ["No competitive insights available"]
            )
            self.battlecard_panel.show()
            # Apply stealth mode if enabled
            if self._stealth_enabled:
                self._apply_stealth_to_window(self.battlecard_panel, True)
            print(f"[TF] Battlecard panel opened for: {competitor}")
        # If previously shown but now closed/dismissed, just highlight the button
        else:
            self._highlight_battlecard_button()
            print(f"[TF] Battlecard button highlighted - new data for: {competitor}")
    
    def _highlight_battlecard_button(self):
        """Highlight the battlecard button to indicate new data is available."""
        if hasattr(self, '_battlecard_btn_highlight_style'):
            self.battlecard_btn.setStyleSheet(self._battlecard_btn_highlight_style)
            self.battlecard_btn.setToolTip("New Battlecard Available! Click to view")
    
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
            print(f"[TF] Selected audio: {file_path}")
            # Could trigger audio processing here
    
    def _toggle_demo_mode(self):
        """Toggle authenticated demo simulation."""
        self._demo_active = not self._demo_active
        
        if self._demo_active:
            print("[TF] Demo Mode: STARTED")
            self.demo_btn.setText("Demo: ON")
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
            print("[TF] Demo Mode: STOPPED")
            self.demo_btn.setText("Demo")
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
            
            # Close panels with 1 second delay
            QTimer.singleShot(1000, self._close_demo_panels)
    
    def _close_demo_panels(self):
        """Close demo-related panels and reset UI after demo mode is turned off."""
        # Close panels
        if self.battlecard_panel and self.battlecard_panel.isVisible():
            self.battlecard_panel.close()
            self.battlecard_panel = None
        if self.insight_panel and self.insight_panel.isVisible():
            self.insight_panel.close()
            self.insight_panel = None
        
        # Clear transcript
        if hasattr(self, 'transcript_text'):
            self.transcript_text.clear()
        
        # Reset hints to waiting state
        for label in self.hint_labels:
            label.setText("Waiting for analysis...")
            label.setStyleSheet(f"""
                color: {STYLES['text_muted']};
                font-size: 12px;
                background: transparent;
                border: none;
            """)
        
        # Clear entities
        if hasattr(self, 'entities_label'):
            self.entities_label.setText("Entities: None detected")
            self.entities_label.setStyleSheet(f"color: {STYLES['text_muted']}; font-size: 10px;")
        
        # Reset demo state variables
        if hasattr(self, '_demo_step'):
            del self._demo_step
        if hasattr(self, '_last_demo_time'):
            del self._last_demo_time
        if hasattr(self, '_demo_context'):
            del self._demo_context
        
        # Reset speaker word counts
        self._speaker_word_counts = {'S1': 0, 'S2': 0}

    def _run_demo_simulation(self):
        """Run a simulation loop for demo purposes with realistic mock data."""
        import time
        
        # Mock sales conversation segments with corresponding insights
        DEMO_CONVERSATION = [
            {
                "transcript": "[Speaker 1]: Hi Sarah, thanks for taking the time to meet today. I'm excited to show you how our platform can help streamline your sales process.",
                "entities": ["Sarah (Decision Maker)"],
                "hints": [
                    "Build rapport - use their name",
                    "Set clear agenda for the call",
                    "Identify key pain points early"
                ],
                "context": "Start by establishing a personal connection. Use their name naturally and show genuine interest in their business challenges.",
                "confidence": 45,
                "face_sentiment": {"happy": 0, "negative": 1}
            },
            {
                "transcript": "[Speaker 2]: Of course, we've been looking at several solutions. We're currently using Salesforce but the implementation has been challenging.",
                "entities": ["Sarah (Decision Maker)", "Salesforce (Competitor)"],
                "hints": [
                    "Competitor mentioned: Salesforce - prepare battlecard!",
                    "Implementation pain point detected",
                    "Ask about specific challenges they faced"
                ],
                "context": "Salesforce is a major competitor. Highlight our faster implementation and dedicated support. Don't badmouth them - focus on our strengths.",
                "confidence": 55,
                "show_battlecard": True,
                "battlecard": {
                    "competitor": "Salesforce",
                    "points": [
                        "Our implementation is 2x faster on average",
                        "We offer dedicated onboarding support",
                        "No hidden fees - transparent pricing model"
                    ]
                },
                "face_sentiment": {"happy": 0, "negative": 2}
            },
            {
                "transcript": "[Speaker 1]: I completely understand. Many of our clients switched from Salesforce because of complex implementations. What specific issues are you facing?",
                "entities": ["Sarah (Decision Maker)", "Salesforce (Competitor)"],
                "hints": [
                    "Great empathy statement - keep building trust",
                    "Dig deeper into their pain points",
                    "Listen for buying signals"
                ],
                "context": "You're building trust with empathy. Now dig deeper - ask open-ended questions to uncover their specific needs.",
                "confidence": 62,
                "face_sentiment": {"happy": 1, "negative": 2}
            },
            {
                "transcript": "[Speaker 2]: The main issue is training time. Our team spent three months just learning the system and we still aren't using half the features.",
                "entities": ["Sarah (Decision Maker)", "Salesforce (Competitor)", "Training (Pain Point)"],
                "hints": [
                    "Training pain point - emphasize our 1-week onboarding",
                    "Highlight our intuitive interface",
                    "Mention our free training resources"
                ],
                "context": "Training is their key pain point. Our 5-day onboarding and unlimited training sessions directly address this. Share the 'Acme Corp' case study.",
                "confidence": 70,
                "face_sentiment": {"happy": 2, "negative": 2}
            },
            {
                "transcript": "[Speaker 1]: That's a common frustration. Our average onboarding time is just 5 days, and we include unlimited training sessions at no extra cost.",
                "entities": ["Sarah (Decision Maker)", "Salesforce (Competitor)", "Training (Pain Point)"],
                "hints": [
                    "Strong value proposition delivered!",
                    "Ask about their budget timeline",
                    "Propose a pilot program"
                ],
                "context": "Great value proposition! Now transition to qualifying - ask about budget, timeline, and other stakeholders.",
                "confidence": 78,
                "face_sentiment": {"happy": 3, "negative": 2}
            },
            {
                "transcript": "[Speaker 2]: That sounds much better. What about pricing? Our budget is around $50,000 for this quarter.",
                "entities": ["Sarah (Decision Maker)", "Budget: $50K/quarter"],
                "hints": [
                    "Budget disclosed: $50K - qualify the opportunity",
                    "Mention 20% discount for annual commitment",
                    "Highlight ROI calculator"
                ],
                "context": "$50K/quarter fits our Enterprise tier perfectly. The 20% annual discount brings it to $160K/year - well within budget. Use the ROI calculator.",
                "confidence": 82,
                "face_sentiment": {"happy": 4, "negative": 2}
            },
            {
                "transcript": "[Speaker 1]: We can definitely work within that budget. For annual commitments, we offer a 20% discount which would give you premium features plus priority support.",
                "entities": ["Sarah (Decision Maker)", "Budget: $50K/quarter", "20% Discount"],
                "hints": [
                    "Pricing leverage used effectively",
                    "Push for decision timeline",
                    "Schedule follow-up with stakeholders"
                ],
                "context": "Discount offered - now create urgency. Ask about their decision timeline and who else needs to be involved.",
                "confidence": 88,
                "face_sentiment": {"happy": 5, "negative": 2}
            },
            {
                "transcript": "[Speaker 2]: That's interesting. I'll need to discuss with our CFO, Michael, but I'm personally very impressed. When can we schedule a demo for the full team?",
                "entities": ["Sarah (Decision Maker)", "Michael (CFO)", "Demo Requested"],
                "hints": [
                    "🎯 Demo requested - strong buying signal!",
                    "Get CFO's calendar for next week",
                    "Prepare ROI presentation for finance"
                ],
                "context": "🎉 Great closing! Demo requested = strong buying signal. Schedule within the week and prepare CFO-focused ROI presentation.",
                "confidence": 92,
                "face_sentiment": {"happy": 7, "negative": 2}
            }
        ]
        
        # Initialize demo state
        if not hasattr(self, '_demo_step'):
            self._demo_step = 0
            self._last_demo_time = 0
        
        current_time = time.time()
        
        # Progress through conversation every 4 seconds
        if current_time - self._last_demo_time > 4:
            step = DEMO_CONVERSATION[self._demo_step % len(DEMO_CONVERSATION)]
            
            # Update transcript
            self.update_transcript(step["transcript"])
            
            # Update hints
            self.update_hints(step["hints"])
            
            # Store current context for insight details
            self._demo_context = step.get("context", "")
            
            # Update entities
            self.update_entities(step["entities"])
            
            # Update confidence
            self.update_confidence(step["confidence"])
            
            # Show battlecard if triggered
            if step.get("show_battlecard"):
                bc = step["battlecard"]
                # Create battlecard panel if it doesn't exist or isn't visible
                if not self.battlecard_panel or not self.battlecard_panel.isVisible():
                    self.battlecard_panel = BattlecardPanel(
                        parent_panel=self,
                        competitor=bc["competitor"],
                        counter_points=bc["points"]
                    )
                    self.battlecard_panel.show()
                else:
                    # Update existing panel
                    self.battlecard_panel.set_content(bc["competitor"], bc["points"])
            
            # Update face sentiment (for demo)
            if step.get("face_sentiment"):
                self.signals.face_sentiment_updated.emit(step["face_sentiment"])
            
            self._demo_step += 1
            self._last_demo_time = current_time
            
            # Reset after full conversation cycle
            if self._demo_step >= len(DEMO_CONVERSATION):
                self._demo_step = 0
                # Clear transcript for next cycle
                if hasattr(self, 'transcript_text'):
                    self.transcript_text.clear()
    
    # ==================== STEALTH MODE ====================
    
    def _apply_stealth_to_window(self, window, enabled: bool) -> bool:
        """Apply stealth mode to a specific window."""
        if sys.platform != 'win32' or window is None:
            return False
        
        try:
            hwnd = int(window.winId())
            user32 = ctypes.windll.user32
            affinity = WDA_EXCLUDEFROMCAPTURE if enabled else WDA_NONE
            result = user32.SetWindowDisplayAffinity(hwnd, affinity)
            return bool(result)
        except Exception as e:
            print(f"[Overlay] Stealth apply error: {e}")
            return False
    
    def set_stealth_mode(self, enabled: bool):
        """
        Enable or disable stealth mode (hidden from screen capture).
        
        Uses Windows SetWindowDisplayAffinity API.
        Only works on Windows 10 version 2004+ (Build 19041+).
        Applies to main window AND all floating panels.
        """
        if sys.platform != 'win32':
            print("[Overlay] Stealth mode only supported on Windows")
            return False
        
        try:
            # Apply to main window
            result = self._apply_stealth_to_window(self, enabled)
            
            # Apply to floating panels if they exist
            if self.insight_panel and self.insight_panel.isVisible():
                self._apply_stealth_to_window(self.insight_panel, enabled)
            if self.battlecard_panel and self.battlecard_panel.isVisible():
                self._apply_stealth_to_window(self.battlecard_panel, enabled)
            
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
                print(f"[TF] Stealth mode: {'ENABLED' if enabled else 'DISABLED'}")
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
    
    def _normalize_hint_text(self, text: str) -> str:
        """Normalize hint text to use Speaker 1/2 instead of pronouns.
        
        Replaces awkward pronoun constructs like "you's issues" or "I a post call"
        with clearer speaker labels.
        """
        import re
        
        # Replace possessive patterns first (you's -> Speaker 2's, I's -> Speaker 1's)
        text = re.sub(r"\byou's\b", "Speaker 2's", text, flags=re.IGNORECASE)
        text = re.sub(r"\bI's\b", "Speaker 1's", text, flags=re.IGNORECASE)
        
        # Replace standalone pronouns at word boundaries
        # "you" -> "Speaker 2" (the prospect/client)
        # "I" -> "Speaker 1" (the sales rep)
        text = re.sub(r"\byou\b", "Speaker 2", text, flags=re.IGNORECASE)
        text = re.sub(r"\bI\b", "Speaker 1", text)
        
        # Clean up any double spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def _on_hints_updated(self, hints: List[str]):
        """Update hint cards with new data and estimate confidence."""
        # Update hint cards
        for i, label in enumerate(self.hint_labels):
            if i < len(hints):
                current_text = label.text()
                new_text = self._normalize_hint_text(hints[i])
                
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
        
        # Estimate confidence based on hints received
        if hints and len(hints) > 0:
            # Track hint updates for confidence calculation
            if not hasattr(self, '_hint_update_count'):
                self._hint_update_count = 0
            self._hint_update_count += 1
            
            # Base confidence: starts at 40%, increases with more updates
            base_confidence = 40 + min(self._hint_update_count * 8, 40)
            
            # Bonus for specific keywords indicating positive progress
            positive_keywords = ["budget", "timeline", "decision", "sign", "pricing", "interested"]
            bonus = 0
            for hint in hints:
                hint_lower = hint.lower()
                for keyword in positive_keywords:
                    if keyword in hint_lower:
                        bonus += 5
                        break
            
            # Calculate final confidence (cap at 95)
            confidence = min(base_confidence + bonus, 95)
            self.update_confidence(confidence)

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
    
    def show_error(self, error_message: str):
        """Display an error message to the user in the hints panel.
        
        Args:
            error_message: The error message to display
        """
        print(f"[TF ERROR] {error_message}")
        # Show error in the first hint card with red styling
        if hasattr(self, 'hint_labels') and len(self.hint_labels) > 0:
            self.hint_labels[0].setText(f"⚠️ {error_message}")
            self.hint_labels[0].setStyleSheet(f"""
                color: {STYLES['error']};
                font-size: 12px;
                background: transparent;
                border: none;
            """)
            # Highlight the hint card in red
            if hasattr(self, 'hint_cards') and len(self.hint_cards) > 0:
                self.hint_cards[0].setStyleSheet(f"""
                    background-color: rgba(255, 82, 82, 0.15);
                    border-radius: {STYLES['radius_sm']};
                    border: 1px solid {STYLES['error']};
                """)
    
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
        """Append to transcript display with speaker formatting and update talk balance."""
        # Initialize speaker word counts if not exists
        if not hasattr(self, '_speaker_word_counts'):
            self._speaker_word_counts = {'S1': 0, 'S2': 0}
        
        # Detect speaker from text and count words
        # Remove HTML tags for word counting but keep for speaker detection
        import re
        clean_text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
        word_count = len(clean_text.split())
        
        # SPEAKER_00 = first detected speaker = usually the other person (Client/S2)
        # SPEAKER_01 = second detected speaker = usually YOU (Sales Rep/S1)
        # This is because in most meeting scenarios, the client speaks first
        text_upper = text.upper()
        is_speaker1 = (
            "[SALES_REP]" in text or
            "[SPEAKER_01]" in text or  # YOU are usually the second speaker
            "[Speaker 2]" in text or   # Formatted version (will swap display too)
            "SPEAKER_01" in text_upper or
            "SPEAKER 2" in text_upper
        )
        is_speaker2 = (
            "[CLIENT]" in text or
            "[SPEAKER_00]" in text or  # Client is usually the first speaker
            "[Speaker 1]" in text or   # Formatted version
            "SPEAKER_00" in text_upper or
            "SPEAKER 1" in text_upper
        )
        
        if is_speaker1 and not is_speaker2:
            self.update_speaker("SALES_REP")
            self._speaker_word_counts['S1'] += word_count
            print(f"[TalkBalance] S1 (You) += {word_count} words (total S1={self._speaker_word_counts['S1']}, S2={self._speaker_word_counts['S2']})")
        elif is_speaker2 and not is_speaker1:
            self.update_speaker("CLIENT")
            self._speaker_word_counts['S2'] += word_count
            print(f"[TalkBalance] S2 (Client) += {word_count} words (total S1={self._speaker_word_counts['S1']}, S2={self._speaker_word_counts['S2']})")
        elif word_count > 0:
            # If no speaker detected or both detected, attribute to S1 (you) by default
            self._speaker_word_counts['S1'] += word_count
            print(f"[TalkBalance] Default S1 (You) += {word_count} words (no clear speaker tag)")
        
        # Update talk balance based on cumulative word counts
        total_words = self._speaker_word_counts['S1'] + self._speaker_word_counts['S2']
        if total_words > 0:
            s1_ratio = (self._speaker_word_counts['S1'] / total_words) * 100
            self.update_talk_balance(int(s1_ratio))
        
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
    
    def _on_entities_updated(self, entities: List[dict]):
        """Update entities label. Handles both strings and dicts."""
        if entities:
            # Extract text if entity is a dict
            clean_entities = []
            for e in entities:
                if isinstance(e, dict):
                    clean_entities.append(e.get("text", str(e)))
                else:
                    clean_entities.append(str(e))
            
            text = "Entities: " + ", ".join(clean_entities[:5])
            if len(clean_entities) > 5:
                text += f" (+{len(clean_entities)-5} more)"
            self.entities_label.setText(text)
            self.entities_label.setStyleSheet("color: #8BC34A; font-size: 11px;")
        else:
            self.entities_label.setText("Entities: None detected")
            self.entities_label.setStyleSheet("color: #888; font-size: 11px;")
    
    def _on_face_sentiment_updated(self, data: dict):
        """Update face sentiment counter labels and sentiment indicator box."""
        happy = data.get("happy", 0)
        negative = data.get("negative", 0)
        
        self.happy_label.setText(f"😊 {happy}")
        self.negative_label.setText(f"😠 {negative}")
        
        # Determine overall sentiment and update the indicator box
        if happy >= negative and (happy > 0 or negative > 0):
            new_state = "positive"
            text = "Engaged!"
            bg_color = "rgba(0, 230, 118, 0.2)"
            border_color = STYLES['success']
            text_color = STYLES['success']
        elif negative > happy:
            new_state = "negative"
            text = "Not Engaged"
            bg_color = "rgba(255, 82, 82, 0.2)"
            border_color = STYLES['error']
            text_color = STYLES['error']
        else:
            new_state = "neutral"
            text = "Analyzing..."
            bg_color = STYLES['bg_tertiary']
            border_color = STYLES['border_subtle']
            text_color = STYLES['text_secondary']
        
        # Check if state changed for animation
        state_changed = new_state != getattr(self, '_last_sentiment_state', 'neutral')
        self._last_sentiment_state = new_state
        
        # Update the sentiment box
        self.sentiment_box.setText(text)
        self.sentiment_box.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                background: {bg_color};
                font-size: 11px;
                font-weight: bold;
                padding: 4px 8px;
                border-radius: 8px;
                border: 1px solid {border_color};
            }}
        """)
        
        # Subtle pulse animation when state changes
        if state_changed and new_state != "neutral":
            # Brief highlight then fade back
            highlight_color = STYLES['success'] if new_state == "positive" else STYLES['error']
            self.sentiment_box.setStyleSheet(f"""
                QLabel {{
                    color: white;
                    background: {highlight_color};
                    font-size: 11px;
                    font-weight: bold;
                    padding: 4px 8px;
                    border-radius: 8px;
                    border: 2px solid {highlight_color};
                }}
            """)
            # Revert to normal style after 300ms
            QTimer.singleShot(300, lambda: self.sentiment_box.setStyleSheet(f"""
                QLabel {{
                    color: {text_color};
                    background: {bg_color};
                    font-size: 11px;
                    font-weight: bold;
                    padding: 4px 8px;
                    border-radius: 8px;
                    border: 1px solid {border_color};
                }}
            """))
        
        print(f"[Overlay] Face sentiment: happy={happy}, negative={negative}, state={new_state}")
    
    # ==================== EVENT HANDLERS ====================
    
    # API Configuration
    API_BASE_URL = "http://127.0.0.1:8000/api/v1"
    
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
        
        # Reset tracking counters for new session
        self._speaker_word_counts = {'S1': 0, 'S2': 0}
        self._hint_update_count = 0
        self.update_confidence(0)  # Reset confidence
        self.update_talk_balance(50)  # Reset to balanced
        
        self.update_status("starting")
        self.transcript_text.clear()
        print("[Overlay] Starting session via API...")
        
        def call_api():
            try:
                response = requests.post(
                    f"{self.API_BASE_URL}/start-session",
                    json={"capture_mode": "remote"},  # Tell backend we're sending audio remotely
                    timeout=30
                )
                if response.status_code == 200:
                    self._is_recording = True
                    self.update_status("running")
                    print(f"[Overlay] Session started: {response.json()}")
                    
                    # Start local audio capture and stream to backend
                    self._audio_capture = ClientAudioCapture(self.API_BASE_URL)
                    self._audio_capture.start()
                    
                    # Start client-side face sentiment (runs on THIS machine)
                    self._start_client_face_sentiment()
                    
                    # Start WebSocket connection for updates
                    self._connect_websocket()
                else:
                    error_msg = f"Session start failed (Status: {response.status_code})"
                    print(f"[Overlay] Start failed: {response.status_code} - {response.text}")
                    self.update_status("error")
                    self.signals.error_updated.emit(error_msg)
            except requests.exceptions.ConnectionError:
                error_msg = "Cannot connect to backend server"
                print(f"[Overlay] Connection error")
                self.update_status("error")
                self.signals.error_updated.emit(error_msg)
            except requests.exceptions.Timeout:
                error_msg = "Backend server timed out"
                print(f"[Overlay] Timeout error")
                self.update_status("error")
                self.signals.error_updated.emit(error_msg)
            except Exception as e:
                error_msg = f"API Error: {str(e)[:40]}"
                print(f"[Overlay] API error: {e}")
                self.update_status("error")
                self.signals.error_updated.emit(error_msg)
        
        # Run API call in background thread
        threading.Thread(target=call_api, daemon=True).start()
    
    def _start_client_face_sentiment(self):
        """Start client-side face sentiment capture (runs on this machine)."""
        import threading
        
        self._face_sentiment_running = True
        self._face_sentiment_happy = 0
        self._face_sentiment_negative = 0
        
        def face_loop():
            import time
            try:
                import mss
                import numpy as np
            except ImportError as e:
                print(f"[Overlay] Face sentiment: missing deps ({e})")
                return
            
            # Try to import DeepFace
            try:
                from deepface import DeepFace
                print("[Overlay] Face sentiment: DeepFace loaded")
            except ImportError:
                print("[Overlay] Face sentiment: DeepFace not installed, feature disabled")
                return
            
            with mss.mss() as sct:
                first_run = True
                capture_count = 0
                
                while self._face_sentiment_running and self._is_recording:
                    # First run: quick 5s delay, then 30s intervals
                    wait_time = 5 if first_run else 30
                    first_run = False
                    time.sleep(wait_time)
                    
                    if not self._is_recording:
                        break
                    
                    capture_count += 1
                    
                    try:
                        # Capture PRIMARY monitor (monitors[1], not [0] which is all monitors combined)
                        # monitors[0] = virtual screen covering all monitors
                        # monitors[1] = primary monitor
                        monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                        
                        print(f"[Overlay] Face capture #{capture_count}: {monitor['width']}x{monitor['height']}")
                        
                        screenshot = sct.grab(monitor)
                        img_array = np.array(screenshot)
                        
                        # Convert BGRA to BGR
                        import cv2
                        img = cv2.cvtColor(img_array, cv2.COLOR_BGRA2BGR)
                        
                        # Resize for faster processing (max 1280px width)
                        height, width = img.shape[:2]
                        max_width = 1280
                        if width > max_width:
                            scale = max_width / width
                            new_width = int(width * scale)
                            new_height = int(height * scale)
                            img = cv2.resize(img, (new_width, new_height))
                            print(f"[Overlay] Resized to {new_width}x{new_height}")
                        
                        # Save to temp file
                        import tempfile
                        import os
                        import uuid
                        temp_path = os.path.join(tempfile.gettempdir(), f"face_{uuid.uuid4().hex}.jpg")
                        cv2.imwrite(temp_path, img, [cv2.IMWRITE_JPEG_QUALITY, 90])
                        
                        # Analyze with DeepFace
                        try:
                            # Use retinaface for better accuracy (slower but more reliable)
                            results = DeepFace.analyze(
                                temp_path,
                                actions=['emotion'],
                                enforce_detection=False,
                                silent=True,
                                detector_backend='retinaface'  # More accurate than opencv
                            )
                            
                            if isinstance(results, dict):
                                results = [results]
                            
                            faces_found = 0
                            for face in results:
                                if 'dominant_emotion' in face:
                                    # Skip if region is too small (likely false positive)
                                    region = face.get('region', {})
                                    face_w = region.get('w', 0)
                                    face_h = region.get('h', 0)
                                    
                                    if face_w < 30 or face_h < 30:
                                        continue
                                    
                                    faces_found += 1
                                    emotion = face['dominant_emotion'].lower()
                                    confidence = face.get('emotion', {}).get(emotion, 0)
                                    
                                    print(f"[Overlay] Face #{faces_found}: {emotion} ({confidence:.1f}%)")
                                    
                                    if emotion in {'happy', 'neutral', 'surprise'}:
                                        self._face_sentiment_happy += 1
                                    else:
                                        self._face_sentiment_negative += 1
                            
                            # Update UI
                            self.signals.face_sentiment_updated.emit({
                                "happy": self._face_sentiment_happy,
                                "negative": self._face_sentiment_negative
                            })
                            
                            if faces_found > 0:
                                print(f"[Overlay] 😊 Face sentiment update: {self._face_sentiment_happy} happy, {self._face_sentiment_negative} negative")
                            else:
                                print(f"[Overlay] No faces detected in capture #{capture_count}")
                            
                        except ValueError as e:
                            print(f"[Overlay] Face detection: {e}")
                        except Exception as e:
                            print(f"[Overlay] Face analysis error: {e}")
                        
                        # Cleanup
                        try:
                            os.remove(temp_path)
                        except:
                            pass
                            
                    except Exception as e:
                        print(f"[Overlay] Face capture error: {e}")
            
            print("[Overlay] Face sentiment loop stopped")
        
        threading.Thread(target=face_loop, daemon=True).start()
        print("[Overlay] Client-side face sentiment started")
    
    def _stop_client_face_sentiment(self):
        """Stop client-side face sentiment capture."""
        if hasattr(self, '_face_sentiment_running'):
            self._face_sentiment_running = False
    
    def _stop_session(self):
        """Stop the capture session via API."""
        import requests
        import threading
        
        self.update_status("processing")
        print("[Overlay] Stopping session via API...")
        
        def call_api():
            try:
                # Stop local audio capture first
                if self._audio_capture:
                    self._audio_capture.stop()
                    self._audio_capture = None
                
                # Stop face sentiment
                self._stop_client_face_sentiment()
                
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
                if self._audio_capture:
                    self._audio_capture.stop()
                    self._audio_capture = None
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
                    self.signals.connection_updated.emit("connecting")
                    
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
                            elif msg_type == "face_sentiment":
                                self.signals.face_sentiment_updated.emit(data)
                            elif msg_type == "battlecard":
                                # Backend sends {"type": "battlecard", "battlecard": {...}}
                                # Extract the battlecard data before emitting
                                battlecard_data = data.get("battlecard", data)
                                print(f"[Overlay DEBUG] Received battlecard for: {battlecard_data.get('competitor', 'Unknown')}")
                                self.signals.battlecard_updated.emit(battlecard_data)
                            elif msg_type == "ping":
                                # Server keep-alive, ignore
                                pass
                        except Exception as e:
                            print(f"[Overlay] WS message error: {e}")
                    
                    def on_error(ws, error):
                        print(f"[Overlay] WS error: {error}")
                        self.signals.connection_updated.emit("error")
                    
                    def on_close(ws, close_status_code=None, close_msg=None):
                        nonlocal ws_connected
                        ws_connected = False
                        print("[Overlay] WS closed")
                        self.signals.connection_updated.emit("disconnected")
                    
                    def on_open(ws):
                        nonlocal ws_connected, reconnect_count
                        ws_connected = True
                        reconnect_count = 0  # Reset on successful connect
                        print("[Overlay] WS connected!")
                        self.signals.connection_updated.emit("connected")
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
    
    def closeEvent(self, event):
        """Handle window close - cleanup all background threads."""
        print("[Overlay] Window closing, cleaning up...")
        self._cleanup_on_close()
        event.accept()
        QApplication.quit()
    
    def _cleanup_on_close(self):
        """Stop all background tasks before closing."""
        # Stop recording session
        self._is_recording = False
        
        # Stop face sentiment
        self._stop_client_face_sentiment()
        
        # Stop audio capture
        if self._audio_capture:
            try:
                self._audio_capture.stop()
            except:
                pass
            self._audio_capture = None
        
        # Close floating panels
        if self.insight_panel:
            self.insight_panel.close()
        if self.battlecard_panel:
            self.battlecard_panel.close()
        
        print("[Overlay] Cleanup complete")


def run_overlay():
    """Run the overlay as a standalone application."""
    app = QApplication(sys.argv)
    
    # Set app-wide dark theme
    app.setStyle("Fusion")
    
    overlay = StealthOverlay()
    overlay.show()
    
    # Ensure app quits when window closes
    app.aboutToQuit.connect(overlay._cleanup_on_close)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    run_overlay()