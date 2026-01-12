"""
Bash execution tool for VPS-CC-MCP.

This is an escape hatch for arbitrary command execution.
Requires EXPLICIT approval (--auto-approve flag).
"""

import subprocess
import time
from typing import Any

from config import ApprovalLevel, BASH_MAX_OUTPUT_BYTES
from schemas.requests import BashRunParams
from tools.base import BaseTool, ToolMetadata, register_tool


@register_tool
class BashRunTool(BaseTool):
    """Execute arbitrary bash commands."""

    metadata = ToolMetadata(
        name="bash_run",
        approval_level=ApprovalLevel.EXPLICIT,
        description="Execute arbitrary bash commands. Escape hatch for operations not covered by other tools. Requires explicit approval.",
        params_model=BashRunParams,
    )

    def execute(self, params: BashRunParams) -> dict[str, Any]:
        """Execute bash command."""
        # Determine working directory
        if params.cwd:
            cwd = params.cwd
        elif self.context.focus_path:
            cwd = str(self.context.focus_path)
        else:
            cwd = None

        # Execute command
        start_time = time.time()
        timed_out = False

        try:
            result = subprocess.run(
                params.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=params.timeout,
                cwd=cwd,
                env=None,  # Use current environment
            )
            exit_code = result.returncode
            stdout = result.stdout
            stderr = result.stderr

        except subprocess.TimeoutExpired as e:
            timed_out = True
            exit_code = -1
            stdout = e.stdout.decode("utf-8", errors="replace") if e.stdout else ""
            stderr = e.stderr.decode("utf-8", errors="replace") if e.stderr else ""
            stderr += f"\nCommand timed out after {params.timeout} seconds"

        except Exception as e:
            exit_code = -1
            stdout = ""
            stderr = str(e)

        duration = time.time() - start_time

        # Truncate output if too large
        stdout_truncated = False
        stderr_truncated = False

        if len(stdout) > BASH_MAX_OUTPUT_BYTES:
            stdout = stdout[:BASH_MAX_OUTPUT_BYTES] + "\n... (output truncated)"
            stdout_truncated = True

        if len(stderr) > BASH_MAX_OUTPUT_BYTES:
            stderr = stderr[:BASH_MAX_OUTPUT_BYTES] + "\n... (output truncated)"
            stderr_truncated = True

        return {
            "command": params.command,
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr,
            "timed_out": timed_out,
            "duration_seconds": round(duration, 3),
            "cwd": cwd,
            "stdout_truncated": stdout_truncated,
            "stderr_truncated": stderr_truncated,
        }
