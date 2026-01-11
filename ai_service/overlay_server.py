"""
Remote Overlay Launcher Server

Run this on the machine where you want the overlay to appear.
It listens for HTTP requests and launches the overlay when triggered.

Usage:
  E:\Projects\hackathon\meeting_monitor\ai_service\.venv\Scripts\python overlay_server.py

Or with venv activation:
  cd E:\Projects\hackathon\meeting_monitor\ai_service
  .venv\Scripts\activate
  python overlay_server.py
"""

import subprocess
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

# Configuration - adjust for teammate's machine
OVERLAY_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON = os.path.join(OVERLAY_DIR, ".venv", "Scripts", "python.exe")

# Fallback to system python if venv not found
if not os.path.exists(VENV_PYTHON):
    VENV_PYTHON = sys.executable

overlay_process = None


class OverlayHandler(BaseHTTPRequestHandler):
    def _send_response(self, status, message):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()
        self.wfile.write(json.dumps(message).encode())

    def do_OPTIONS(self):
        self._send_response(200, {"status": "ok"})

    def do_GET(self):
        if self.path == '/status':
            global overlay_process
            is_running = overlay_process and overlay_process.poll() is None
            self._send_response(200, {
                "status": "running" if is_running else "stopped",
                "python": VENV_PYTHON
            })
        else:
            self._send_response(200, {"message": "Overlay Server Ready", "endpoints": ["/launch", "/stop", "/status"]})

    def do_POST(self):
        global overlay_process

        if self.path == '/launch':
            # Check if overlay is already running
            if overlay_process and overlay_process.poll() is None:
                print("[OverlayServer] Overlay already running, skipping relaunch")
                self._send_response(200, {"status": "already_running", "pid": overlay_process.pid})
                return

            print(f"[OverlayServer] Launching overlay with: {VENV_PYTHON}")
            
            # Launch overlay
            overlay_process = subprocess.Popen(
                [VENV_PYTHON, "-m", "app.ui.overlay"],
                cwd=OVERLAY_DIR,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            
            self._send_response(200, {"status": "launched", "pid": overlay_process.pid})

        elif self.path == '/stop':
            if overlay_process and overlay_process.poll() is None:
                overlay_process.terminate()
                overlay_process.wait(timeout=5)
                self._send_response(200, {"status": "stopped"})
            else:
                self._send_response(200, {"status": "not_running"})
        else:
            self._send_response(404, {"error": "Not found"})


def main():
    port = 8888
    print(f"=" * 50)
    print(f"  OVERLAY LAUNCHER SERVER")
    print(f"=" * 50)
    print(f"  Directory: {OVERLAY_DIR}")
    print(f"  Python: {VENV_PYTHON}")
    print(f"  Listening on: http://0.0.0.0:{port}")
    print(f"")
    print(f"  Endpoints:")
    print(f"    POST /launch  - Start overlay")
    print(f"    POST /stop    - Stop overlay")
    print(f"    GET  /status  - Check status")
    print(f"=" * 50)
    
    server = HTTPServer(('0.0.0.0', port), OverlayHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
