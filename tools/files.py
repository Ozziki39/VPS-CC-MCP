"""
File operation tools for VPS-CC-MCP.

Tools:
- file_read: Read file contents
- file_write: Write content to a file
- dir_tree: Get directory structure
"""

import fnmatch
from pathlib import Path
from typing import Any

from config import ApprovalLevel, MAX_FILE_SIZE_BYTES, MAX_DIR_TREE_DEPTH, MAX_DIR_TREE_FILES
from schemas.requests import FileReadParams, FileWriteParams, DirTreeParams
from tools.base import BaseTool, ToolMetadata, register_tool


@register_tool
class FileReadTool(BaseTool):
    """Read the contents of a file."""

    metadata = ToolMetadata(
        name="file_read",
        approval_level=ApprovalLevel.AUTO,
        description="Read the contents of a file. Supports line range selection and different encodings.",
        params_model=FileReadParams,
    )

    def execute(self, params: FileReadParams) -> dict[str, Any]:
        """Read file contents."""
        # Resolve path relative to project focus
        file_path = self.context.resolve_path(params.path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise ValueError(f"Not a file: {file_path}")

        # Check file size
        size = file_path.stat().st_size
        if size > MAX_FILE_SIZE_BYTES:
            raise ValueError(
                f"File too large ({size} bytes). Maximum is {MAX_FILE_SIZE_BYTES} bytes."
            )

        # Read file
        content = file_path.read_text(encoding=params.encoding)
        lines = content.splitlines(keepends=True)
        total_lines = len(lines)

        # Apply line range if specified
        truncated = False
        if params.start_line or params.end_line:
            start = (params.start_line or 1) - 1  # Convert to 0-indexed
            end = params.end_line or total_lines
            lines = lines[start:end]
            content = "".join(lines)
            truncated = True

        return {
            "path": str(file_path),
            "content": content,
            "lines": len(lines),
            "total_lines": total_lines,
            "size_bytes": size,
            "encoding": params.encoding,
            "truncated": truncated,
        }


@register_tool
class FileWriteTool(BaseTool):
    """Write content to a file."""

    metadata = ToolMetadata(
        name="file_write",
        approval_level=ApprovalLevel.CONFIRM,
        description="Write content to a file. Creates parent directories if needed.",
        params_model=FileWriteParams,
    )

    def execute(self, params: FileWriteParams) -> dict[str, Any]:
        """Write content to file."""
        # Resolve path relative to project focus
        file_path = self.context.resolve_path(params.path)

        # Create parent directories if needed
        if params.create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)

        # Check if file exists (for reporting)
        existed = file_path.exists()
        old_size = file_path.stat().st_size if existed else 0

        # Write content
        file_path.write_text(params.content, encoding=params.encoding)

        new_size = file_path.stat().st_size
        lines = len(params.content.splitlines())

        return {
            "path": str(file_path),
            "created": not existed,
            "modified": existed,
            "old_size_bytes": old_size,
            "new_size_bytes": new_size,
            "lines": lines,
            "encoding": params.encoding,
        }


@register_tool
class DirTreeTool(BaseTool):
    """Get directory structure as a tree."""

    metadata = ToolMetadata(
        name="dir_tree",
        approval_level=ApprovalLevel.AUTO,
        description="Get directory structure as a tree. Supports depth limiting and pattern filtering.",
        params_model=DirTreeParams,
    )

    def execute(self, params: DirTreeParams) -> dict[str, Any]:
        """Build directory tree."""
        # Use project focus if path not specified
        if params.path:
            dir_path = self.context.resolve_path(params.path)
        elif self.context.focus_path:
            dir_path = self.context.focus_path
        else:
            raise ValueError(
                "No path specified and no project focus set. "
                "Use project_focus first or provide a path."
            )

        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")

        if not dir_path.is_dir():
            raise ValueError(f"Not a directory: {dir_path}")

        # Build tree
        tree, stats = self._build_tree(
            dir_path,
            max_depth=min(params.max_depth, MAX_DIR_TREE_DEPTH),
            include_hidden=params.include_hidden,
            pattern=params.pattern,
        )

        return {
            "path": str(dir_path),
            "tree": tree,
            "total_files": stats["files"],
            "total_dirs": stats["dirs"],
            "truncated": stats["truncated"],
        }

    def _build_tree(
        self,
        path: Path,
        max_depth: int,
        include_hidden: bool,
        pattern: str | None,
        current_depth: int = 0,
        stats: dict | None = None,
    ) -> tuple[dict[str, Any], dict[str, int]]:
        """Recursively build directory tree."""
        if stats is None:
            stats = {"files": 0, "dirs": 0, "truncated": False}

        result: dict[str, Any] = {
            "name": path.name or str(path),
            "type": "directory",
            "children": [],
        }

        if current_depth >= max_depth:
            result["truncated"] = True
            return result, stats

        if stats["files"] + stats["dirs"] >= MAX_DIR_TREE_FILES:
            stats["truncated"] = True
            result["truncated"] = True
            return result, stats

        try:
            entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            result["error"] = "Permission denied"
            return result, stats

        for entry in entries:
            # Skip hidden files unless requested
            if not include_hidden and entry.name.startswith("."):
                continue

            # Apply pattern filter
            if pattern and entry.is_file():
                if not fnmatch.fnmatch(entry.name, pattern):
                    continue

            # Skip common ignored directories
            if entry.is_dir() and entry.name in (
                "node_modules", "__pycache__", ".git", "venv", ".venv",
                "target", "dist", "build", ".next", ".cache"
            ):
                continue

            if stats["files"] + stats["dirs"] >= MAX_DIR_TREE_FILES:
                stats["truncated"] = True
                result["truncated"] = True
                break

            if entry.is_file():
                stats["files"] += 1
                child = {
                    "name": entry.name,
                    "type": "file",
                    "size": entry.stat().st_size,
                }
                result["children"].append(child)
            elif entry.is_dir():
                stats["dirs"] += 1
                child, _ = self._build_tree(
                    entry,
                    max_depth=max_depth,
                    include_hidden=include_hidden,
                    pattern=pattern,
                    current_depth=current_depth + 1,
                    stats=stats,
                )
                result["children"].append(child)

        return result, stats
