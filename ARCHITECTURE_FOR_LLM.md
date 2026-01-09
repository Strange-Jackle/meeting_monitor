# Meeting Monitor - Technical Architecture for Enhancement

> **Purpose**: This document provides comprehensive technical context for an LLM to suggest enhancements and improvements.

## Current System Overview

### Core Functionality
A real-time "Sales Intelligence Pro" assistant that:
1. **Captures** screen + system audio locally (Stealth mode)
2. **Transcribes** audio using **WhisperX** (GPU) with **Speaker Diarization**
3. **Analyzes** visuals using **Gemini 2.0 Flash** (Vision API)
4. **Persists** session data and "Starred Hints" to **SQLite**
5. **Generates** competitive **Battlecards** on demand
6. **Syncs** leads to **Odoo CRM** in background

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Backend | FastAPI + Uvicorn | REST API + WebSocket server |
| Transcription | **WhisperX (Large-v2)** | Audio → Text + Diarization |
| Diarization | Pyannote Audio | Speaker ID (User Auth Required) |
| Vision AI | Google Gemini 2.0 Flash | Screenshot + context → Hints |
| Database | **aiosqlite** | Async SQLite persistence |
| Entity Extraction | GLiNER | Named entity recognition |
| Overlay UI | PyQt6 | Transparent, always-on-top window |
| Audio Capture | sounddevice (WASAPI) | System audio loopback |

---

## File Structure

```
ai_service/
├── app/
│   ├── main.py                         # FastAPI app entry
│   ├── core/
│   │   ├── config.py                   # Settings (Env vars)
│   │   └── database.py                 # SQLite Ops (Sessions, Hints)
│   ├── modules/
│   │   ├── api/
│   │   │   └── endpoints.py            # Routes: /start-session, /star-hint, /battlecard
│   │   ├── intelligence/
│   │   │   └── gemini_service.py       # Gemini: Vision Insights + Battlecards
│   │   ├── odoo_client/
│   │   │   └── client.py               # CRM integration (Async wrapped)
│   │   ├── transcription/
│   │   │   └── service.py              # WhisperX + DiarizationPipeline
│   │   └── workflow/
│   │       ├── local_capture.py        # Capture (Screen/Audio/DemoMode)
│   │       └── live_session.py         # Pipeline Orchestrator
│   └── ui/
│       └── overlay.py                  # PyQt6 stealth overlay
```

---

## Key Modules Explained

### 1. LiveSession (live_session.py)
**Purpose**: The central nervous system.
**Flow**:
```
Audio -> Buffer -> WhisperX -> Diarized Segments -> Transcript
Screenshot -> Gemini -> Hints/Entities -> WebSocket -> UI
```
**Robustness**:
- Auto-restarts audio stream if device disconnects
- Filters hallucinations (repetitive text)
- Background threads for Odoo sync

### 2. TranscriptionService (transcription/service.py)
**Purpose**: High-fidelity audio processing.
**Features**:
- **Diarization**: Identifies separate speakers (requires HF_TOKEN)
- **Fallback**: Downgrades to CPU if CUDA fails
- **Safety**: Checks for FFmpeg on startup

### 3. Database (database.py)
**Purpose**: Local persistence.
**Schema**:
- `sessions`: id, start_time, duration, notes
- `starred_hints`: id, session_id, hint_text (Synced to CRM)
- `battlecards`: id, competitor_name, content

### 4. LocalCaptureService (local_capture.py)
**Purpose**: Hardware interface.
**Features**:
- **Demo Simulation Mode**: Replays `demo_transcript.txt` if live audio is risky
- **WASAPI Loopback**: Captures "What U Hear"

---

## Current Issues & Limits

### Known Limitations
1.  **VRAM Hungry**: Large-v2 + Diarization requires ~6GB VRAM.
2.  **Windows Only**: Relies on specific Windows Audio Session APIs.
3.  **Hugging Face Auth**: User must manually accept terms for Pyannote models.
4.  **Odoo Sync**: One-way only (App -> Odoo).

### Future Enhancement Opportunities
1.  **Web Dashboard**: Replace PyQt overlay with a React/Next.js real-time dashboard.
2.  **Audio Recording**: Save the actual .wav file for playback.
3.  **Multi-Language**: Add translation layer to Gemini prompt.
4.  **Custom Battlecards**: Allow user to edit battlecards in UI.

---

## Questions for Future LLMs

1.  How can we implement a "Review Mode" to playback the audio alongside the transcript segments stored or simulated?
2.  What is the best way to package this Python/CUDA complex stack into a one-click installer for non-technical sales reps?
3.  How can we optimize the `insight_interval` dynamically based on speech velocity?

