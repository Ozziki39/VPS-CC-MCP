"""
VPS-CC-MCP Configuration

Defines approval levels, paths, session settings, and tool metadata requirements.
"""

from enum import Enum
from pathlib import Path
from typing import Final


class ApprovalLevel(str, Enum):
    """Tool approval levels for the tiered permission system."""
    AUTO = "auto"           # Execute immediately, no confirmation needed
    CONFIRM = "confirm"     # External LLM should confirm before invoking
    EXPLICIT = "explicit"   # Requires explicit user approval + --auto-approve flag


# Tool approval level mappings
TOOL_APPROVAL_LEVELS: Final[dict[str, ApprovalLevel]] = {
    # Auto - safe, read-only operations
    "project_list": ApprovalLevel.AUTO,
    "project_info": ApprovalLevel.AUTO,
    "file_read": ApprovalLevel.AUTO,
    "dir_tree": ApprovalLevel.AUTO,
    "code_explain": ApprovalLevel.AUTO,
    "code_debug": ApprovalLevel.AUTO,
    "service_status": ApprovalLevel.AUTO,
    "service_list": ApprovalLevel.AUTO,
    "vps_status": ApprovalLevel.AUTO,

    # Confirm - modifying operations, LLM should confirm first
    "file_write": ApprovalLevel.CONFIRM,
    "service_start": ApprovalLevel.CONFIRM,
    "service_restart": ApprovalLevel.CONFIRM,
    "project_focus": ApprovalLevel.AUTO,  # Context switch is safe

    # Explicit - dangerous operations, require --auto-approve
    "bash_run": ApprovalLevel.EXPLICIT,
    "service_stop": ApprovalLevel.EXPLICIT,
}


# Session configuration
SESSION_DIR: Final[Path] = Path.home() / ".vps-cc-mcp" / "sessions"
SESSION_TTL_HOURS: Final[int] = 24  # Sessions expire after 24 hours of inactivity
SESSION_ID_PREFIX: Final[str] = "sess_"
SESSION_ID_LENGTH: Final[int] = 8  # Random suffix length


# Project configuration
DEFAULT_PROJECTS_DIR: Final[Path] = Path.home() / "projects"
MAX_FILE_SIZE_BYTES: Final[int] = 10 * 1024 * 1024  # 10MB max file read
MAX_DIR_TREE_DEPTH: Final[int] = 10
MAX_DIR_TREE_FILES: Final[int] = 1000


# Bash execution limits
BASH_TIMEOUT_SECONDS: Final[int] = 60
BASH_MAX_OUTPUT_BYTES: Final[int] = 1 * 1024 * 1024  # 1MB max output


# Service management
SUPPORTED_SERVICE_MANAGERS: Final[list[str]] = ["systemd", "docker", "pm2"]


def get_approval_level(tool_name: str) -> ApprovalLevel:
    """Get the approval level for a tool, defaulting to EXPLICIT if unknown."""
    return TOOL_APPROVAL_LEVELS.get(tool_name, ApprovalLevel.EXPLICIT)
