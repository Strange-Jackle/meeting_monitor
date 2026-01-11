# Meeting Monitor AI 🎯

> **AI-Powered Real-Time Meeting Intelligence** — Live transcription, speaker diarization, competitive battlecards, document analysis, face sentiment detection, and a stealth overlay for sales professionals.

![Version](https://img.shields.io/badge/version-2.0-blue) ![Python](https://img.shields.io/badge/python-3.10+-green) ![License](https://img.shields.io/badge/license-MIT-blue)

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🎤 **Speaker Diarization** | Identify WHO is speaking (`[SALES_REP]` / `[CLIENT]`) in real-time |
| ⚔️ **Smart Battlecards** | AI-generated counter-points with live web research |
| 📄 **Document Analysis** | Upload PDF/PPTX/DOCX → AI summary via Ollama vision models |
| 🌐 **Web Insights** | Real-time competitor research via DuckDuckGo |
| 😊 **Face Sentiment** | Client engagement detection via webcam (DeepFace) |
| 🧠 **Gemini AI Hints** | Smart suggestions and research topic identification |
| ⭐ **Star Hints** | Save important hints for CRM export |
| 🎯 **Stealth Overlay** | Hidden from screen share (Windows 10+) |
| 📊 **Analytics Dashboard** | React dashboard with meeting history & engagement metrics |
| 📝 **GPU Transcription** | WhisperX on CUDA for fast, accurate transcription |
| 🗄️ **Persistent Storage** | SQLite database for meetings, leads, documents |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        AUDIO CAPTURE                            │
│   Stereo Mix / WASAPI Loopback / Browser Tab Audio              │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AI PROCESSING PIPELINE                     │
│  ┌─────────┐   ┌──────────────┐   ┌─────────────┐              │
│  │WhisperX │ → │ pyannote.audio│ → │ GLiNER NER  │              │
│  │(Speech) │   │  (Speakers)   │   │ (Entities)  │              │
│  └─────────┘   └──────────────┘   └──────┬──────┘              │
│                                          ▼                      │
│  ┌──────────────┐   ┌─────────────────────────────┐            │
│  │  Gemini AI   │ ← │  Web Research (DuckDuckGo)  │            │
│  │ (Hints/Topics)│   │  + Battlecard Generation    │            │
│  └──────┬───────┘   └─────────────────────────────┘            │
└─────────┼───────────────────────────────────────────────────────┘
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      OUTPUT CHANNELS                            │
│  ┌──────────────┐   ┌────────────────┐   ┌───────────────┐     │
│  │Stealth Overlay│   │ React Dashboard │   │ SQLite Storage│     │
│  │  (PyQt6)     │   │  (Analytics)   │   │  (Persistence)│     │
│  └──────────────┘   └────────────────┘   └───────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 System Requirements

| Component | Requirement |
|-----------|-------------|
| **OS** | Windows 10 2004+ (for stealth overlay) |
| **GPU** | NVIDIA RTX 3060+ (CUDA 11.8+) |
| **Python** | 3.10 or higher |
| **Node.js** | 18+ (for dashboard) |
| **Audio** | Stereo Mix enabled |

---

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <repo-url>
cd meeting_monitor
python -m venv .venv && .venv\Scripts\activate
pip install -r ai_service/requirements.txt
```

### 2. Configure Environment

Create `ai_service/app/.env`:

```env
# Required
WHISPER_MODEL_SIZE=small
HF_TOKEN=your_huggingface_token

# Optional
GEMINI_API_KEY=your_gemini_key
DEMO_SIMULATION_MODE=false
OLLAMA_URL=http://10.119.65.52:11434
```

### 3. Accept HuggingFace Model Terms

Visit and accept:
- [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
- [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0)

### 4. Run the Application

```bash
# Terminal 1: Backend API
run_ai_service.bat

# Terminal 2: Dashboard (optional)
cd meeting_monitor-dashboard
npm install && npm run dev
# Open http://localhost:5173
```

---

## 📊 Dashboard Features

The React dashboard provides:

- **Meeting Intelligence** — Start sessions, upload documents
- **Document Analysis** — AI-powered PDF/PPTX/DOCX summaries
- **Meeting History** — Browse past meetings with search/filter
- **Analytics Overview** — Engagement metrics, sentiment trends
- **Lead Management** — Track extracted entities and contacts

---

## 📡 API Endpoints

### Session Management
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/start-session` | POST | Start meeting capture |
| `/api/v1/stop-session` | POST | Stop session & persist |
| `/api/v1/session-status` | GET | Current session state |
| `/api/v1/launch-overlay` | POST | Launch stealth UI |

### Document Analysis (Ollama)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/documents/upload` | POST | Upload PDF/PPTX/DOCX |
| `/api/v1/documents` | GET | List all documents |
| `/api/v1/documents/{id}/analyze` | POST | AI analysis with OCR |
| `/api/v1/ollama/health` | GET | Ollama service status |

### WebSocket Streams
| Endpoint | Description |
|----------|-------------|
| `/api/v1/session-stream` | Real-time transcripts, entities, battlecards |
| `/api/v1/audio-stream` | Remote audio input |

### Dashboard Data
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/meetings` | GET | List past meetings |
| `/api/v1/meetings/{id}` | GET | Meeting details |
| `/api/v1/analytics/overview` | GET | Dashboard metrics |

---

## 📁 Project Structure

```
meeting_monitor/
├── ai_service/
│   └── app/
│       ├── core/
│       │   ├── config.py              # Settings & env vars
│       │   └── database.py            # SQLite schema & operations
│       ├── modules/
│       │   ├── api/endpoints.py       # REST + WebSocket APIs
│       │   ├── extraction/            # GLiNER entity extraction
│       │   ├── intelligence/
│       │   │   ├── gemini_service.py  # AI hints & topics
│       │   │   ├── ollama_service.py  # Document analysis
│       │   │   └── web_insight_service.py
│       │   ├── transcription/         # WhisperX + diarization
│       │   ├── vision/face_sentiment.py
│       │   └── workflow/              # Session orchestration
│       └── ui/overlay.py              # Stealth PyQt6 overlay
│
├── meeting_monitor-dashboard/         # React frontend
│   ├── components/
│   │   ├── MeetingIntelligenceView.tsx
│   │   ├── MeetingsHistoryView.tsx
│   │   ├── MeetingDetailView.tsx
│   │   └── OverviewView.tsx
│   ├── lib/api.ts                     # API client
│   └── App.tsx                        # Routing
│
├── requirements.txt
├── docker-compose.yml
└── run_ai_service.bat
```

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| **FFmpeg missing** | `winget install "FFmpeg (Essentials Build)"` |
| **pyannote auth error** | Accept HuggingFace model terms (links above) |
| **No Stereo Mix** | Sound Settings → Recording → Show Disabled → Enable |
| **Dashboard CORS** | Backend configured for ports 5173, 3000 |
| **Ollama connection** | Verify URL in `.env` and run `GET /ollama/health` |

---

## 💰 Cost Breakdown

| Component | Cost |
|-----------|------|
| WhisperX (local) | **FREE** |
| pyannote.audio (local) | **FREE** |
| GLiNER NER (local) | **FREE** |
| DeepFace (local) | **FREE** |
| Ollama (local/remote) | **FREE** |
| DuckDuckGo search | **FREE** |
| Gemini API | ~$0.001/call (optional) |

---

## 🎤 Whisper Model Selection

| Model | VRAM | Speed | Use Case |
|-------|------|-------|----------|
| `tiny` | ~1GB | ⚡⚡⚡ | Quick testing |
| `small` | ~2GB | ⚡⚡ | **Recommended** |
| `medium` | ~5GB | ⚡ | Better accuracy |
| `large-v2` | ~6GB | 🐢 | Maximum accuracy |

---

## 📜 License

MIT License - See [LICENSE](LICENSE) for details.

---

**Built with ❤️ by Team Technowolf**
