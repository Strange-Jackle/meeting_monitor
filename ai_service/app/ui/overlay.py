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


class SignalBridge(QObject):
    """Bridge for thread-safe signal emission."""
    hints_updated = pyqtSignal(list)
    transcript_updated = pyqtSignal(str)
    status_updated = pyqtSignal(str)
    entities_updated = pyqtSignal(list)


class StealthOverlay(QMainWindow):
    """
    Stealth overlay window for real-time sales assistance.
    
    Can be hidden from screen capture using Windows API.
    """
    
    def __init__(self):
        super().__init__()
        
        self._stealth_enabled = False
        self._is_recording = False
        
        # Signal bridge for thread-safe updates
        self.signals = SignalBridge()
        self.signals.hints_updated.connect(self._on_hints_updated)
        self.signals.transcript_updated.connect(self._on_transcript_updated)
        self.signals.status_updated.connect(self._on_status_updated)
        self.signals.entities_updated.connect(self._on_entities_updated)
        
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
        
        # Hint labels (3 slots)
        self.hint_labels = []
        for i in range(3):
            label = QLabel(f"• Waiting for analysis...")
            label.setStyleSheet("color: #CCC; font-size: 13px; padding-left: 8px;")
            label.setWordWrap(True)
            self.hint_labels.append(label)
            layout.addWidget(label)
        
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
        """Update hint labels."""
        for i, label in enumerate(self.hint_labels):
            if i < len(hints):
                label.setText(f"• {hints[i]}")
                label.setStyleSheet("color: #FFF; font-size: 13px; padding-left: 8px;")
            else:
                label.setText("• ...")
                label.setStyleSheet("color: #666; font-size: 13px; padding-left: 8px;")
    
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
                                self.update_hints(data.get("hints", []))
                            elif msg_type == "transcript":
                                self.update_transcript(data.get("text", ""))
                            elif msg_type == "status":
                                status = data.get("status", "")
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
