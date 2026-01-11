"""
Stealth Overlay UI - Always-on-top transparent overlay for sales hints.

Features:
- Transparent, borderless window that stays on top
- Stealth Mode: Hidden from screen capture/recording (Windows 10+)
- Live transcript display
- Quick Hints panel
- Status indicator
"""

import sys
import ctypes
from typing import List, Optional
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QColor, QPalette


# Windows constants for SetWindowDisplayAffinity
WDA_NONE = 0x00000000
WDA_EXCLUDEFROMCAPTURE = 0x00000011  # Windows 10 2004+ (Build 19041+)

# Audio capture imports
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
            try:
                print(f"[ClientAudio] Connecting to {ws_url}...")
                self._ws = websocket.create_connection(ws_url, timeout=10)
                print("[ClientAudio] Connected to backend")
                
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
                
                # Open audio stream
                print(f"[ClientAudio] Opening stream at {native_rate}Hz...")
                stream = sd.InputStream(
                    device=device_id,
                    samplerate=native_rate,
                    channels=1,
                    dtype=np.float32,
                    callback=audio_callback,
                    blocksize=1024
                )
                stream.start()
                print("[ClientAudio] Audio stream active")
                
                # Keep alive while running
                while self._running and stream.active:
                    time.sleep(0.5)
                    # Check WebSocket health
                    try:
                        self._ws.ping()
                    except:
                        print("[ClientAudio] WebSocket disconnected")
                        break
                
                stream.stop()
                stream.close()
                
            except Exception as e:
                print(f"[ClientAudio] Error (retrying in 3s): {e}")
                time.sleep(3)
            
            finally:
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
            print(f"[ClientAudio] Sent {len(audio_data)/self._sample_rate:.1f}s chunk")
            
        except Exception as e:
            print(f"[ClientAudio] Send error: {e}")
        
        # Reset buffer
        self._audio_buffer = []
        self._buffer_start_time = time.time()


class SignalBridge(QObject):
    """Bridge for thread-safe signal emission."""
    hints_updated = pyqtSignal(list)
    transcript_updated = pyqtSignal(str)
    status_updated = pyqtSignal(str)
    entities_updated = pyqtSignal(list)
    battlecard_received = pyqtSignal(dict)


class BattlecardPanel(QFrame):
    """
    Panel for displaying competitive battlecards.
    Pops up when a competitor is detected.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(60, 20, 20, 220);
                border: 1px solid #E53935;
                border-radius: 8px;
            }
        """)
        self.setVisible(False)  # Hidden by default
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)
        
        # Header
        header = QHBoxLayout()
        self.title = QLabel("⚔️ COMPETITOR DETECTED")
        self.title.setStyleSheet("color: #FF5252; font-weight: bold; font-size: 13px;")
        header.addWidget(self.title)
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(20, 20)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton { color: #AAA; border: none; font-weight: bold; }
            QPushButton:hover { color: white; }
        """)
        close_btn.clicked.connect(self.hide)
        header.addWidget(close_btn)
        layout.addLayout(header)
        
        # Competitor Name
        self.competitor_label = QLabel("Competitor: ???")
        self.competitor_label.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
        layout.addWidget(self.competitor_label)
        
        # Quick Response
        self.response_label = QLabel("Quick Response...")
        self.response_label.setWordWrap(True)
        self.response_label.setStyleSheet("color: #FFD700; font-style: italic; font-size: 13px; margin: 4px 0;")
        layout.addWidget(self.response_label)
        
        # Counter Points
        self.points_label = QLabel("• Point 1\n• Point 2\n• Point 3")
        self.points_label.setWordWrap(True)
        self.points_label.setStyleSheet("color: #EEE; font-size: 12px;")
        layout.addWidget(self.points_label)
    
    def show_battlecard(self, data):
        """Update and show the panel."""
        self.competitor_label.setText(f"VS {data.get('competitor', 'Unknown')}")
        self.response_label.setText(f"\"{data.get('quick_response', '')}\"")
        
        points = data.get("counter_points", [])
        points_text = "\n".join([f"• {p}" for p in points])
        self.points_label.setText(points_text)
        
        self.setVisible(True)

    
class StealthOverlay(QMainWindow):
    """
    Stealth overlay window for real-time sales assistance.
    
    Can be hidden from screen capture using Windows API.
    """
    
    def __init__(self):
        super().__init__()
        
        self._stealth_enabled = False
        self._is_recording = False
        
        # Client-side audio capture for distributed deployment
        self._audio_capture = None
        
        # Signal bridge for thread-safe updates
        self.signals = SignalBridge()
        self.signals.hints_updated.connect(self._on_hints_updated)
        self.signals.transcript_updated.connect(self._on_transcript_updated)
        self.signals.status_updated.connect(self._on_status_updated)
        self.signals.entities_updated.connect(self._on_entities_updated)
        self.signals.battlecard_received.connect(self._on_battlecard_received)
        
        self._setup_ui()
        self._setup_window()
        
    def _setup_window(self):
        """Configure window properties."""
        self.setWindowTitle("Sales Assistant")
        
        # Frameless, always on top, tool window (doesn't show in taskbar)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        
        # Transparent background
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Position: Bottom-right corner
        self.resize(350, 400)
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
        """Build the UI components."""
        # Main container with semi-transparent dark background
        container = QWidget()
        container.setObjectName("container")
        container.setStyleSheet("""
            #container {
                background-color: rgba(20, 20, 30, 220);
                border-radius: 12px;
                border: 1px solid rgba(100, 100, 120, 100);
            }
        """)
        self.setCentralWidget(container)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        
        # Header with status and stealth toggle
        header = self._create_header()
        layout.addWidget(header)
        
        # Hints panel
        self.hints_frame = self._create_hints_panel()
        layout.addWidget(self.hints_frame)

        # Battlecard Panel (Hidden by default)
        self.battlecard_panel = BattlecardPanel()
        layout.addWidget(self.battlecard_panel)
        
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
        """Create header with status indicator."""
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title = QLabel("🎯 Sales Assistant")
        title.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Status indicator
        self.status_label = QLabel("● Idle")
        self.status_label.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(self.status_label)
        
        # Stealth indicator
        self.stealth_indicator = QLabel("👁")
        self.stealth_indicator.setStyleSheet("font-size: 14px;")
        self.stealth_indicator.setToolTip("Stealth Mode: OFF")
        layout.addWidget(self.stealth_indicator)
        
        return header
    
    def _create_hints_panel(self) -> QFrame:
        """Create the Quick Hints display panel."""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: rgba(40, 40, 60, 200);
                border-radius: 8px;
                padding: 8px;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)
        
        # Header
        header = QLabel("💡 Quick Hints")
        header.setStyleSheet("color: #FFD700; font-size: 12px; font-weight: bold;")
        layout.addWidget(header)
        
        # Hint buttons (3 slots)
        self.hint_buttons = []
        for i in range(3):
            btn = QPushButton(f"• Waiting for analysis...")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    color: #CCC;
                    font-size: 13px;
                    text-align: left;
                    border: none;
                    padding: 4px;
                    background: transparent;
                }
                QPushButton:hover {
                    color: #FFD700;
                    background-color: rgba(255, 255, 255, 20);
                    border-radius: 4px;
                }
            """)
            # Connect using closure to capture index/text
            # Note: We'll attach the specific hint text dynamically later
            btn.clicked.connect(lambda checked, b=btn: self._on_hint_clicked(b))
            self.hint_buttons.append(btn)
            layout.addWidget(btn)
        
        return frame
    
    def _create_transcript_panel(self) -> QWidget:
        """Create scrollable transcript display."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Header
        header = QLabel("📝 Live Transcript")
        header.setStyleSheet("color: #AAA; font-size: 11px;")
        layout.addWidget(header)
        
        # Transcript text area
        self.transcript_text = QTextEdit()
        self.transcript_text.setReadOnly(True)
        self.transcript_text.setStyleSheet("""
            QTextEdit {
                background-color: rgba(30, 30, 40, 200);
                color: #DDD;
                border: 1px solid rgba(80, 80, 100, 100);
                border-radius: 6px;
                font-size: 12px;
                padding: 6px;
            }
        """)
        self.transcript_text.setMaximumHeight(120)
        layout.addWidget(self.transcript_text)
        
        return panel
    
    def _create_controls(self) -> QWidget:
        """Create control buttons."""
        controls = QWidget()
        layout = QHBoxLayout(controls)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Start/Stop button
        self.start_btn = QPushButton("▶ Start")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #2E7D32;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        self.start_btn.clicked.connect(self._on_start_clicked)
        layout.addWidget(self.start_btn)
        
        # Stealth toggle
        self.stealth_btn = QPushButton("🙈 Stealth")
        self.stealth_btn.setStyleSheet("""
            QPushButton {
                background-color: #455A64;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background-color: #546E7A;
            }
        """)
        self.stealth_btn.clicked.connect(self._toggle_stealth)
        layout.addWidget(self.stealth_btn)
        
        # Close button
        close_btn = QPushButton("✕")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(180, 60, 60, 200);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background-color: rgba(200, 80, 80, 220);
            }
        """)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        return controls
    
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
                self.stealth_indicator.setText("🙈" if enabled else "👁")
                self.stealth_indicator.setToolTip(
                    "Stealth Mode: ON (Hidden from capture)" if enabled 
                    else "Stealth Mode: OFF"
                )
                self.stealth_btn.setText("👁 Visible" if enabled else "🙈 Stealth")
                print(f"[Overlay] Stealth mode: {'ENABLED' if enabled else 'DISABLED'}")
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
        """Update hint buttons."""
        for i, btn in enumerate(self.hint_buttons):
            if i < len(hints):
                text = hints[i]
                btn.setText(f"• {text}")
                btn.setStyleSheet("""
                    QPushButton {
                        color: #FFF;
                        font-size: 13px;
                        text-align: left;
                        border: none;
                        padding: 4px;
                    }
                    QPushButton:hover {
                        color: #FFD700;
                        background-color: rgba(255, 255, 255, 30);
                        border-radius: 4px;
                        font-weight: bold;
                    }
                """)
                btn.setProperty("hint_text", text)
                btn.setToolTip("Click to Star (Save to CRM)")
                btn.setEnabled(True)
            else:
                btn.setText("• ...")
                btn.setStyleSheet("""
                   QPushButton { 
                        color: #666; 
                        font-size: 13px; 
                        text-align: left;
                        border: none;
                        padding: 4px;
                   }
                """)
                btn.setEnabled(False)
    
    def _on_hint_clicked(self, btn):
        """Handle click on hint button to star it."""
        hint_text = btn.property("hint_text")
        if not hint_text:
            return
            
        print(f"[Overlay] Star clicked: {hint_text}")
        
        # Visual feedback
        original_text = btn.text()
        btn.setText(f"⭐ SAVED: {hint_text}")
        btn.setStyleSheet("color: #4CAF50; font-weight: bold; border: none; padding: 4px;")
        
        # Revert visual feedback after 1.5s
        QTimer.singleShot(1500, lambda: self._revert_hint_btn(btn, original_text))
        
        # Call API
        self._star_hint_api(hint_text)
        
    def _revert_hint_btn(self, btn, text):
        if btn.text().startswith("⭐"):
            btn.setText(text)
            btn.setStyleSheet("""
                QPushButton {
                    color: #FFF;
                    font-size: 13px;
                    text-align: left;
                    border: none;
                    padding: 4px;
                }
                QPushButton:hover {
                    color: #FFD700;
                    background-color: rgba(255, 255, 255, 30);
                    border-radius: 4px;
                    font-weight: bold;
                }
            """)

    def _star_hint_api(self, hint_text):
        """Call API to star the hint."""
        import requests
        import threading
        def call():
            try:
                requests.post(
                    f"{self.API_BASE_URL}/star-hint",
                    json={"hint_text": hint_text}
                )
            except Exception as e:
                print(f"[Overlay] Star API error: {e}")
        threading.Thread(target=call, daemon=True).start()
    
    def update_transcript(self, text: str):
        """Thread-safe transcript update via signal."""
        self.signals.transcript_updated.emit(text)
    
    def _on_transcript_updated(self, text: str):
        """Append to transcript display."""
        current = self.transcript_text.toPlainText()
        self.transcript_text.setPlainText(current + " " + text if current else text)
        # Auto-scroll to bottom
        scrollbar = self.transcript_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def update_status(self, status: str):
        """Thread-safe status update via signal."""
        self.signals.status_updated.emit(status)
    
    def _on_status_updated(self, status: str):
        """Update status indicator."""
        status_lower = status.lower()
        if status_lower == "running":
            self.status_label.setText("● Recording")
            self.status_label.setStyleSheet("color: #4CAF50; font-size: 12px;")
            self.start_btn.setText("⏹ Stop")
            self.start_btn.setStyleSheet("""
                QPushButton {
                    background-color: #C62828;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #D32F2F;
                }
            """)
        elif status_lower == "processing":
            self.status_label.setText("● Processing...")
            self.status_label.setStyleSheet("color: #FFA726; font-size: 12px;")
        elif status_lower == "completed":
            self.status_label.setText("● Completed")
            self.status_label.setStyleSheet("color: #42A5F5; font-size: 12px;")
            self._reset_start_button()
        else:
            self.status_label.setText(f"● {status.capitalize()}")
            self.status_label.setStyleSheet("color: #888; font-size: 12px;")
            self._reset_start_button()
    
    def _reset_start_button(self):
        """Reset start button to initial state."""
        self.start_btn.setText("▶ Start")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #2E7D32;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
    
    def update_entities(self, entities: List[str]):
        """Thread-safe entities update via signal."""
        self.signals.entities_updated.emit(entities)
    
    def update_battlecard(self, battlecard: dict):
        """Thread-safe battlecard update via signal."""
        self.signals.battlecard_received.emit(battlecard)
    
    def _on_battlecard_received(self, battlecard: dict):
        """Show battlecard panel."""
        self.battlecard_panel.show_battlecard(battlecard)
        
        # Auto-hide after 30 seconds
        QTimer.singleShot(30000, self.battlecard_panel.hide)
    
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
                # Stop local audio capture first
                if self._audio_capture:
                    self._audio_capture.stop()
                    self._audio_capture = None
                
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
                    
                    ws_connected = False
                    
                    def on_message(ws, message):
                        try:
                            data = json.loads(message)
                            msg_type = data.get("type")
                            
                            if msg_type == "hints":
                                self.update_hints(data.get("hints", []))
                            elif msg_type == "transcript":
                                self.update_transcript(data.get("text", ""))
                            elif msg_type == "status":
                                status = data.get("status", "")
                                if status and status != "ping":
                                    self.update_status(status)
                            elif msg_type == "entities":
                                self.update_entities(data.get("entities", []))
                            elif msg_type == "battlecard":
                                self.update_battlecard(data.get("battlecard", {}))
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
        """Handle window dragging."""
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, '_drag_pos'):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
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
        "Introduce yourself",
        "Ask about needs",
        "Listen carefully"
    ]))
    
    sys.exit(app.exec())


if __name__ == "__main__":
    run_overlay()
