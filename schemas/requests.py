"""
Request/input validation models for VPS-CC-MCP tools.

All tool parameters inherit from BaseToolParams and define their specific fields.
"""

from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class BaseToolParams(BaseModel):
    """Base class for all tool parameters."""
    dry_run: bool = Field(default=False, description="Preview action without executing")

    class Config:
        extra = "forbid"  # Reject unknown fields


# =============================================================================
# Project Tools
# =============================================================================

class ProjectFocusParams(BaseToolParams):
    """Parameters for project_focus tool."""
    path: str = Field(..., description="Absolute path to project directory")

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        if not v.startswith("/"):
            raise ValueError("Path must be absolute (start with /)")
        return v


class ProjectListParams(BaseToolParams):
    """Parameters for project_list tool."""
    base_path: Optional[str] = Field(
        default=None,
        description="Base directory to search for projects (defaults to ~/projects)"
    )


class ProjectInfoParams(BaseToolParams):
    """Parameters for project_info tool."""
    path: Optional[str] = Field(
        default=None,
        description="Project path (uses current focus if not specified)"
    )


# =============================================================================
# File Tools
# =============================================================================

class FileReadParams(BaseToolParams):
    """Parameters for file_read tool."""
    path: str = Field(..., description="Path to file (relative to project or absolute)")
    start_line: Optional[int] = Field(default=None, ge=1, description="Start line (1-indexed)")
    end_line: Optional[int] = Field(default=None, ge=1, description="End line (1-indexed)")
    encoding: str = Field(default="utf-8", description="File encoding")


class FileWriteParams(BaseToolParams):
    """Parameters for file_write tool."""
    path: str = Field(..., description="Path to file (relative to project or absolute)")
    content: str = Field(..., description="Content to write")
    create_dirs: bool = Field(default=True, description="Create parent directories if needed")
    encoding: str = Field(default="utf-8", description="File encoding")


class DirTreeParams(BaseToolParams):
    """Parameters for dir_tree tool."""
    path: Optional[str] = Field(
        default=None,
        description="Directory path (uses current project if not specified)"
    )
    max_depth: int = Field(default=3, ge=1, le=10, description="Maximum traversal depth")
    include_hidden: bool = Field(default=False, description="Include hidden files/dirs")
    pattern: Optional[str] = Field(default=None, description="Glob pattern to filter files")


# =============================================================================
# Code Tools
# =============================================================================

class CodeExplainParams(BaseToolParams):
    """Parameters for code_explain tool."""
    path: str = Field(..., description="Path to file to explain")
    question: Optional[str] = Field(
        default=None,
        description="Specific question about the code"
    )


class CodeDebugParams(BaseToolParams):
    """Parameters for code_debug tool."""
    path: Optional[str] = Field(
        default=None,
        description="Path to file with error (optional)"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message or traceback"
    )
    context: Optional[str] = Field(
        default=None,
        description="Additional context about the issue"
    )


# =============================================================================
# Service Tools
# =============================================================================

class ServiceListParams(BaseToolParams):
    """Parameters for service_list tool."""
    manager: Optional[str] = Field(
        default=None,
        description="Service manager (systemd, docker, pm2). Lists all if not specified."
    )


class ServiceStatusParams(BaseToolParams):
    """Parameters for service_status tool."""
    name: str = Field(..., description="Service name")
    manager: Optional[str] = Field(
        default=None,
        description="Service manager (auto-detected if not specified)"
    )


class ServiceControlParams(BaseToolParams):
    """Parameters for service_start, service_stop, service_restart tools."""
    name: str = Field(..., description="Service name")
    manager: Optional[str] = Field(
        default=None,
        description="Service manager (auto-detected if not specified)"
    )


# =============================================================================
# VPS Tools
# =============================================================================

class VpsStatusParams(BaseToolParams):
    """Parameters for vps_status tool."""
    include_processes: bool = Field(default=False, description="Include top processes")
    include_network: bool = Field(default=False, description="Include network stats")


# =============================================================================
# Bash Tools
# =============================================================================

class BashRunParams(BaseToolParams):
    """Parameters for bash_run tool."""
    command: str = Field(..., description="Shell command to execute")
    timeout: int = Field(default=60, ge=1, le=300, description="Timeout in seconds")
    cwd: Optional[str] = Field(
        default=None,
        description="Working directory (uses project focus if not specified)"
    )
