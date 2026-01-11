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
    capture_mode: str = "local"  # "local" or "remote"
    remote_overlay_url: Optional[str] = None  # e.g., "http://10.119.65.XX:8888" for teammate's machine


# Remote overlay server URLs to trigger (add teammate's IP here)
REMOTE_OVERLAY_SERVERS = [
     "http://10.119.65.126:8888",  # Teammate 1 - uncomment and set IP
]


def trigger_remote_overlays(servers: list = None):
    """Trigger overlay launch on remote machines."""
    import requests
    servers = servers or REMOTE_OVERLAY_SERVERS
    for server_url in servers:
        if not server_url:
            continue
        try:
            print(f"[API] Triggering remote overlay at: {server_url}")
            response = requests.post(f"{server_url}/launch", timeout=5)
            print(f"[API] Remote overlay response: {response.json()}")
        except Exception as e:
            print(f"[API] Remote overlay trigger failed for {server_url}: {e}")


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
                enable_final_sync=config.enable_final_sync,
                capture_mode=config.capture_mode  # "local" or "remote"
            )
        
        # Start session
        session = await start_new_session(session_config)
        
        # Trigger remote overlays on teammate machines
        remote_urls = list(REMOTE_OVERLAY_SERVERS)
        if config and config.remote_overlay_url:
            remote_urls.append(config.remote_overlay_url)
        if remote_urls:
            trigger_remote_overlays(remote_urls)
        
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
        
        def broadcast_battlecard(battlecard):
            try:
                asyncio.run_coroutine_threadsafe(_broadcast({
                    "type": "battlecard",
                    "battlecard": battlecard
                }), loop)
            except Exception as e:
                print(f"[API] Broadcast battlecard error: {e}")
        
        def broadcast_face_sentiment(data):
            try:
                asyncio.run_coroutine_threadsafe(_broadcast(data), loop)
            except Exception as e:
                print(f"[API] Broadcast face sentiment error: {e}")
        
        session.set_callbacks(
            on_hints_update=broadcast_hints,
            on_transcript_update=broadcast_transcript,
            on_status_change=broadcast_status,
            on_entities_update=broadcast_entities,
            on_battlecard=broadcast_battlecard,
            on_face_sentiment=broadcast_face_sentiment
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
    Persists all data to SQLite database.
    """
    try:
        result = await stop_current_session()
        
        if result is None:
            return {
                "status": "not_running",
                "message": "No active session to stop"
            }
        
        # ===== PERSIST TO DATABASE =====
        try:
            from app.core.database import get_database
            import json
            
            db = await get_database()
            
            # Create session record
            session_id = await db.create_session(
                title=result.get('lead', {}).get('lead_name', 'Meeting Session')
            )
            
            # Update session with transcript and summary
            await db.update_session(
                session_id,
                transcript=result.get('transcript', ''),
                summary=result.get('lead', {}).get('summary', ''),
                entities=json.dumps(result.get('entities', [])),
                status='completed'
            )
            
            # Save battlecards
            meeting_json = result.get('lead', {}).get('meeting_json', {})
            battlecards = meeting_json.get('battlecards', [])
            for bc in battlecards:
                await db.save_battlecard(
                    session_id,
                    bc.get('competitor', 'Unknown'),
                    bc.get('counter_points', [])
                )
            
            # Save entities to separate table
            entities = result.get('entities', [])
            for entity in entities:
                await db._connection.execute(
                    "INSERT INTO entities (session_id, text, label, score) VALUES (?, ?, ?, ?)",
                    (session_id, entity.get('text', ''), entity.get('label', ''), entity.get('score', 0))
                )
            await db._connection.commit()
            
            # Save lead info
            lead_info = result.get('lead', {}).get('meeting_json', {}).get('lead', {})
            if lead_info:
                await db._connection.execute(
                    "INSERT INTO leads (session_id, name, email, phone, company) VALUES (?, ?, ?, ?, ?)",
                    (session_id, lead_info.get('name'), lead_info.get('email'), 
                     lead_info.get('phone'), lead_info.get('company'))
                )
                await db._connection.commit()
            
            # ===== POST-CALL SENTIMENT ANALYSIS =====
            try:
                from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
                
                transcript = result.get('transcript', '')
                if transcript:
                    analyzer = SentimentIntensityAnalyzer()
                    sentiment = analyzer.polarity_scores(transcript)
                    
                    # Convert compound score (-1 to 1) to 0-100 scale
                    sentiment_score = int((sentiment['compound'] + 1) * 50)
                    
                    # Calculate engagement metrics from transcript analysis
                    words = len(transcript.split())
                    sentences = transcript.count('.') + transcript.count('?') + transcript.count('!')
                    
                    # Basic engagement heuristics
                    attention = min(100, 60 + (words // 50))  # More words = higher attention
                    interaction = min(100, 50 + (sentences * 2))  # More sentences = more interaction
                    speaking = min(100, 40 + (words // 30))
                    clarity = min(100, 70 + (10 if sentiment['compound'] > 0 else -10))
                    participation = min(100, 55 + (sentences * 3))
                    
                    # Save engagement metrics
                    await db._connection.execute(
                        """INSERT INTO engagement_metrics 
                           (session_id, attention, interaction, sentiment, speaking, participation, clarity)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (session_id, attention, interaction, sentiment_score, speaking, participation, clarity)
                    )
                    await db._connection.commit()
                    
                    print(f"[API] Post-call sentiment score: {sentiment_score}/100")
                    
                    # ===== SYNC TO ODOO CRM =====
                    # Lead stage is determined by sentiment score:
                    # >= 50 = Qualified, < 50 = Lost
                    try:
                        from app.modules.odoo_client.client import OdooClient
                        from app.modules.core.domain import LeadCandidate
                        
                        lead_info = result.get('lead', {}).get('meeting_json', {}).get('lead', {})
                        odoo = OdooClient()
                        
                        lead_data = LeadCandidate(
                            name=lead_info.get('name', 'Meeting Lead'),
                            email=lead_info.get('email', ''),
                            phone=lead_info.get('phone', ''),
                            company=lead_info.get('company', ''),
                            notes=result.get('lead', {}).get('summary', ''),
                            source_summary=transcript[:500] if transcript else ''
                        )
                        
                        starred_hints = result.get('starred_hints', [])
                        
                        # Create lead with sentiment-based stage
                        odoo_lead_id = odoo.create_lead(lead_data, starred_hints, sentiment_score)
                        
                        stage = "Qualified" if sentiment_score >= 50 else "Lost"
                        print(f"[API] Created Odoo Lead ID: {odoo_lead_id} | Stage: {stage} | Sentiment: {sentiment_score}/100")
                        
                        # Save Odoo lead ID to database
                        await db._connection.execute(
                            "UPDATE sessions SET odoo_lead_id = ? WHERE id = ?",
                            (odoo_lead_id, session_id)
                        )
                        await db._connection.commit()
                        
                    except Exception as odoo_error:
                        print(f"[API] Warning: Odoo sync failed: {odoo_error}")
                    
            except Exception as sent_error:
                print(f"[API] Warning: Sentiment analysis failed: {sent_error}")
            
            print(f"[API] Session {session_id} saved to database with {len(battlecards)} battlecards")
            
        except Exception as db_error:
            print(f"[API] Warning: Failed to save to database: {db_error}")
            import traceback
            traceback.print_exc()
        # ===== END DATABASE PERSIST =====
        
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


class StarHintRequest(BaseModel):
    """Request to star/save a hint."""
    hint_text: str
    session_id: Optional[int] = None


class BattlecardRequest(BaseModel):
    """Request for competitive battlecard."""
    competitor_name: str
    context: Optional[str] = ""


@router.post("/star-hint")
async def star_hint(request: StarHintRequest):
    """
    Star/save an important hint for later CRM sync.
    
    The salesman can click a hint to save it. All starred hints
    will be included in the Odoo lead description.
    """
    try:
        from app.core.database import get_database
        
        session = get_active_session()
        session_id = request.session_id
        
        # Use current session ID if not specified
        if not session_id and session:
            session_id = session.state.session_id
        
        if not session_id:
            # Create a temporary session ID
            session_id = 0
        
        db = await get_database()
        hint_id = await db.star_hint(session_id, request.hint_text)
        
        # Also add to session state if active
        if session and request.hint_text not in session.state.starred_hints:
            session.state.starred_hints.append(request.hint_text)
        
        return {
            "status": "starred",
            "hint_id": hint_id,
            "message": f"Hint saved: {request.hint_text[:30]}..."
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/battlecard")
async def get_battlecard(request: BattlecardRequest):
    """
    Generate a competitive battlecard for a competitor.
    
    Returns 3 counter-points the salesman can use immediately,
    enhanced with web research for negative competitor analysis.
    """
    try:
        from app.modules.intelligence.gemini_service import GeminiService
        from app.modules.intelligence.web_insight_service import WebInsightService
        
        # 1. Generate battlecard with Gemini
        gemini = GeminiService()
        battlecard = await gemini.get_battlecard(
            competitor_name=request.competitor_name,
            context=request.context
        )
        
        # 2. Get web insights for competitor (use existing service)
        try:
            web_service = WebInsightService()
            web_insights = {"negative_findings": [], "sources": []}
            
            # Stream insights from web_insight_service
            async for update in web_service.get_negative_insights_stream(request.competitor_name):
                if update.get("type") == "fast" and update.get("data"):
                    data = update["data"]
                    web_insights["negative_findings"].append(data.get("summary", ""))
                    web_insights["sources"] = data.get("sources", [])
                    web_insights["verdict"] = data.get("verdict", "")
                    web_insights["negative_score"] = data.get("negative_score", 0)
                elif update.get("type") == "deep" and update.get("data"):
                    data = update["data"]
                    if data.get("evidence"):
                        web_insights["negative_findings"].extend(data["evidence"])
                    web_insights["verdict"] = data.get("verdict", web_insights.get("verdict", ""))
            
            battlecard["web_research"] = web_insights
            print(f"[API] Web insight: {web_insights.get('verdict', 'N/A')} for {request.competitor_name}")
            
        except Exception as e:
            print(f"[API] Web insight error: {e}")
            battlecard["web_research"] = {"negative_findings": [], "sources": []}
        
        # Save to session if active
        session = get_active_session()
        if session:
            session.state.battlecards.append(battlecard)
            
            # Broadcast to UI
            if session._on_battlecard:
                session._on_battlecard(battlecard)
        
        return {
            "status": "success",
            "battlecard": battlecard
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
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
        },
        "battlecards": session.state.battlecards
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


@router.websocket("/audio-stream")
async def audio_stream(websocket: WebSocket):
    """
    WebSocket endpoint for receiving audio from remote clients.
    
    Clients capture audio locally and stream WAV data here.
    The backend transcribes and processes it.
    """
    await websocket.accept()
    print("[API] Audio stream client connected")
    
    try:
        import tempfile
        import os
        import asyncio
        import threading
        
        def process_audio_in_background(wav_path: str):
            """Process audio in background thread to not block WebSocket."""
            try:
                session = get_active_session()
                if session:
                    # Transcribe
                    segments = session.transcriber.transcribe_with_speakers(wav_path)
                    
                    if segments:
                        # Add to session state
                        session.state.transcript_segments.extend(segments)
                        session.state.audio_chunks_processed += 1
                        
                        # Format and broadcast
                        formatted = session.transcriber.format_transcript_with_speakers(segments)
                        if session._on_transcript_update:
                            session._on_transcript_update(formatted)
                        
                        print(f"[API] Transcribed: {formatted[:50]}...")
                    else:
                        print("[API] No speech detected in audio chunk")
                else:
                    print("[API] No active session for audio")
            except Exception as e:
                print(f"[API] Background transcription error: {e}")
            finally:
                # Cleanup
                if os.path.exists(wav_path):
                    try:
                        os.remove(wav_path)
                    except:
                        pass
        
        while True:
            try:
                # Receive binary WAV data with timeout
                data = await asyncio.wait_for(websocket.receive_bytes(), timeout=120)
                
                if not data:
                    continue
                
                print(f"[API] Received audio chunk: {len(data)} bytes")
                
                # Send ACK immediately to keep connection alive
                try:
                    await websocket.send_text("ACK")
                except:
                    pass
                
                # Save to temp file
                fd, wav_path = tempfile.mkstemp(suffix=".wav")
                os.close(fd)
                
                with open(wav_path, 'wb') as f:
                    f.write(data)
                
                # Process in background thread (don't block WebSocket)
                threading.Thread(
                    target=process_audio_in_background, 
                    args=(wav_path,), 
                    daemon=True
                ).start()
                
            except asyncio.TimeoutError:
                # Send ping to check if client is still alive
                try:
                    await websocket.send_text("ping")
                except:
                    print("[API] Audio stream client timed out")
                    break
            except WebSocketDisconnect:
                print("[API] Audio stream client disconnected")
                break
            except Exception as e:
                print(f"[API] Audio stream error: {e}")
                import traceback
                traceback.print_exc()
                continue
                
    except Exception as e:
        print(f"[API] Audio stream connection error: {e}")
    finally:
        print("[API] Audio stream client removed")


# ==================== DASHBOARD API ENDPOINTS ====================

@router.get("/meetings")
async def get_meetings(limit: int = 20, offset: int = 0):
    """
    Get list of meetings for dashboard.
    Returns meeting history with status, type, and basic metrics.
    """
    try:
        from app.core.database import get_database
        db = await get_database()
        
        cursor = await db._connection.execute(
            """SELECT id, title, start_time, end_time, status, meeting_type, duration_seconds, summary
               FROM sessions 
               ORDER BY start_time DESC 
               LIMIT ? OFFSET ?""",
            (limit, offset)
        )
        rows = await cursor.fetchall()
        
        meetings = []
        for row in rows:
            meeting = dict(row)
            # Format for dashboard
            meetings.append({
                "id": meeting["id"],
                "title": meeting["title"] or f"Meeting #{meeting['id']}",
                "date": meeting["start_time"],
                "type": meeting["meeting_type"] or "Call",
                "status": "Analyzed" if meeting["status"] == "completed" else meeting["status"],
                "duration": meeting["duration_seconds"] or 0,
                "summary": meeting["summary"] or ""
            })
        
        # Get total count
        count_cursor = await db._connection.execute("SELECT COUNT(*) FROM sessions")
        total = (await count_cursor.fetchone())[0]
        
        return {
            "meetings": meetings,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        print(f"[API] Get meetings error: {e}")
        return {"meetings": [], "total": 0, "error": str(e)}


@router.get("/meetings/{meeting_id}")
async def get_meeting_details(meeting_id: int):
    """
    Get detailed meeting information including transcript, entities, and battlecards.
    """
    try:
        from app.core.database import get_database
        import json
        db = await get_database()
        
        # Get session
        session = await db.get_session(meeting_id)
        if not session:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        # Get entities
        entity_cursor = await db._connection.execute(
            "SELECT text, label, score FROM entities WHERE session_id = ?",
            (meeting_id,)
        )
        entities = [dict(row) for row in await entity_cursor.fetchall()]
        
        # Get battlecards
        battlecards = await db.get_battlecards(meeting_id)
        
        # Get starred hints
        starred = await db.get_starred_hints(meeting_id)
        
        # Get lead info
        lead_cursor = await db._connection.execute(
            "SELECT * FROM leads WHERE session_id = ?",
            (meeting_id,)
        )
        lead_row = await lead_cursor.fetchone()
        lead = dict(lead_row) if lead_row else None
        
        # Get engagement metrics
        metrics_cursor = await db._connection.execute(
            "SELECT attention, interaction, sentiment, speaking, participation, clarity FROM engagement_metrics WHERE session_id = ?",
            (meeting_id,)
        )
        metrics_row = await metrics_cursor.fetchone()
        engagement = dict(metrics_row) if metrics_row else None
        
        return {
            "id": session["id"],
            "title": session["title"],
            "date": session["start_time"],
            "end_time": session["end_time"],
            "status": session["status"],
            "transcript": session["final_transcript"],
            "summary": session["summary"],
            "entities": entities,
            "battlecards": battlecards,
            "starred_hints": starred,
            "lead": lead,
            "engagement": engagement,
            "sentiment_score": engagement.get("sentiment", 0) if engagement else 0
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Get meeting details error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leads")
async def get_leads(limit: int = 50):
    """Get list of leads from all meetings."""
    try:
        from app.core.database import get_database
        db = await get_database()
        
        cursor = await db._connection.execute(
            """SELECT l.*, s.title as meeting_title, s.start_time as meeting_date
               FROM leads l
               LEFT JOIN sessions s ON l.session_id = s.id
               ORDER BY l.created_at DESC
               LIMIT ?""",
            (limit,)
        )
        rows = await cursor.fetchall()
        
        return {"leads": [dict(row) for row in rows]}
    except Exception as e:
        print(f"[API] Get leads error: {e}")
        return {"leads": [], "error": str(e)}


# ===== ANALYTICS HELPER FUNCTIONS =====

async def _get_avg_sentiment(db) -> int:
    """Get average sentiment score across all sessions."""
    try:
        cursor = await db._connection.execute(
            "SELECT AVG(sentiment) FROM engagement_metrics"
        )
        row = await cursor.fetchone()
        return int(row[0]) if row[0] else 75  # Default 75 if no data
    except:
        return 75

async def _get_avg_engagement(db) -> int:
    """Get average overall engagement score."""
    try:
        cursor = await db._connection.execute(
            "SELECT AVG((attention + interaction + speaking + participation + clarity) / 5) FROM engagement_metrics"
        )
        row = await cursor.fetchone()
        return int(row[0]) if row[0] else 80  # Default 80 if no data
    except:
        return 80

async def _get_radar_data(db) -> list:
    """Get radar chart data from engagement metrics."""
    try:
        cursor = await db._connection.execute(
            """SELECT AVG(attention) as attention, AVG(interaction) as interaction,
                      AVG(sentiment) as sentiment, AVG(speaking) as speaking,
                      AVG(participation) as participation, AVG(clarity) as clarity
               FROM engagement_metrics"""
        )
        row = await cursor.fetchone()
        
        if row and row[0]:
            return [
                {"subject": "Attention", "A": int(row[0] or 80), "fullMark": 150},
                {"subject": "Interaction", "A": int(row[1] or 75), "fullMark": 150},
                {"subject": "Sentiment", "A": int(row[2] or 70), "fullMark": 150},
                {"subject": "Speaking", "A": int(row[3] or 65), "fullMark": 150},
                {"subject": "Participation", "A": int(row[4] or 70), "fullMark": 150},
                {"subject": "Clarity", "A": int(row[5] or 65), "fullMark": 150}
            ]
    except:
        pass
    
    # Default data
    return [
        {"subject": "Attention", "A": 80, "fullMark": 150},
        {"subject": "Interaction", "A": 75, "fullMark": 150},
        {"subject": "Sentiment", "A": 70, "fullMark": 150},
        {"subject": "Speaking", "A": 65, "fullMark": 150},
        {"subject": "Participation", "A": 70, "fullMark": 150},
        {"subject": "Clarity", "A": 65, "fullMark": 150}
    ]


@router.get("/analytics/overview")
async def get_analytics_overview():
    """
    Get overview analytics for dashboard.
    Returns meeting counts, action items, sentiment scores, and more.
    """
    try:
        from app.core.database import get_database
        from datetime import datetime, timedelta
        db = await get_database()
        
        # Total meetings
        total_cursor = await db._connection.execute("SELECT COUNT(*) FROM sessions")
        total_meetings = (await total_cursor.fetchone())[0]
        
        # Meetings today
        today = datetime.now().strftime("%Y-%m-%d")
        today_cursor = await db._connection.execute(
            "SELECT COUNT(*) FROM sessions WHERE date(start_time) = ?",
            (today,)
        )
        meetings_today = (await today_cursor.fetchone())[0]
        
        # Analyzed meetings (completed)
        analyzed_cursor = await db._connection.execute(
            "SELECT COUNT(*) FROM sessions WHERE status = 'completed'"
        )
        analyzed = (await analyzed_cursor.fetchone())[0]
        
        # Total battlecards generated
        bc_cursor = await db._connection.execute("SELECT COUNT(*) FROM battlecards")
        battlecards_count = (await bc_cursor.fetchone())[0]
        
        # Pending action items
        action_cursor = await db._connection.execute(
            "SELECT COUNT(*) FROM action_items WHERE status = 'pending'"
        )
        pending_actions = (await action_cursor.fetchone())[0]
        
        # Leads count
        leads_cursor = await db._connection.execute("SELECT COUNT(*) FROM leads")
        leads_count = (await leads_cursor.fetchone())[0]
        
        # Recent meetings for list
        recent = await db.get_recent_sessions(5)
        recent_meetings = [{
            "id": m["id"],
            "title": m["title"] or f"Meeting #{m['id']}",
            "date": m["start_time"],
            "type": "Call",
            "status": "Analyzed" if m["status"] == "completed" else m["status"]
        } for m in recent]
        
        return {
            "meetings_analyzed": analyzed,
            "meetings_today": meetings_today,
            "total_meetings": total_meetings,
            "ai_insights_generated": battlecards_count * 3,  # Approximate
            "pending_actions": pending_actions,
            "completed_actions": max(0, pending_actions - 2),  # Placeholder
            "audio_issues": 0,  # Placeholder
            "sentiment_score": await _get_avg_sentiment(db),
            "engagement_score": await _get_avg_engagement(db),
            "leads_count": leads_count,
            "recent_meetings": recent_meetings,
            "radar_data": await _get_radar_data(db)
        }
    except Exception as e:
        print(f"[API] Analytics overview error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "meetings_analyzed": 0,
            "meetings_today": 0,
            "total_meetings": 0,
            "error": str(e)
        }


@router.get("/analytics/engagement")
async def get_engagement_data():
    """Get engagement radar chart data."""
    try:
        from app.core.database import get_database
        db = await get_database()
        
        # Get latest engagement metrics
        cursor = await db._connection.execute(
            """SELECT AVG(attention) as attention, AVG(interaction) as interaction,
                      AVG(sentiment) as sentiment, AVG(speaking) as speaking,
                      AVG(participation) as participation, AVG(clarity) as clarity
               FROM engagement_metrics"""
        )
        row = await cursor.fetchone()
        
        if row and row[0]:
            return {
                "data": [
                    {"subject": "Attention", "A": int(row[0] or 80), "fullMark": 150},
                    {"subject": "Interaction", "A": int(row[1] or 75), "fullMark": 150},
                    {"subject": "Sentiment", "A": int(row[2] or 90), "fullMark": 150},
                    {"subject": "Speaking", "A": int(row[3] or 70), "fullMark": 150},
                    {"subject": "Participation", "A": int(row[4] or 85), "fullMark": 150},
                    {"subject": "Clarity", "A": int(row[5] or 65), "fullMark": 150}
                ],
                "active_participants": 47,
                "avg_speaking_time": 35
            }
        else:
            # Default data if no metrics yet
            return {
                "data": [
                    {"subject": "Attention", "A": 120, "fullMark": 150},
                    {"subject": "Interaction", "A": 98, "fullMark": 150},
                    {"subject": "Sentiment", "A": 86, "fullMark": 150},
                    {"subject": "Speaking", "A": 99, "fullMark": 150},
                    {"subject": "Participation", "A": 85, "fullMark": 150},
                    {"subject": "Clarity", "A": 65, "fullMark": 150}
                ],
                "active_participants": 47,
                "avg_speaking_time": 35
            }
    except Exception as e:
        print(f"[API] Engagement data error: {e}")
        return {"data": [], "error": str(e)}


# ==================== OVERLAY LAUNCHER ====================

# Track overlay process
_overlay_process = None

@router.post("/launch-overlay")
async def launch_overlay():
    """
    Launch the Python overlay UI as a subprocess.
    Uses the venv at the project root.
    """
    global _overlay_process
    import subprocess
    import sys
    from pathlib import Path
    
    try:
        # Check if already running
        if _overlay_process and _overlay_process.poll() is None:
            return {
                "status": "already_running",
                "message": "Overlay is already running",
                "pid": _overlay_process.pid
            }
        
        # Get paths
        # ai_service/app/modules/api/endpoints.py -> meeting_monitor/
        project_root = Path(__file__).parent.parent.parent.parent.parent
        venv_python = project_root / ".venv" / "Scripts" / "python.exe"
        ai_service_dir = project_root / "ai_service"
        
        # Fallback to current Python if venv not found
        if not venv_python.exists():
            venv_python = Path(sys.executable)
            print(f"[API] Venv not found, using: {venv_python}")
        
        print(f"[API] Launching overlay from: {ai_service_dir}")
        print(f"[API] Using Python: {venv_python}")
        
        # Launch overlay as subprocess
        # Run: python -m app.ui.overlay (runs __main__ block)
        _overlay_process = subprocess.Popen(
            [
                str(venv_python),
                "-c",
                "from app.ui.overlay import run_overlay; run_overlay()"
            ],
            cwd=str(ai_service_dir),
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0,
            # Don't capture stdout/stderr so we can see errors in console
        )
        
        print(f"[API] Overlay launched with PID: {_overlay_process.pid}")
        
        return {
            "status": "launched",
            "message": "Overlay UI started successfully",
            "pid": _overlay_process.pid
        }
        
    except Exception as e:
        print(f"[API] Failed to launch overlay: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop-overlay")
async def stop_overlay():
    """Stop the overlay process if running."""
    global _overlay_process
    
    if _overlay_process and _overlay_process.poll() is None:
        _overlay_process.terminate()
        _overlay_process.wait(timeout=5)
        _overlay_process = None
        return {"status": "stopped", "message": "Overlay terminated"}
    
    return {"status": "not_running", "message": "No overlay process to stop"}


@router.get("/overlay-status")
async def get_overlay_status():
    """Check if overlay is running."""
    global _overlay_process
    
    if _overlay_process and _overlay_process.poll() is None:
        return {"running": True, "pid": _overlay_process.pid}
    
    return {"running": False}


# ==================== DOCUMENT UPLOAD ENDPOINTS ====================

ALLOWED_EXTENSIONS = {'.pdf', '.pptx', '.docx'}
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads')

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/documents/upload")
async def upload_document(file: UploadFile = File(...), session_id: Optional[int] = None):
    """
    Upload a document (PDF, PPTX, DOCX) and store metadata in database.
    """
    try:
        # Validate file extension
        filename = file.filename or "unknown"
        ext = os.path.splitext(filename)[1].lower()
        
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Save file to disk
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
            file_size = len(content)
        
        # Store metadata in database
        from app.core.database import get_database
        db = await get_database()
        
        cursor = await db._connection.execute(
            """INSERT INTO documents (session_id, filename, original_filename, file_type, file_size, file_path)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (session_id, unique_filename, filename, ext[1:], file_size, file_path)
        )
        await db._connection.commit()
        doc_id = cursor.lastrowid
        
        print(f"[API] Document uploaded: {filename} ({file_size} bytes)")
        
        return {
            "status": "success",
            "document": {
                "id": doc_id,
                "filename": filename,
                "type": ext[1:],
                "size": file_size,
                "session_id": session_id
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Document upload error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents")
async def list_documents(session_id: Optional[int] = None):
    """
    List all uploaded documents, optionally filtered by session.
    """
    try:
        from app.core.database import get_database
        db = await get_database()
        
        if session_id:
            cursor = await db._connection.execute(
                "SELECT id, original_filename, file_type, file_size, uploaded_at FROM documents WHERE session_id = ? ORDER BY uploaded_at DESC",
                (session_id,)
            )
        else:
            cursor = await db._connection.execute(
                "SELECT id, original_filename, file_type, file_size, uploaded_at, session_id FROM documents ORDER BY uploaded_at DESC LIMIT 50"
            )
        
        rows = await cursor.fetchall()
        documents = []
        for row in rows:
            doc = dict(row)
            doc['filename'] = doc.pop('original_filename')
            documents.append(doc)
        
        return {"documents": documents}
        
    except Exception as e:
        print(f"[API] List documents error: {e}")
        return {"documents": [], "error": str(e)}


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: int):
    """
    Delete a document by ID.
    """
    try:
        from app.core.database import get_database
        db = await get_database()
        
        # Get file path first
        cursor = await db._connection.execute(
            "SELECT file_path FROM documents WHERE id = ?",
            (doc_id,)
        )
        row = await cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete file from disk
        file_path = row['file_path']
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete from database
        await db._connection.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        await db._connection.commit()
        
        return {"status": "deleted", "id": doc_id}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Delete document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== DOCUMENT ANALYSIS (Ollama) ====================

@router.post("/documents/{doc_id}/analyze")
async def analyze_document(doc_id: int, prompt: Optional[str] = None):
    """
    Analyze a document using Ollama vision model with OCR capabilities.
    
    Supports PDF, PPTX, DOCX files.
    
    - PDF: Converts pages to images, uses vision model for OCR
    - PPTX: Extracts text from slides
    - DOCX: Extracts text from paragraphs
    """
    try:
        from app.core.database import get_database
        from app.modules.intelligence.ollama_service import get_ollama_service
        
        db = await get_database()
        
        # Get document from database
        cursor = await db._connection.execute(
            "SELECT file_path, original_filename, file_type FROM documents WHERE id = ?",
            (doc_id,)
        )
        row = await cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_path = row['file_path']
        filename = row['original_filename']
        file_type = row['file_type']
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Document file not found on disk")
        
        print(f"[API] Analyzing document: {filename} ({file_type})")
        
        # Get Ollama service and analyze
        ollama = get_ollama_service()
        result = await ollama.analyze_document(file_path, prompt)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Generate 3 key insights for overlay display
        text_content = result.get("text_content", "") or result.get("summary", "")
        insights = await ollama.generate_key_insights(text_content, 3)
        result["key_insights"] = insights
        
        print(f"[API] Document analysis complete for: {filename}")
        print(f"[API] Generated insights: {insights}")
        
        # Broadcast insights to overlay via WebSocket
        try:
            for insight in insights:
                hint_data = {
                    "type": "hint",
                    "data": {
                        "text": insight,
                        "hint_type": "document_insight",
                        "source": filename,
                        "starred": False
                    }
                }
                await broadcast_to_session(hint_data)
        except Exception as ws_error:
            print(f"[API] WebSocket broadcast error: {ws_error}")
        
        return {
            "status": "success",
            "document_id": doc_id,
            "filename": filename,
            "analysis": result,
            "insights": insights
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Document analysis error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ollama/health")
async def ollama_health():
    """Check Ollama service health and list available models."""
    try:
        from app.modules.intelligence.ollama_service import get_ollama_service
        ollama = get_ollama_service()
        return ollama.check_health()
    except Exception as e:
        return {"status": "error", "message": str(e)}
