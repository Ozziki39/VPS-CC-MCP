"""
Response models for VPS-CC-MCP tools.

All tool responses follow a consistent JSON structure.
"""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Structured error information."""
    type: str = Field(..., description="Error type/class name")
    message: str = Field(..., description="Human-readable error message")
    tool: Optional[str] = Field(default=None, description="Tool that caused the error")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional error context")


class ContextInfo(BaseModel):
    """Current execution context."""
    project: Optional[str] = Field(default=None, description="Current project path")
    session_id: Optional[str] = Field(default=None, description="Active session ID")
    additional: dict[str, Any] = Field(default_factory=dict, description="Tool-specific context")


class ToolResponse(BaseModel):
    """Standard response format for all tools."""
    success: bool = Field(..., description="Whether the operation succeeded")
    session_id: str = Field(..., description="Session ID for this invocation")
    tool: str = Field(..., description="Name of the tool that was invoked")
    approval_level: str = Field(..., description="Approval level of the tool")
    dry_run: bool = Field(default=False, description="Whether this was a dry run")
    result: Optional[Any] = Field(default=None, description="Tool result data")
    context: ContextInfo = Field(default_factory=ContextInfo, description="Execution context")
    error: Optional[ErrorDetail] = Field(default=None, description="Error details if failed")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="ISO timestamp of response"
    )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return self.model_dump_json(indent=2, exclude_none=False)

    @classmethod
    def success_response(
        cls,
        session_id: str,
        tool: str,
        approval_level: str,
        result: Any,
        context: Optional[ContextInfo] = None,
        dry_run: bool = False,
    ) -> "ToolResponse":
        """Create a successful response."""
        return cls(
            success=True,
            session_id=session_id,
            tool=tool,
            approval_level=approval_level,
            dry_run=dry_run,
            result=result,
            context=context or ContextInfo(),
            error=None,
        )

    @classmethod
    def error_response(
        cls,
        session_id: str,
        tool: str,
        approval_level: str,
        error_type: str,
        error_message: str,
        details: Optional[dict[str, Any]] = None,
        context: Optional[ContextInfo] = None,
    ) -> "ToolResponse":
        """Create an error response."""
        return cls(
            success=False,
            session_id=session_id,
            tool=tool,
            approval_level=approval_level,
            result=None,
            context=context or ContextInfo(),
            error=ErrorDetail(
                type=error_type,
                message=error_message,
                tool=tool,
                details=details or {},
            ),
        )


# =============================================================================
# Tool-specific result models
# =============================================================================

class ProjectInfoResult(BaseModel):
    """Result for project_info tool."""
    path: str
    name: str
    exists: bool
    is_git: bool = False
    languages: list[str] = Field(default_factory=list)
    files_count: int = 0
    directories_count: int = 0
    readme_exists: bool = False
    config_files: list[str] = Field(default_factory=list)


class FileReadResult(BaseModel):
    """Result for file_read tool."""
    path: str
    content: str
    lines: int
    size_bytes: int
    encoding: str
    truncated: bool = False


class DirTreeResult(BaseModel):
    """Result for dir_tree tool."""
    path: str
    tree: dict[str, Any]  # Nested structure
    total_files: int
    total_dirs: int
    truncated: bool = False


class CodeExplainResult(BaseModel):
    """Result for code_explain tool."""
    path: str
    file_type: str
    content: str
    lines: int
    imports: list[str] = Field(default_factory=list)
    functions: list[str] = Field(default_factory=list)
    classes: list[str] = Field(default_factory=list)
    structure: dict[str, Any] = Field(default_factory=dict)


class ServiceStatusResult(BaseModel):
    """Result for service_status tool."""
    name: str
    manager: str
    status: str  # running, stopped, failed, unknown
    enabled: bool = False
    pid: Optional[int] = None
    uptime: Optional[str] = None
    memory: Optional[str] = None
    details: dict[str, Any] = Field(default_factory=dict)


class VpsStatusResult(BaseModel):
    """Result for vps_status tool."""
    hostname: str
    uptime: str
    load_average: list[float]
    memory: dict[str, Any]
    disk: dict[str, Any]
    cpu: dict[str, Any]
    processes: Optional[list[dict[str, Any]]] = None
    network: Optional[dict[str, Any]] = None


class BashRunResult(BaseModel):
    """Result for bash_run tool."""
    command: str
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False
    duration_seconds: float
