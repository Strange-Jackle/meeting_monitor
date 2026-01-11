# Sales Intelligence Pro 🎯

> **Real-time AI sales assistant** with speaker diarization, competitive battlecards, and stealth overlay.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎤 **Speaker Diarization** | Know WHO is speaking ([SALES_REP] / [CLIENT]) |
| ⚔️ **Battlecards** | Instant counter-points for competitors |
| ⭐ **Star Hints** | Save important hints for CRM sync |
| 🎯 **Stealth Overlay** | Hidden from screen share (Windows 10+) |
| 📝 **GPU Transcription** | WhisperX on CUDA |
| 🎬 **Demo Mode** | Simulated transcript for reliable demos |

## 📋 Requirements

- Windows 10 2004+ | NVIDIA GPU (RTX 3070+ recommended)
- Python 3.10+ | CUDA 11.8+
- Stereo Mix enabled (for live audio)

## 🚀 Quick Start

```bash
# Setup
cd meeting_monitor
python -m venv .venv && .venv\Scripts\activate
pip install -r ai_service/requirements.txt

# Configure
# Create ai_service/app/.env with:
GEMINI_API_KEY=your_key
WHISPER_MODEL_SIZE=small
HF_TOKEN=your_token  # Optional: for speaker diarization
DEMO_SIMULATION_MODE=false

# Run backend
cd ai_service
python -m uvicorn app.main:app --reload --port 8000

# Run overlay (new terminal)
cd ai_service
python -m app.ui.overlay
```

## 🎤 Whisper Models

| Model | VRAM | Speed | Best For |
|-------|------|-------|----------|
| `tiny` | ~1GB | ⚡⚡⚡ | Quick tests |
| `small` | ~2GB | ⚡⚡ | **Recommended** |
| `medium` | ~5GB | ⚡ | Better accuracy |
| `large-v2` | ~6GB | 🐢 | Best accuracy |

Set via `WHISPER_MODEL_SIZE` in `.env`.

## 📡 API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/start-session` | POST | Start capture |
| `/api/v1/stop-session` | POST | Stop & results |
| `/api/v1/star-hint` | POST | Save hint for CRM |
| `/api/v1/battlecard` | POST | Get competitor counter-points |
| `/api/v1/reset-session` | POST | Force reset |
| `/api/v1/session-stream` | WS | Real-time updates |

## 🎬 Demo Mode

For reliable hackathon demos (no live audio needed):
```env
DEMO_SIMULATION_MODE=true
```

Uses `demo_transcript.txt` with simulated sales meeting.

## 📁 Project Structure

```
ai_service/app/
├── core/
│   ├── config.py        # Settings
│   └── database.py      # SQLite persistence
├── modules/
│   ├── api/endpoints.py
│   ├── intelligence/gemini_service.py
│   ├── transcription/service.py  # WhisperX
│   └── workflow/
│       ├── local_capture.py
│       └── live_session.py
└── ui/overlay.py        # Stealth overlay
```

## 🔧 Troubleshooting

### 🔴 "WinError 2" / FFmpeg Missing
We now auto-detect FFmpeg. If it fails:
```bash
winget install "FFmpeg (Essentials Build)"
# Then restart VS Code
```

### ⚠️ "Could not download pyannote..."
You must accept model terms on Hugging Face:
1. [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
2. [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0)
Then add your Read token to `.env` as `HF_TOKEN`.

### ⚠️ "Gemini Rate Limit (429)"
**Normal behavior.** The app will switch to **Dynamic Mock Mode** so your demo continues smoothly with simulated data.

### 🚫 "ReproducibilityWarning" / "FutureWarning"
Safe to ignore. These are library optimization warnings.

## 💰 Costs

| Service | Cost |
|---------|------|
| HuggingFace Token | **FREE** |
| pyannote (local) | **FREE** |
| Whisper (local) | **FREE** |
| Gemini API | Free tier available |

## 📜 License
MIT
