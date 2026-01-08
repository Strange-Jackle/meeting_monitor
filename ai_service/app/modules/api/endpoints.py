from fastapi import APIRouter, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from app.modules.core.domain import SalesSummary
from app.modules.workflow.processor import LeadWorkflowProcessor
import shutil
import os
import uuid
import json
import asyncio

router = APIRouter()
processor = LeadWorkflowProcessor() # Singleton-ish context

from pydantic import BaseModel
from typing import Optional

class InsightRequest(BaseModel):
    entity: str

class MeetingRequest(BaseModel):
    meeting_url: str

# Store active meeting sessions for status checks
active_meetings = {}

@router.post("/process-summary")
async def process_summary(summary: SalesSummary):
    try:
        result = await processor.process_summary_to_lead(summary.content)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/fetch-insight-details")
async def fetch_insight_details(req: InsightRequest):
    try:
        # We access the insight service directly from the processor instance
        # In a cleaner architecture, this would be a dependency injection
        data = await processor.insights_service.get_detailed_insights_async(req.entity)
        return data
    except Exception as e:
        print(f"Error fetching details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-audio")
async def process_audio(file: UploadFile = File(...)):
    temp_filename = f"temp_{uuid.uuid4()}.{file.filename.split('.')[-1]}"
    temp_path = os.path.join("temp_audio", temp_filename)
    
    # Ensure temp dir exists
    os.makedirs("temp_audio", exist_ok=True)
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        result = await processor.process_audio_file(temp_path)
        return result
        
    except Exception as e:
        print(f"Error processing audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)


# ==================== DEPRECATED ENDPOINTS ====================
# The following endpoints have been removed:
#   - POST /process-meeting (Vexa bot integration)
#   - WS /meeting-stream/{session_id} (Vexa transcript stream)
#   - GET /meeting-status/{session_id} (Vexa session status)
#   - POST /process-meeting-sync (Vexa SSE stream)
#
# Live meeting monitoring is now handled by LOCAL CAPTURE:
#   - POST /start-session (starts screen/audio capture)
#   - POST /stop-session (stops capture, creates lead)
#   - GET /session-status (current session state)
#   - WS /session-stream (real-time hints/transcript)
# =============================================================


# ==================== STEALTH ASSISTANT SESSION ENDPOINTS ====================

from app.modules.workflow.live_session import (
    get_active_session,
    start_new_session,
    stop_current_session,
    force_reset_session,
    SessionConfig,
    SessionStatus
)

# Store WebSocket connections for broadcasting
session_websockets = set()


class SessionConfigRequest(BaseModel):
    """Configuration for starting a new session."""
    insight_interval: float = 5.0
    screen_interval: float = 2.0
    enable_vision: bool = True
    enable_transcription: bool = True
    enable_final_sync: bool = True


@router.post("/start-session")
async def start_session(config: Optional[SessionConfigRequest] = None):
    """
    Start a new stealth assistant session.
    
    Begins local screen/audio capture and real-time analysis.
    """
    try:
        # Build config
        session_config = None
        if config:
            session_config = SessionConfig(
                insight_interval=config.insight_interval,
                screen_interval=config.screen_interval,
                enable_vision=config.enable_vision,
                enable_transcription=config.enable_transcription,
                enable_final_sync=config.enable_final_sync
            )
        
        # Start session
        session = await start_new_session(session_config)
        
        # Get the current event loop for thread-safe callbacks
        loop = asyncio.get_running_loop()
        
        # Set up callbacks to broadcast to WebSockets
        # These must be thread-safe because audio capture runs in a thread
        def broadcast_hints(hints):
            try:
                asyncio.run_coroutine_threadsafe(_broadcast({
                    "type": "hints",
                    "hints": hints
                }), loop)
            except Exception as e:
                print(f"[API] Broadcast hints error: {e}")
        
        def broadcast_transcript(text):
            try:
                asyncio.run_coroutine_threadsafe(_broadcast({
                    "type": "transcript",
                    "text": text
                }), loop)
            except Exception as e:
                print(f"[API] Broadcast transcript error: {e}")
        
        def broadcast_status(status):
            try:
                asyncio.run_coroutine_threadsafe(_broadcast({
                    "type": "status",
                    "status": status.value
                }), loop)
            except Exception as e:
                print(f"[API] Broadcast status error: {e}")
        
        def broadcast_entities(entities):
            try:
                asyncio.run_coroutine_threadsafe(_broadcast({
                    "type": "entities",
                    "entities": entities
                }), loop)
            except Exception as e:
                print(f"[API] Broadcast entities error: {e}")
        
        session.set_callbacks(
            on_hints_update=broadcast_hints,
            on_transcript_update=broadcast_transcript,
            on_status_change=broadcast_status,
            on_entities_update=broadcast_entities
        )
        
        return {
            "status": "started",
            "message": "Stealth assistant session started",
            "config": {
                "insight_interval": session.config.insight_interval,
                "screen_interval": session.config.screen_interval
            }
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop-session")
async def stop_session():
    """
    Stop the current stealth assistant session.
    
    Finalizes transcription, creates lead, and returns results.
    """
    try:
        result = await stop_current_session()
        
        if result is None:
            return {
                "status": "not_running",
                "message": "No active session to stop"
            }
        
        return {
            "status": "completed",
            "message": "Session stopped and processed",
            "result": result
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset-session")
async def reset_session():
    """
    Force reset the session state.
    
    Use this if the session gets stuck or for error recovery.
    """
    try:
        force_reset_session()
        return {
            "status": "reset",
            "message": "Session state cleared"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session-status")
async def get_session_status():
    """
    Get the current session status and latest data.
    """
    session = get_active_session()
    
    if not session:
        return {
            "status": "idle",
            "message": "No active session"
        }
    
    return {
        "status": session.state.status.value,
        "duration": session.state.duration,
        "hints": session.state.quick_hints,
        "entities": session.state.detected_entities,
        "transcript_length": len(session.state.full_transcript),
        "stats": {
            "screenshots_processed": session.state.screenshots_processed,
            "audio_chunks_processed": session.state.audio_chunks_processed,
            "gemini_calls": session.state.gemini_calls
        }
    }


@router.websocket("/session-stream")
async def session_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time session updates.
    
    Broadcasts:
    - hints: Quick hints from Gemini
    - transcript: New transcript segments
    - status: Session status changes
    - entities: Detected entities
    """
    await websocket.accept()
    session_websockets.add(websocket)
    print("[API] WebSocket client connected")
    
    try:
        # Send initial status
        session = get_active_session()
        if session:
            await websocket.send_json({
                "type": "status",
                "status": session.state.status.value,
                "hints": session.state.quick_hints
            })
        else:
            await websocket.send_json({
                "type": "status",
                "status": "idle"
            })
        
        # Keep connection alive with periodic pings
        while True:
            try:
                # Use timeout to allow for periodic checks
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0  # 30 second timeout
                )
                
                if data == "ping":
                    await websocket.send_text("pong")
                    
            except asyncio.TimeoutError:
                # Send keep-alive ping
                try:
                    await websocket.send_json({"type": "ping"})
                except:
                    break
                    
            except WebSocketDisconnect:
                print("[API] WebSocket client disconnected")
                break
            except Exception as e:
                print(f"[API] WebSocket error: {e}")
                break
                
    except Exception as e:
        print(f"[API] WebSocket connection error: {e}")
    finally:
        session_websockets.discard(websocket)
        print("[API] WebSocket client removed")


async def _broadcast(message: dict):
    """Broadcast message to all connected WebSocket clients."""
    if not session_websockets:
        return
    
    disconnected = set()
    for ws in session_websockets:
        try:
            await ws.send_json(message)
        except:
            disconnected.add(ws)
    
    # Clean up disconnected clients
    for ws in disconnected:
        session_websockets.discard(ws)
