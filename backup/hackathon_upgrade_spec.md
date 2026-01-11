Technical Specification: Salesman AI Assistant "Pro" Upgrade
1. Objective
Refactor the existing Meeting Monitor to include speaker-labeled transcription, contextual competitive battlecards, and session persistence to dominate the hackathon demo.

2. Hardware Context (Optimization Target)
GPU: NVIDIA RTX 3070 (8GB VRAM).

CPU: i7-12700H.

RAM: 32GB.

Optimization Goal: All local models (WhisperX, GLiNER) must use device="cuda" with compute_type="float16" to maximize speed without losing accuracy.

3. Core Task A: Speaker Diarization with WhisperX
File: app/modules/transcription/service.py

Upgrade: Replace faster-whisper with whisperX.

Requirements:

Use whisperx.load_model("large-v2", device="cuda", compute_type="float16").

Implement whisperx.DiarizationPipeline to assign speaker IDs (e.g., "SPEAKER_00") to segments.

Maintain sub-second latency for chunks by utilizing your 8GB VRAM.

4. Core Task B: Contextual Battlecards
File: app/modules/intelligence/gemini_service.py

New Logic: When GLiNERService detects a competitor (e.g., AWS, Salesforce, Datadog), trigger a specific "Battlecard" prompt.

Prompt Specification:

"The client mentioned [Competitor]. Provide 3 concise counter-points or 'battlecard' facts that highlight why our solution is superior in terms of [Product Feature]. Keep it under 20 words per point."

UI Update: Display these in the Stealth Overlay with a distinct "Battlecard" badge.

5. Core Task C: Persistence & Action Item Storage
System Change: Implement a local SQLite database using aiosqlite.

Database Schema:

sessions: (id, start_time, title, final_transcript, summary).

starred_hints: (id, session_id, hint_text, timestamp, status).

Workflow:

Create a /api/v1/star-hint endpoint to save a specific hint from the overlay.

Final Meeting End: All "starred" hints must be bundled into the description field of the crm.lead created in Odoo.

Benefit: Ensures no data is lost during a demo crash and provides a "Session History" for the salesman.

6. Core Task D: Speed & Accuracy Optimization
Batching: Process audio in 10s chunks but use overlapping windows to ensure no words are cut off during transcription.

VRAM Management:

Transcription Model: large-v2 (high accuracy).

Summarization Model: MEETING_SUMMARY (quantized to 8-bit).

Entity Extraction: gliner_small-v2.1 (low footprint).

Parallelism: Use asyncio.gather for Gemini insights and Web searches to ensure the UI never lags while waiting for external APIs.

7. Implementation Roadmap for IDE
Step 1: Install whisperx and aiosqlite in requirements.txt.

Step 2: Update config.py to include DATABASE_URL="sqlite+aiosqlite:///./meeting_monitor.db".

Step 3: Refactor TranscriptionService to return List[Dict[speaker, text]].

Step 4: Update LeadWorkflowProcessor to store intermediate data in SQLite.

Step 5: Modify OdooClient to prioritize "Starred Hints" in the final Lead description.