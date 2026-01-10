"""
SQLite Database for Session Persistence and Starred Hints.

Tables:
- sessions: Store meeting transcripts, summaries, and metadata
- starred_hints: Store salesman-flagged hints for CRM sync
"""

import aiosqlite
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.core.config import settings


class Database:
    """Async SQLite database manager."""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.DATABASE_PATH
        self._connection: Optional[aiosqlite.Connection] = None
    
    async def connect(self):
        """Initialize database connection and create tables."""
        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row
        await self._create_tables()
        print(f"[Database] Connected to {self.db_path}")
    
    async def close(self):
        """Close database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None
    
    async def _create_tables(self):
        """Create database schema if not exists."""
        await self._connection.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                title TEXT,
                final_transcript TEXT,
                summary TEXT,
                entities TEXT,
                status TEXT DEFAULT 'active'
            );
            
            CREATE TABLE IF NOT EXISTS starred_hints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                hint_text TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );
            
            CREATE TABLE IF NOT EXISTS battlecards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                competitor TEXT NOT NULL,
                points TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );
        """)
        await self._connection.commit()
    
    # ==================== SESSION OPERATIONS ====================
    
    async def create_session(self, title: Optional[str] = None) -> int:
        """Create a new session and return its ID."""
        cursor = await self._connection.execute(
            "INSERT INTO sessions (title, start_time) VALUES (?, ?)",
            (title or f"Meeting {datetime.now().strftime('%Y-%m-%d %H:%M')}", datetime.now())
        )
        await self._connection.commit()
        return cursor.lastrowid
    
    async def update_session(
        self,
        session_id: int,
        transcript: Optional[str] = None,
        summary: Optional[str] = None,
        entities: Optional[str] = None,
        status: Optional[str] = None
    ):
        """Update session data."""
        updates = []
        values = []
        
        if transcript is not None:
            updates.append("final_transcript = ?")
            values.append(transcript)
        if summary is not None:
            updates.append("summary = ?")
            values.append(summary)
        if entities is not None:
            updates.append("entities = ?")
            values.append(entities)
        if status is not None:
            updates.append("status = ?")
            values.append(status)
            if status == "completed":
                updates.append("end_time = ?")
                values.append(datetime.now())
        
        if updates:
            values.append(session_id)
            await self._connection.execute(
                f"UPDATE sessions SET {', '.join(updates)} WHERE id = ?",
                values
            )
            await self._connection.commit()
    
    async def get_session(self, session_id: int) -> Optional[Dict[str, Any]]:
        """Get session by ID."""
        cursor = await self._connection.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    
    async def get_recent_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent sessions."""
        cursor = await self._connection.execute(
            "SELECT * FROM sessions ORDER BY start_time DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    
    # ==================== STARRED HINTS OPERATIONS ====================
    
    async def star_hint(self, session_id: int, hint_text: str) -> int:
        """Star a hint for later CRM sync."""
        cursor = await self._connection.execute(
            "INSERT INTO starred_hints (session_id, hint_text) VALUES (?, ?)",
            (session_id, hint_text)
        )
        await self._connection.commit()
        print(f"[Database] Starred hint: {hint_text[:30]}...")
        return cursor.lastrowid
    
    async def get_starred_hints(self, session_id: int) -> List[Dict[str, Any]]:
        """Get all starred hints for a session."""
        cursor = await self._connection.execute(
            "SELECT * FROM starred_hints WHERE session_id = ? ORDER BY timestamp",
            (session_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    
    async def mark_hints_synced(self, session_id: int):
        """Mark all hints as synced to CRM."""
        await self._connection.execute(
            "UPDATE starred_hints SET status = 'synced' WHERE session_id = ?",
            (session_id,)
        )
        await self._connection.commit()
    
    # ==================== BATTLECARD OPERATIONS ====================
    
    async def save_battlecard(self, session_id: int, competitor: str, points: List[str]) -> int:
        """Save a battlecard for a session."""
        import json
        cursor = await self._connection.execute(
            "INSERT INTO battlecards (session_id, competitor, points) VALUES (?, ?, ?)",
            (session_id, competitor, json.dumps(points))
        )
        await self._connection.commit()
        return cursor.lastrowid
    
    async def get_battlecards(self, session_id: int) -> List[Dict[str, Any]]:
        """Get all battlecards for a session."""
        import json
        cursor = await self._connection.execute(
            "SELECT * FROM battlecards WHERE session_id = ? ORDER BY timestamp",
            (session_id,)
        )
        rows = await cursor.fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d["points"] = json.loads(d["points"])
            result.append(d)
        return result


# Global database instance
_db: Optional[Database] = None


async def get_database() -> Database:
    """Get or create the global database instance."""
    global _db
    if _db is None:
        _db = Database()
        await _db.connect()
    return _db


async def close_database():
    """Close the global database connection."""
    global _db
    if _db:
        await _db.close()
        _db = None
