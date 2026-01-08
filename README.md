# Meeting Monitor - Stealth Sales Assistant

> **Real-time AI meeting assistant** with GPU transcription, visual analysis, and stealth overlay.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎯 **Stealth Overlay** | Hidden from screen share (Windows 10+) |
| 🎤 **Audio Capture** | WASAPI loopback (Stereo Mix) |
| 📸 **Screen Analysis** | Gemini Vision for context |
| 💡 **Quick Hints** | 3-4 word actionable tips |
| 📝 **GPU Transcription** | Whisper small (2GB VRAM) |
| 📊 **Entity Extraction** | GLiNER for lead generation |

## 📋 Requirements

- Windows 10 2004+ | NVIDIA GPU (RTX 3070+ recommended)
- Python 3.10+ | CUDA 11.8+
- Stereo Mix enabled in Sound settings

## 🚀 Quick Start

```bash
# Setup
cd meeting_monitor
python -m venv .venv && .venv\Scripts\activate
pip install -r ai_service/requirements.txt

# Configure (optional)
echo GEMINI_API_KEY=your_key > ai_service/app/.env

# Run backend
cd ai_service
python -m uvicorn app.main:app --reload --port 8000

# Run overlay (new terminal)
cd ai_service
python -m app.ui.overlay
```

## 🎮 Usage

1. Start backend → Launch overlay
2. Click **Start** → Enable **Stealth** (🙈)
3. Watch hints update every 5 seconds
4. Click **Stop** to end session

## 📡 API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/start-session` | POST | Start capture |
| `/api/v1/stop-session` | POST | Stop & results |
| `/api/v1/reset-session` | POST | Force reset |
| `/api/v1/session-stream` | WS | Real-time updates |

## 📁 Structure

```
ai_service/app/
├── modules/
│   ├── api/endpoints.py        # REST/WebSocket
│   ├── intelligence/gemini_service.py
│   ├── transcription/service.py
│   └── workflow/
│       ├── local_capture.py    # Audio/Screen
│       └── live_session.py     # Pipeline
└── ui/overlay.py               # Stealth UI
```

## 🔧 Troubleshooting

```bash
# Reset stuck session
curl -X POST http://127.0.0.1:8000/api/v1/reset-session

# Check GPU
python -c "import torch; print(torch.cuda.is_available())"
```

## 📜 License
MIT
