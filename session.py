"""
Session management for VPS-CC-MCP.

Sessions persist logical context across invocations:
- Current project focus
- Tool call history
- Accumulated context

Storage: One JSON file per session, append-only log format.
"""

import json
import secrets
import string
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from config import (
    SESSION_DIR,
    SESSION_TTL_HOURS,
    SESSION_ID_PREFIX,
    SESSION_ID_LENGTH,
)


class SessionEntry(dict):
    """A single entry in the session log."""

    @classmethod
    def create(
        cls,
        entry_type: str,
        tool: Optional[str] = None,
        params: Optional[dict[str, Any]] = None,
        result: Optional[Any] = None,
        error: Optional[dict[str, Any]] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> "SessionEntry":
        """Create a new session entry."""
        return cls(
            timestamp=datetime.utcnow().isoformat() + "Z",
            type=entry_type,
            tool=tool,
            params=params,
            result=result,
            error=error,
            context=context,
        )


class Session:
    """
    Manages a single session's state and persistence.

    Sessions are stored as append-only JSON log files:
    - Each line is a JSON object (JSON Lines format)
    - Entries are never modified after writing
    - This makes debugging and replay trivial
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.session_file = SESSION_DIR / f"{session_id}.jsonl"
        self._project_focus: Optional[str] = None
        self._entries: list[SessionEntry] = []
        self._loaded = False

    @property
    def project_focus(self) -> Optional[str]:
        """Get the current project focus path."""
        if not self._loaded:
            self._load()
        return self._project_focus

    @project_focus.setter
    def project_focus(self, path: Optional[str]) -> None:
        """Set the project focus path."""
        self._project_focus = path

    def _load(self) -> None:
        """Load session from disk if it exists."""
        if self._loaded:
            return

        if self.session_file.exists():
            with open(self.session_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        entry = SessionEntry(json.loads(line))
                        self._entries.append(entry)
                        # Reconstruct state from log
                        if entry.get("type") == "context_change":
                            ctx = entry.get("context", {})
                            if "project_focus" in ctx:
                                self._project_focus = ctx["project_focus"]

        self._loaded = True

    def append(self, entry: SessionEntry) -> None:
        """Append an entry to the session log (write-through)."""
        if not self._loaded:
            self._load()

        self._entries.append(entry)

        # Ensure session directory exists
        SESSION_DIR.mkdir(parents=True, exist_ok=True)

        # Append to file (append-only, never mutate past entries)
        with open(self.session_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(dict(entry)) + "\n")

    def log_tool_call(
        self,
        tool: str,
        params: dict[str, Any],
        result: Optional[Any] = None,
        error: Optional[dict[str, Any]] = None,
    ) -> None:
        """Log a tool invocation."""
        entry = SessionEntry.create(
            entry_type="tool_call",
            tool=tool,
            params=params,
            result=result,
            error=error,
            context={"project_focus": self._project_focus},
        )
        self.append(entry)

    def log_context_change(self, project_focus: Optional[str]) -> None:
        """Log a context change (project focus)."""
        self._project_focus = project_focus
        entry = SessionEntry.create(
            entry_type="context_change",
            context={"project_focus": project_focus},
        )
        self.append(entry)

    def get_history(self, limit: int = 10) -> list[SessionEntry]:
        """Get recent session history."""
        if not self._loaded:
            self._load()
        return self._entries[-limit:]

    def is_expired(self) -> bool:
        """Check if session has expired based on TTL."""
        if not self.session_file.exists():
            return True

        mtime = datetime.fromtimestamp(self.session_file.stat().st_mtime)
        expiry = mtime + timedelta(hours=SESSION_TTL_HOURS)
        return datetime.now() > expiry


class SessionManager:
    """
    Manages session lifecycle: create, resume, continue.
    """

    def __init__(self):
        self._current_session: Optional[Session] = None

    @staticmethod
    def generate_session_id() -> str:
        """Generate a unique session ID."""
        suffix = "".join(
            secrets.choice(string.ascii_lowercase + string.digits)
            for _ in range(SESSION_ID_LENGTH)
        )
        return f"{SESSION_ID_PREFIX}{suffix}"

    def create_session(self) -> Session:
        """Create a new session."""
        session_id = self.generate_session_id()
        session = Session(session_id)

        # Log session start
        entry = SessionEntry.create(entry_type="session_start")
        session.append(entry)

        self._current_session = session
        return session

    def resume_session(self, session_id: str) -> Optional[Session]:
        """Resume an existing session by ID."""
        session = Session(session_id)

        if not session.session_file.exists():
            return None

        if session.is_expired():
            return None

        # Force load to reconstruct state
        session._load()

        # Log session resume
        entry = SessionEntry.create(entry_type="session_resume")
        session.append(entry)

        self._current_session = session
        return session

    def continue_last_session(self) -> Optional[Session]:
        """Continue the most recent session."""
        SESSION_DIR.mkdir(parents=True, exist_ok=True)

        # Find most recently modified session file
        session_files = list(SESSION_DIR.glob("sess_*.jsonl"))
        if not session_files:
            return None

        # Sort by modification time, newest first
        session_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        for session_file in session_files:
            session_id = session_file.stem
            session = Session(session_id)

            if not session.is_expired():
                session._load()

                # Log session continue
                entry = SessionEntry.create(entry_type="session_continue")
                session.append(entry)

                self._current_session = session
                return session

        return None

    def get_or_create_session(
        self,
        resume_id: Optional[str] = None,
        continue_last: bool = False,
    ) -> Session:
        """
        Get a session based on flags, creating new if needed.

        Priority:
        1. Resume specific session by ID
        2. Continue last session
        3. Create new session
        """
        if resume_id:
            session = self.resume_session(resume_id)
            if session:
                return session
            # Fall through to create new if resume fails

        if continue_last:
            session = self.continue_last_session()
            if session:
                return session
            # Fall through to create new if continue fails

        return self.create_session()

    def list_sessions(self, include_expired: bool = False) -> list[dict[str, Any]]:
        """List all sessions with metadata."""
        SESSION_DIR.mkdir(parents=True, exist_ok=True)

        sessions = []
        for session_file in SESSION_DIR.glob("sess_*.jsonl"):
            session = Session(session_file.stem)
            if include_expired or not session.is_expired():
                mtime = datetime.fromtimestamp(session_file.stat().st_mtime)
                sessions.append({
                    "session_id": session.session_id,
                    "last_modified": mtime.isoformat() + "Z",
                    "expired": session.is_expired(),
                    "project_focus": session.project_focus,
                })

        # Sort by modification time, newest first
        sessions.sort(key=lambda s: s["last_modified"], reverse=True)
        return sessions

    def cleanup_expired(self) -> int:
        """Remove expired session files. Returns count of deleted sessions."""
        SESSION_DIR.mkdir(parents=True, exist_ok=True)

        deleted = 0
        for session_file in SESSION_DIR.glob("sess_*.jsonl"):
            session = Session(session_file.stem)
            if session.is_expired():
                session_file.unlink()
                deleted += 1

        return deleted


# Global session manager instance
session_manager = SessionManager()
