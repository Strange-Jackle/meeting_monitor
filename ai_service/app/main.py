from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.modules.api.endpoints import router as api_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler for startup and shutdown.
    Ensures proper cleanup of all resources.
    """
    # ===== STARTUP =====
    print("[Server] Starting up...")
    yield
    
    # ===== SHUTDOWN =====
    print("[Server] Shutting down, cleaning up resources...")
    
    # 1. Stop any active session
    try:
        from app.modules.workflow.live_session import stop_current_session, force_reset_session
        await stop_current_session()
        force_reset_session()
        print("[Server] Active session stopped")
    except Exception as e:
        print(f"[Server] Session cleanup error: {e}")
    
    # 2. Close database connection
    try:
        from app.core.database import close_database
        await close_database()
        print("[Server] Database closed")
    except Exception as e:
        print(f"[Server] Database cleanup error: {e}")
    
    # 3. Stop overlay process if running
    try:
        from app.modules.api.endpoints import _overlay_process
        if _overlay_process and _overlay_process.poll() is None:
            _overlay_process.terminate()
            _overlay_process.wait(timeout=3)
            print("[Server] Overlay process terminated")
    except Exception as e:
        print(f"[Server] Overlay cleanup error: {e}")
    
    print("[Server] Cleanup complete")


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# CORS middleware for dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative dev port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://10.119.65.34:3000",  # Network access
        "http://10.119.65.34:5173",
        "*",  # Allow all origins for development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

# Serve Static Files (Frontend)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse("app/static/index.html")
