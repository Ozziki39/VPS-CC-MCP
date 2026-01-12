"""
Project context management for VPS-CC-MCP.

Manages the current project focus and provides path resolution utilities.
The context is stored in the session and persists across invocations.
"""

from pathlib import Path
from typing import Optional

from config import DEFAULT_PROJECTS_DIR


class ProjectContext:
    """
    Manages project focus and path resolution.

    The project focus is the "current working project" that tools operate on
    when paths are relative. It's similar to `cd` but for project context.
    """

    def __init__(self, focus_path: Optional[str] = None):
        self._focus_path: Optional[Path] = None
        if focus_path:
            self.set_focus(focus_path)

    @property
    def focus_path(self) -> Optional[Path]:
        """Get the current project focus path."""
        return self._focus_path

    @property
    def focus_path_str(self) -> Optional[str]:
        """Get the current project focus path as string."""
        return str(self._focus_path) if self._focus_path else None

    def set_focus(self, path: str) -> None:
        """
        Set the project focus to the given path.

        Args:
            path: Absolute path to the project directory.

        Raises:
            ValueError: If path is not absolute or doesn't exist.
        """
        p = Path(path)

        if not p.is_absolute():
            raise ValueError(f"Project path must be absolute: {path}")

        if not p.exists():
            raise ValueError(f"Project path does not exist: {path}")

        if not p.is_dir():
            raise ValueError(f"Project path is not a directory: {path}")

        self._focus_path = p

    def clear_focus(self) -> None:
        """Clear the current project focus."""
        self._focus_path = None

    def resolve_path(self, path: str) -> Path:
        """
        Resolve a path relative to the project focus.

        If the path is absolute, return it as-is.
        If the path is relative, resolve it against the project focus.
        If there's no project focus and path is relative, raise an error.

        Args:
            path: Path to resolve (absolute or relative).

        Returns:
            Resolved absolute Path.

        Raises:
            ValueError: If path is relative and no project focus is set.
        """
        p = Path(path)

        if p.is_absolute():
            return p

        if self._focus_path is None:
            raise ValueError(
                f"Cannot resolve relative path '{path}' without a project focus. "
                "Use project_focus to set the current project first."
            )

        return (self._focus_path / p).resolve()

    def is_within_focus(self, path: str) -> bool:
        """
        Check if a path is within the current project focus.

        Args:
            path: Path to check (absolute or relative).

        Returns:
            True if path is within the project focus, False otherwise.
        """
        if self._focus_path is None:
            return False

        try:
            resolved = self.resolve_path(path)
            # Check if resolved path is under the focus path
            return str(resolved).startswith(str(self._focus_path))
        except ValueError:
            return False

    def get_relative_path(self, path: str) -> str:
        """
        Get a path relative to the project focus.

        Args:
            path: Absolute path to convert.

        Returns:
            Relative path string if within focus, absolute path otherwise.
        """
        if self._focus_path is None:
            return path

        p = Path(path)
        if not p.is_absolute():
            return path

        try:
            return str(p.relative_to(self._focus_path))
        except ValueError:
            # Path is not under focus, return absolute
            return path


def discover_projects(base_path: Optional[str] = None) -> list[dict]:
    """
    Discover projects in a directory.

    A directory is considered a project if it contains any of:
    - .git directory
    - package.json
    - pyproject.toml / setup.py / requirements.txt
    - Cargo.toml
    - go.mod
    - Makefile

    Args:
        base_path: Directory to search (defaults to ~/projects).

    Returns:
        List of project info dicts with path, name, and detected type.
    """
    base = Path(base_path) if base_path else DEFAULT_PROJECTS_DIR

    if not base.exists():
        return []

    project_markers = [
        ".git",
        "package.json",
        "pyproject.toml",
        "setup.py",
        "requirements.txt",
        "Cargo.toml",
        "go.mod",
        "Makefile",
    ]

    projects = []

    # Check immediate subdirectories
    for entry in base.iterdir():
        if not entry.is_dir():
            continue

        if entry.name.startswith("."):
            continue

        # Check for project markers
        markers_found = []
        for marker in project_markers:
            if (entry / marker).exists():
                markers_found.append(marker)

        if markers_found:
            project_type = _detect_project_type(markers_found)
            projects.append({
                "path": str(entry),
                "name": entry.name,
                "type": project_type,
                "markers": markers_found,
            })

    # Sort by name
    projects.sort(key=lambda p: p["name"].lower())
    return projects


def _detect_project_type(markers: list[str]) -> str:
    """Detect project type from markers."""
    if "package.json" in markers:
        return "node"
    if "pyproject.toml" in markers or "setup.py" in markers or "requirements.txt" in markers:
        return "python"
    if "Cargo.toml" in markers:
        return "rust"
    if "go.mod" in markers:
        return "go"
    if ".git" in markers:
        return "git"
    return "unknown"


def get_project_info(path: str) -> dict:
    """
    Get detailed information about a project.

    Args:
        path: Path to the project directory.

    Returns:
        Dict with project metadata.
    """
    p = Path(path)

    if not p.exists():
        return {"path": path, "exists": False}

    if not p.is_dir():
        return {"path": path, "exists": True, "is_dir": False}

    info = {
        "path": str(p.resolve()),
        "name": p.name,
        "exists": True,
        "is_dir": True,
        "is_git": (p / ".git").exists(),
    }

    # Count files and directories
    files = 0
    dirs = 0
    for entry in p.rglob("*"):
        # Skip hidden files and common ignored directories
        parts = entry.relative_to(p).parts
        if any(part.startswith(".") or part in ("node_modules", "__pycache__", "venv", ".venv", "target", "dist", "build") for part in parts):
            continue

        if entry.is_file():
            files += 1
        elif entry.is_dir():
            dirs += 1

    info["files_count"] = files
    info["directories_count"] = dirs

    # Check for common config files
    config_files = []
    for config in [
        "package.json", "pyproject.toml", "setup.py", "requirements.txt",
        "Cargo.toml", "go.mod", "Makefile", "docker-compose.yml",
        "Dockerfile", ".env.example", "tsconfig.json",
    ]:
        if (p / config).exists():
            config_files.append(config)

    info["config_files"] = config_files

    # Check for README
    for readme in ["README.md", "README.rst", "README.txt", "README"]:
        if (p / readme).exists():
            info["readme"] = readme
            break

    # Detect languages
    languages = set()
    extensions_map = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".jsx": "JavaScript",
        ".tsx": "TypeScript",
        ".rs": "Rust",
        ".go": "Go",
        ".rb": "Ruby",
        ".java": "Java",
        ".c": "C",
        ".cpp": "C++",
        ".h": "C",
        ".hpp": "C++",
        ".sh": "Shell",
        ".sql": "SQL",
    }

    for entry in p.rglob("*"):
        if entry.is_file():
            ext = entry.suffix.lower()
            if ext in extensions_map:
                languages.add(extensions_map[ext])
        if len(languages) >= 5:  # Limit detection
            break

    info["languages"] = sorted(languages)

    return info
