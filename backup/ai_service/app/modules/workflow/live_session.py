"""
Live Assistant Session - Real-time meeting analysis and hint generation.

Orchestrates:
1. Local screen/audio capture
2. GPU-accelerated transcription  
3. Gemini Vision analysis
4. Quick Hints for overlay UI
5. Final lead generation on session end
"""

import asyncio
import time
import os
from dataclasses import dataclass, field
from typing import Optional, Callable, List, Dict, Any
from enum import Enum

from app.modules.workflow.local_capture import (
    LocalCaptureService, 
    CaptureConfig, 
    Screenshot, 
    AudioChunk
)
from app.modules.transcription.service import TranscriptionService
from app.modules.summarization.service import SummarizationService
from app.modules.extraction.gliner_service import GLiNERService
from app.modules.intelligence.gemini_service import GeminiService
from app.modules.odoo_client.client import OdooClient


class SessionStatus(Enum):
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    PROCESSING = "processing"  # End-of-session processing
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class SessionConfig:
    """Configuration for live assistant session."""
    # Analysis intervals
    insight_interval: float = 5.0  # seconds between Gemini analysis
    transcript_chunk_interval: float = 10.0  # seconds of audio per transcription
    
    # Capture settings
    screen_interval: float = 2.0
    capture_mode: str = "local"  # "local" or "remote" (remote = client streams audio)
    
    # Processing
    enable_vision: bool = True
    enable_transcription: bool = True
    enable_final_sync: bool = True  # Push to Odoo on session end


@dataclass
class SessionState:
    """Current state of a live session."""
    status: SessionStatus = SessionStatus.IDLE
    start_time: Optional[float] = None
    session_id: Optional[int] = None  # Database session ID
    
    # Accumulated data - now with speaker info
    transcript_segments: List[Dict] = field(default_factory=list)  # [{speaker, text, start, end}]
    quick_hints: List[str] = field(default_factory=list)
    detected_entities: List[str] = field(default_factory=list)
    starred_hints: List[str] = field(default_factory=list)
    battlecards: List[Dict] = field(default_factory=list)
    
    # Stats
    screenshots_processed: int = 0
    audio_chunks_processed: int = 0
    gemini_calls: int = 0
    
    @property
    def full_transcript(self) -> str:
        """Get plain text transcript."""
        texts = [seg.get("text", "") if isinstance(seg, dict) else seg for seg in self.transcript_segments]
        return " ".join(texts)
    
    @property
    def formatted_transcript(self) -> str:
        """Get transcript with speaker labels."""
        if not self.transcript_segments:
            return ""
        
        lines = []
        current_speaker = None
        current_text = []
        
        for seg in self.transcript_segments:
            if isinstance(seg, dict):
                speaker = seg.get("speaker", "SPEAKER_00")
                text = seg.get("text", "").strip()
            else:
                speaker = "SPEAKER_00"
                text = str(seg).strip()
            
            if speaker != current_speaker:
                if current_text:
                    lines.append(f"[{current_speaker}]: {' '.join(current_text)}")
                current_speaker = speaker
                current_text = [text] if text else []
            else:
                if text:
                    current_text.append(text)
        
        if current_text:
            lines.append(f"[{current_speaker}]: {' '.join(current_text)}")
        
        return "\n".join(lines)
    
    @property
    def duration(self) -> float:
        if self.start_time:
            return time.time() - self.start_time
        return 0.0


class LiveAssistantSession:
    """
    Manages a real-time meeting assistance session.
    
    Coordinates capture → transcription → analysis → hints pipeline.
    """
    
    def __init__(self, config: Optional[SessionConfig] = None):
        self.config = config or SessionConfig()
        self.state = SessionState()
        
        # Services
        self.capture_service: Optional[LocalCaptureService] = None
        self.transcriber = TranscriptionService()
        self.summarizer = SummarizationService()
        self.extractor = GLiNERService()
        self.gemini = GeminiService()
        self.odoo = OdooClient()
        
        # Tasks
        self._insight_task: Optional[asyncio.Task] = None
        self._transcription_task: Optional[asyncio.Task] = None
        
        # Callbacks
        self._on_hints_update: Optional[Callable[[List[str]], None]] = None
        self._on_transcript_update: Optional[Callable[[str], None]] = None
        self._on_status_change: Optional[Callable[[SessionStatus], None]] = None
        self._on_entities_update: Optional[Callable[[List[str]], None]] = None
        self._on_battlecard: Optional[Callable[[Dict], None]] = None
        
        print("[LiveSession] Session initialized")
    
    def set_callbacks(
        self,
        on_hints_update: Optional[Callable[[List[str]], None]] = None,
        on_transcript_update: Optional[Callable[[str], None]] = None,
        on_status_change: Optional[Callable[[SessionStatus], None]] = None,
        on_entities_update: Optional[Callable[[List[str]], None]] = None,
        on_battlecard: Optional[Callable[[Dict], None]] = None
    ):
        """Set callbacks for real-time updates."""
        self._on_hints_update = on_hints_update
        self._on_transcript_update = on_transcript_update
        self._on_status_change = on_status_change
        self._on_entities_update = on_entities_update
        self._on_battlecard = on_battlecard
    
    def _set_status(self, status: SessionStatus):
        """Update status and notify callback."""
        self.state.status = status
        if self._on_status_change:
            self._on_status_change(status)
        print(f"[LiveSession] Status: {status.value}")
    
    async def start(self):
        """Start the live assistant session."""
        if self.state.status == SessionStatus.RUNNING:
            print("[LiveSession] Already running")
            return
        
        self._set_status(SessionStatus.STARTING)
        self.state.start_time = time.time()
        
        try:
            # Initialize capture service (always needed for screen capture)
            capture_config = CaptureConfig(
                screen_interval=self.config.screen_interval,
                audio_chunk_duration=self.config.transcript_chunk_interval
            )
            self.capture_service = LocalCaptureService(capture_config)
            
            # Set capture callbacks - ONLY register audio callback if NOT remote mode
            if self.config.capture_mode == "local":
                print("[LiveSession] Mode: LOCAL (capturing audio from this machine)")
                self.capture_service.set_callbacks(
                    on_audio_chunk=self._handle_audio_chunk
                )
            else:
                print("[LiveSession] Mode: REMOTE (audio will be streamed from clients)")
                # No audio callback - audio comes via /audio-stream WebSocket
            
            # Start capture
            await self.capture_service.start()
            
            # Start insight loop
            if self.config.enable_vision:
                self._insight_task = asyncio.create_task(self._insight_loop())
            
            self._set_status(SessionStatus.RUNNING)
            print("[LiveSession] Session started")
            
        except Exception as e:
            print(f"[LiveSession] Start error: {e}")
            import traceback
            traceback.print_exc()
            self._set_status(SessionStatus.ERROR)
            raise
    
    async def stop(self) -> Dict[str, Any]:
        """
        Stop the session and finalize.
        
        Returns:
            Final session results including lead data if sync enabled.
        """
        if self.state.status not in [SessionStatus.RUNNING, SessionStatus.STARTING]:
            return {"error": "Session not running"}
        
        self._set_status(SessionStatus.PROCESSING)
        
        # Stop insight loop with timeout
        if self._insight_task:
            self._insight_task.cancel()
            try:
                await asyncio.wait_for(
                    asyncio.shield(self._insight_task), 
                    timeout=2.0
                )
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
        
        # Stop capture with timeout
        if self.capture_service:
            try:
                await asyncio.wait_for(
                    self.capture_service.stop(),
                    timeout=3.0
                )
            except asyncio.TimeoutError:
                print("[LiveSession] Capture stop timed out, forcing...")
                self.capture_service._running = False
        
        # Finalize
        result = {
            "duration": self.state.duration,
            "transcript": self.state.full_transcript,
            "entities": self.state.detected_entities,
            "stats": {
                "screenshots_processed": self.state.screenshots_processed,
                "audio_chunks_processed": self.state.audio_chunks_processed,
                "gemini_calls": self.state.gemini_calls
            }
        }
        
        if self.config.enable_final_sync and self.state.full_transcript:
            # Run finalization (includes Odoo sync)
            try:
                lead_data = await self._finalize_lead()
                result["lead"] = lead_data
            except Exception as e:
                print(f"[LiveSession] Finalization failed: {e}")
                result["lead"] = {"error": str(e)}
        
        self._set_status(SessionStatus.COMPLETED)
        print(f"[LiveSession] Session completed. Duration: {self.state.duration:.1f}s")
        
        return result
    
    def _handle_audio_chunk(self, chunk: AudioChunk):
        """Handle incoming audio chunk - queue it for transcription."""
        if not self.config.enable_transcription:
            return
        
        # Run transcription in a separate thread to avoid blocking audio capture
        import threading
        import re
        import numpy as np
        
        def is_hallucination(text: str) -> bool:
            """Detect Whisper hallucinations from silent audio."""
            text = text.strip()
            if not text:
                return True
                
            # Allow short "Yes", "No", "Ok"
            if len(text) < 2:
                print(f"[Filter] Text too short (<2): '{text}'")
                return True
            
            # Check for repeated single characters (!!!!!!, ......, etc.)
            if re.match(r'^(.)\1{4,}$', text):
                print(f"[Filter] Repeated characters: '{text}'")
                return True
            
            # Check for common hallucination phrases
            hallucination_phrases = [
                "thank you for watching", "thanks for watching",
                "please subscribe", "like and subscribe",
                "see you next time", "[music]", "(music)",
                "subtitle by", "copyright", "all rights reserved"
            ]
            text_lower = text.lower()
            if any(phrase in text_lower for phrase in hallucination_phrases):
                print(f"[Filter] Hallucination phrase detected: '{text}'")
                return True
            
            return False
        
        def is_silent_audio(audio_data: np.ndarray) -> bool:
            """Check if audio is mostly silent."""
            rms = np.sqrt(np.mean(audio_data ** 2))
            return rms < 0.01  # Very low amplitude threshold
        
        def transcribe_in_background():
            try:
                # Check for silence before transcribing
                if is_silent_audio(chunk.data):
                    print("[LiveSession] Skipping silent audio chunk")
                    return
                
                # Save chunk to temp file
                wav_path = LocalCaptureService.audio_chunk_to_wav_file(chunk)
                
                segments = []
                try:
                    # Transcribe with speaker diarization
                    segments = self.transcriber.transcribe_with_speakers(wav_path)
                    
                    # Fallback to plain text if diarization returns empty
                    if not segments:
                        text = self.transcriber.transcribe(wav_path)
                        if text and text.strip():
                            segments = [{"speaker": "SPEAKER_00", "text": text.strip(), "start": 0, "end": 0}]
                finally:
                    # Clean up temp file
                    if os.path.exists(wav_path):
                        try:
                            os.remove(wav_path)
                        except:
                            pass
                
                # Process valid segments
                if segments:
                    valid_segments = []
                    for seg in segments:
                        text = seg.get("text", "").strip()
                        
                        # Filter out hallucinations
                        if text and not is_hallucination(text):
                            valid_segments.append(seg)
                    
                    if valid_segments:
                        # Add to transcript
                        self.state.transcript_segments.extend(valid_segments)
                        self.state.audio_chunks_processed += 1
                        
                        # Format for display (with speaker labels)
                        display_text = " | ".join([
                            f"[{s.get('speaker', 'SPK')}] {s.get('text', '')[:30]}" 
                            for s in valid_segments[:2]  # Show first 2 segments
                        ])
                        print(f"[LiveSession] Transcript: {display_text}...")
                        
                        # Send formatted text to UI
                        if self._on_transcript_update:
                            formatted_text = self.transcriber.format_transcript_with_speakers(valid_segments)
                            self._on_transcript_update(formatted_text)
                        
                        # Placeholder for battlecard generation (assuming it happens here)
                        # If a battlecard is generated based on the valid_segments,
                        # it would be appended to self.state.battlecards and the callback triggered.
                        # For example:
                        # battlecard = self._generate_battlecard_from_segments(valid_segments)
                        # if battlecard:
                        #     self.state.battlecards.append(battlecard)
                        #     if self._on_battlecard:
                        #         self._on_battlecard(battlecard)
                        
                        # Re-broadcasting hints to keep UI fresh (if needed, though usually done in insight loop)
                        if self._on_hints_update:
                            self._on_hints_update(self.state.quick_hints)
                    else:
                        print("[LiveSession] All segments filtered as hallucinations")
                
            except Exception as e:
                print(f"[LiveSession] Transcription error: {e}")
                import traceback
                traceback.print_exc()
        
        # Start transcription in background thread
        thread = threading.Thread(target=transcribe_in_background, daemon=True)
        thread.start()
    
    async def _insight_loop(self):
        """Periodic loop for Gemini vision analysis."""
        print(f"[LiveSession] Insight loop started (interval: {self.config.insight_interval}s)")
        
        while self.state.status == SessionStatus.RUNNING:
            try:
                await asyncio.sleep(self.config.insight_interval)
                
                # Get latest screenshot
                screenshot = self.capture_service.get_latest_screenshot()
                if not screenshot:
                    continue
                
                # Get current transcript context
                transcript_context = self.state.full_transcript
                if not transcript_context:
                    transcript_context = "(No transcript yet)"
                
                # Convert screenshot to base64
                screenshot_b64 = LocalCaptureService.screenshot_to_base64(screenshot)
                
                # Call Gemini Vision
                result = await self.gemini.get_vision_insights(
                    screenshot_b64,
                    transcript_context,
                    max_hints=3
                )
                
                # Update state
                self.state.quick_hints = result.get("quick_hints", [])
                self.state.detected_entities = result.get("detected_entities", [])
                self.state.gemini_calls += 1
                
                print(f"[LiveSession] Insights: {len(self.state.quick_hints)} hints, {len(self.state.detected_entities)} entities")
                
                # Notify UI
                if self._on_hints_update:
                    self._on_hints_update(self.state.quick_hints)
                
                if self._on_entities_update:
                    self._on_entities_update(self.state.detected_entities)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[LiveSession] Insight error: {e}")
                await asyncio.sleep(1.0)
        
        print("[LiveSession] Insight loop ended")
    
    async def _finalize_lead(self) -> Dict[str, Any]:
        """
        Finalize session and create Odoo lead.
        
        Returns lead creation result.
        """
        transcript = self.state.full_transcript
        if not transcript:
            return {"error": "No transcript to process"}
        
        print("[LiveSession] Finalizing lead...")
        
        # 1. Summarize
        summary = self.summarizer.summarize(transcript)
        print(f"[LiveSession] Summary: {summary[:100]}...")
        
        # 2. Extract entities
        entities = self.extractor.extract(transcript)
        print(f"[LiveSession] Extracted {len(entities)} entities")
        
        # 3. Build lead candidate
        lead_name = "Meeting Lead"
        lead_email = None
        lead_phone = None
        lead_company = None
        
        for entity in entities:
            if entity.label == "person" and lead_name == "Meeting Lead":
                lead_name = entity.text
            elif entity.label == "email" and not lead_email:
                lead_email = entity.text
            elif entity.label == "phone number" and not lead_phone:
                lead_phone = entity.text
            elif entity.label == "organization" and not lead_company:
                lead_company = entity.text
        
        # 4. Create Odoo lead
        # 4. Create Odoo lead (in background thread to prevent blocking)
        try:
            print("[LiveSession] Syncing to Odoo (background)...")
            lead_result = await asyncio.to_thread(
                self.odoo.create_lead,
                {
                    "name": lead_name,
                    "email": lead_email,
                    "phone": lead_phone,
                    "company": lead_company,
                    "notes": summary,
                    "source": "Stealth Assistant",
                    "raw_transcript": transcript[:5000]
                },
                self.state.starred_hints  # Pass starred hints
            )
        except Exception as e:
            print(f"[LiveSession] Odoo Sync Failed (Non-critical): {e}")
            lead_result = {"id": 0, "status": "failed_local_only"}
        
        return {
            "lead_id": lead_result.get("id"),
            "lead_name": lead_name,
            "summary": summary,
            "entities_count": len(entities)
        }
    
    # ==================== STATUS ACCESSORS ====================
    
    @property
    def is_running(self) -> bool:
        return self.state.status == SessionStatus.RUNNING
    
    @property
    def current_hints(self) -> List[str]:
        return self.state.quick_hints
    
    @property
    def current_transcript(self) -> str:
        return self.state.full_transcript


# Global session instance for API access
_active_session: Optional[LiveAssistantSession] = None


def get_active_session() -> Optional[LiveAssistantSession]:
    """Get the current active session, if any."""
    global _active_session
    return _active_session

async def start_new_session(config: Optional[SessionConfig] = None) -> LiveAssistantSession:
    """Start a new session (stops any existing one)."""
    global _active_session
    
    # Stop existing session if running
    if _active_session:
        if _active_session.is_running:
            try:
                await _active_session.stop()
            except Exception as e:
                print(f"[LiveSession] Error stopping previous session: {e}")
        # Always reset the session reference
        _active_session = None
    
    # Create and start new session
    _active_session = LiveAssistantSession(config)
    await _active_session.start()
    
    return _active_session


async def stop_current_session() -> Optional[Dict[str, Any]]:
    """Stop the current session and return results."""
    global _active_session
    
    if not _active_session:
        return None
    
    session = _active_session
    
    # Clear global reference immediately (allows new sessions to start)
    _active_session = None
    
    if session.is_running or session.state.status == SessionStatus.STARTING:
        try:
            result = await session.stop()
            return result
        except Exception as e:
            print(f"[LiveSession] Error stopping session: {e}")
            return {"error": str(e)}
    
    return {"status": "not_running"}


def force_reset_session():
    """Force reset the session state (for error recovery)."""
    global _active_session
    if _active_session:
        try:
            if _active_session.capture_service:
                _active_session.capture_service._running = False
        except:
            pass
    _active_session = None
    print("[LiveSession] Session force reset")
