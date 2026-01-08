# Meeting Monitor - Technical Architecture for Enhancement

> **Purpose**: This document provides comprehensive technical context for an LLM to suggest enhancements and improvements.

## Current System Overview

### Core Functionality
A real-time meeting assistant that:
1. Captures screen + system audio locally
2. Transcribes audio using Whisper GPU
3. Analyzes visuals using Gemini Vision API
4. Displays actionable "Quick Hints" in a stealth overlay
5. Extracts entities (people, companies, products) for CRM lead generation

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Backend | FastAPI + Uvicorn | REST API + WebSocket server |
| Transcription | faster-whisper (small, CUDA) | Audio → Text (~2GB VRAM) |
| Vision AI | Google Gemini 2.5 Flash | Screenshot + context → Hints |
| Entity Extraction | GLiNER | Named entity recognition |
| Summarization | HuggingFace Transformers | Meeting summary generation |
| Overlay UI | PyQt6 | Transparent, always-on-top window |
| Audio Capture | sounddevice (WASAPI) | System audio loopback |
| Screen Capture | mss | Fast screenshot library |

---

## File Structure

```
ai_service/
├── app/
│   ├── main.py                         # FastAPI app entry
│   ├── core/
│   │   └── config.py                   # Settings, env loading
│   ├── modules/
│   │   ├── api/
│   │   │   └── endpoints.py            # REST + WebSocket routes
│   │   ├── extraction/
│   │   │   └── gliner_service.py       # Entity extraction
│   │   ├── intelligence/
│   │   │   ├── gemini_service.py       # Gemini Vision API
│   │   │   └── web_insight_service.py  # Web search fallback
│   │   ├── odoo_client/
│   │   │   └── client.py               # CRM integration
│   │   ├── summarization/
│   │   │   └── service.py              # Meeting summarizer
│   │   ├── transcription/
│   │   │   └── service.py              # Whisper GPU
│   │   └── workflow/
│   │       ├── local_capture.py        # Screen/Audio capture
│   │       ├── live_session.py         # Real-time pipeline orchestrator
│   │       └── processor.py            # Lead generation workflow
│   ├── static/                         # Web frontend (optional)
│   └── ui/
│       └── overlay.py                  # PyQt6 stealth overlay
└── requirements.txt
```

---

## Key Modules Explained

### 1. LocalCaptureService (local_capture.py)
**Purpose**: Captures screen and system audio.

**Key Methods**:
- `_get_loopback_device()`: Finds Stereo Mix for WASAPI audio
- `_audio_capture_loop()`: Threaded audio capture with callbacks
- `_screen_capture_loop()`: Async screen capture

**Current Limitations**:
- Windows-only (WASAPI)
- Requires Stereo Mix enabled
- No speaker diarization

### 2. LiveAssistantSession (live_session.py)
**Purpose**: Orchestrates the real-time pipeline.

**Data Flow**:
```
Audio Chunk → Whisper → Transcript
Screenshot → Gemini Vision → Quick Hints + Entities
```

**Callbacks**:
- `on_hints_update`: Triggered every 5s with new hints
- `on_transcript_update`: Triggered per audio chunk (10s)
- `on_entities_update`: Triggered when entities detected

### 3. GeminiService (gemini_service.py)
**Purpose**: Multimodal analysis using Gemini Vision.

**Input**: Base64 screenshot + transcript context
**Output**:
```json
{
  "quick_hints": ["Mention pricing", "Ask timeline"],
  "detected_entities": ["John Smith", "Acme Corp"],
  "meeting_context": "Product demo",
  "sentiment": "positive"
}
```

### 4. StealthOverlay (overlay.py)
**Purpose**: Always-on-top transparent window hidden from screen capture.

**Key Features**:
- `SetWindowDisplayAffinity(WDA_EXCLUDEFROMCAPTURE)` Windows API
- WebSocket connection for real-time updates
- Draggable, frameless design

---

## Current Issues & Enhancement Opportunities

### Performance
1. **Transcription Latency**: 3-5s per 10s chunk (acceptable)
2. **Memory Usage**: ~4GB VRAM total (Whisper + GLiNER + Summarizer)
3. **First Start Time**: 15-20s (model loading)

### Functionality Gaps
1. **No Speaker Diarization**: Can't distinguish who is speaking
2. **No Meeting Recording**: Only real-time, no playback
3. **Limited Entity Types**: Only basic NER, no custom entities
4. **No Multi-language**: English only for hints
5. **No Offline Mode**: Requires Gemini API

### UX Issues
1. **Overlay Only**: No web interface for real-time viewing
2. **No Hint History**: Hints overwritten each cycle
3. **No Confidence Scores**: All hints shown equally

### Architecture
1. **Single Session**: Only one session at a time
2. **No Persistence**: Transcript lost on restart
3. **No Authentication**: API completely open
4. **Windows Only**: WASAPI and SetWindowDisplayAffinity

---

## Suggested Enhancement Areas

### High Impact
1. **Speaker Diarization**: Use pyannote-audio or WhisperX
2. **Hint History Panel**: Show last 10 hints with timestamps
3. **Transcript Persistence**: Save to SQLite with session ID
4. **Web Dashboard**: Real-time view without overlay

### Medium Impact
1. **Custom Entity Training**: Fine-tune GLiNER for sales terms
2. **Meeting Recording**: Optional audio/video save
3. **Multi-session**: Support multiple concurrent users
4. **API Authentication**: JWT or API keys

### Low Impact / Nice-to-Have
1. **Cross-platform Audio**: macOS/Linux support
2. **Mobile Companion App**: View hints on phone
3. **Calendar Integration**: Auto-start for scheduled meetings
4. **CRM Sync Improvements**: Real-time Odoo/Salesforce push

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/start-session` | POST | Start capture |
| `/api/v1/stop-session` | POST | Stop & get results |
| `/api/v1/reset-session` | POST | Force cleanup |
| `/api/v1/session-status` | GET | Current state |
| `/api/v1/session-stream` | WS | Real-time updates |

### WebSocket Message Types
```json
{"type": "hints", "hints": ["...", "..."]}
{"type": "transcript", "text": "..."}
{"type": "entities", "entities": ["...", "..."]}
{"type": "status", "status": "running|processing|completed"}
```

---

## Environment Variables

```env
GEMINI_API_KEY=xxx          # Required for real AI insights
ODOO_URL=https://...        # Optional CRM
ODOO_DB=dbname
ODOO_USERNAME=admin
ODOO_PASSWORD=xxx
```

---

## Questions for Enhancement LLM

1. How can we add speaker diarization without significantly increasing latency?
2. What's the best approach for persisting session data while maintaining real-time performance?
3. How should we structure a web dashboard that mirrors the overlay functionality?
4. What security measures should be prioritized for enterprise deployment?
5. How can we optimize VRAM usage further while maintaining transcription quality?
