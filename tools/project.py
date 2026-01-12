"""
Project context tools for VPS-CC-MCP.

Tools:
- project_focus: Set the current project context
- project_list: List available projects
- project_info: Get information about a project
"""

from typing import Any

from config import ApprovalLevel
from context import discover_projects, get_project_info
from schemas.requests import (
    ProjectFocusParams,
    ProjectListParams,
    ProjectInfoParams,
)
from tools.base import BaseTool, ToolMetadata, register_tool


@register_tool
class ProjectFocusTool(BaseTool):
    """Set the current project focus for subsequent tool calls."""

    metadata = ToolMetadata(
        name="project_focus",
        approval_level=ApprovalLevel.AUTO,
        description="Set the current project context. Subsequent relative paths will resolve against this project.",
        params_model=ProjectFocusParams,
    )

    def execute(self, params: ProjectFocusParams) -> dict[str, Any]:
        """Set project focus and update session context."""
        # Set the focus in context
        self.context.set_focus(params.path)

        # Update session
        self.session.log_context_change(params.path)

        # Get project info
        info = get_project_info(params.path)

        return {
            "focused": True,
            "path": params.path,
            "project": info,
        }


@register_tool
class ProjectListTool(BaseTool):
    """List available projects in a directory."""

    metadata = ToolMetadata(
        name="project_list",
        approval_level=ApprovalLevel.AUTO,
        description="List available projects. Discovers projects by looking for common project markers (git, package.json, etc.).",
        params_model=ProjectListParams,
    )

    def execute(self, params: ProjectListParams) -> dict[str, Any]:
        """Discover and list projects."""
        projects = discover_projects(params.base_path)

        return {
            "base_path": params.base_path or "~/projects",
            "count": len(projects),
            "projects": projects,
        }


@register_tool
class ProjectInfoTool(BaseTool):
    """Get detailed information about a project."""

    metadata = ToolMetadata(
        name="project_info",
        approval_level=ApprovalLevel.AUTO,
        description="Get detailed information about a project including file counts, languages, and config files.",
        params_model=ProjectInfoParams,
    )

    def execute(self, params: ProjectInfoParams) -> dict[str, Any]:
        """Get project information."""
        # Use current focus if path not specified
        if params.path:
            path = params.path
        elif self.context.focus_path:
            path = str(self.context.focus_path)
        else:
            raise ValueError(
                "No project path specified and no project focus set. "
                "Use project_focus first or provide a path."
            )

        info = get_project_info(path)
        return info
