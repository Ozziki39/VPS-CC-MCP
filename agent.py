#!/usr/bin/env python3
"""
VPS-CC-MCP Agent - Main CLI Entrypoint

A VPS-resident tool execution server for remote LLM chat clients.
All interactions are headless, non-interactive, and return structured JSON.

Usage:
    python3 agent.py --tool <tool_name> --params '<json>'
    python3 agent.py --continue --tool <tool_name> --params '<json>'
    python3 agent.py --resume <session_id> --tool <tool_name> --params '<json>'
    python3 agent.py --list-tools
"""

import argparse
import json
import sys
from typing import Any

# Add project root to path for imports
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config import get_approval_level
from context import ProjectContext
from schemas.responses import ToolResponse, ContextInfo, ErrorDetail
from session import session_manager, Session


def create_error_response(
    error_type: str,
    message: str,
    tool: str = "agent",
    session_id: str = "none",
    details: dict[str, Any] | None = None,
) -> str:
    """Create a structured error response."""
    response = ToolResponse(
        success=False,
        session_id=session_id,
        tool=tool,
        approval_level="none",
        result=None,
        context=ContextInfo(),
        error=ErrorDetail(
            type=error_type,
            message=message,
            tool=tool,
            details=details or {},
        ),
    )
    return response.to_json()


def list_tools_response() -> str:
    """Generate response listing all available tools."""
    # Import tools to trigger registration
    import tools
    tool_list = tools.list_tools()

    response = ToolResponse(
        success=True,
        session_id="none",
        tool="list_tools",
        approval_level="none",
        result={
            "count": len(tool_list),
            "tools": tool_list,
        },
        context=ContextInfo(),
    )
    return response.to_json()


def execute_tool(
    tool_name: str,
    params: dict[str, Any],
    session: Session,
    auto_approve: bool = False,
) -> str:
    """Execute a tool and return JSON response."""
    # Import tools to trigger registration
    import tools

    # Create context from session
    context = ProjectContext(session.project_focus)

    # Get tool
    tool_instance = tools.create_tool(tool_name, session, context)

    if tool_instance is None:
        return create_error_response(
            error_type="ToolNotFound",
            message=f"Unknown tool: {tool_name}",
            tool=tool_name,
            session_id=session.session_id,
            details={"available_tools": [t["name"] for t in tools.list_tools()]},
        )

    # Run tool
    response = tool_instance.run(params, auto_approve=auto_approve)

    # Update context in response
    response.context.project = context.focus_path_str
    response.context.session_id = session.session_id

    return response.to_json()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="VPS-CC-MCP Agent - Tool execution server for remote LLM clients",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available tools
  python3 agent.py --list-tools

  # Read a file
  python3 agent.py --tool file_read --params '{"path": "/etc/hostname"}'

  # Set project focus
  python3 agent.py --tool project_focus --params '{"path": "/root/myproject"}'

  # Continue last session
  python3 agent.py --continue --tool dir_tree --params '{}'

  # Resume specific session
  python3 agent.py --resume sess_abc123 --tool file_read --params '{"path": "main.py"}'

  # Execute with explicit approval
  python3 agent.py --auto-approve --tool bash_run --params '{"command": "ls -la"}'

  # Dry run (preview action)
  python3 agent.py --tool file_write --params '{"path": "test.txt", "content": "hello", "dry_run": true}'
        """,
    )

    # Tool execution
    parser.add_argument(
        "--tool",
        type=str,
        help="Tool name to execute",
    )
    parser.add_argument(
        "--params",
        type=str,
        default="{}",
        help="JSON parameters for the tool (default: {})",
    )

    # Session management
    parser.add_argument(
        "--continue",
        dest="continue_session",
        action="store_true",
        help="Continue the most recent session",
    )
    parser.add_argument(
        "--resume",
        type=str,
        metavar="SESSION_ID",
        help="Resume a specific session by ID",
    )

    # Approval
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Override approval checks for EXPLICIT level tools",
    )

    # Utility
    parser.add_argument(
        "--list-tools",
        action="store_true",
        help="List all available tools and exit",
    )
    parser.add_argument(
        "--list-sessions",
        action="store_true",
        help="List all sessions and exit",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    try:
        args = parse_args()

        # Handle --list-tools
        if args.list_tools:
            print(list_tools_response())
            return 0

        # Handle --list-sessions
        if args.list_sessions:
            sessions = session_manager.list_sessions(include_expired=False)
            response = ToolResponse(
                success=True,
                session_id="none",
                tool="list_sessions",
                approval_level="none",
                result={
                    "count": len(sessions),
                    "sessions": sessions,
                },
                context=ContextInfo(),
            )
            print(response.to_json())
            return 0

        # Require --tool for execution
        if not args.tool:
            print(create_error_response(
                error_type="MissingArgument",
                message="--tool is required. Use --list-tools to see available tools.",
            ))
            return 1

        # Parse params
        try:
            params = json.loads(args.params)
        except json.JSONDecodeError as e:
            print(create_error_response(
                error_type="InvalidJSON",
                message=f"Invalid JSON in --params: {e}",
                tool=args.tool,
            ))
            return 1

        # Get or create session
        session = session_manager.get_or_create_session(
            resume_id=args.resume,
            continue_last=args.continue_session,
        )

        # Execute tool
        result = execute_tool(
            tool_name=args.tool,
            params=params,
            session=session,
            auto_approve=args.auto_approve,
        )

        print(result)
        return 0

    except Exception as e:
        # Catch-all for unexpected errors
        print(create_error_response(
            error_type=type(e).__name__,
            message=str(e),
        ))
        return 1


if __name__ == "__main__":
    sys.exit(main())
