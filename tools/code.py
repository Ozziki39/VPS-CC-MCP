"""
Code intelligence tools for VPS-CC-MCP.

These tools gather context for the external LLM to analyze.
They do NOT call any LLM API - the external chat client does the analysis.

Tools:
- code_explain: Gather code context for explanation
- code_debug: Gather debugging context
"""

import ast
import re
from pathlib import Path
from typing import Any

from config import ApprovalLevel, MAX_FILE_SIZE_BYTES
from schemas.requests import CodeExplainParams, CodeDebugParams
from tools.base import BaseTool, ToolMetadata, register_tool


# File type mappings
FILE_TYPE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".rs": "rust",
    ".go": "go",
    ".rb": "ruby",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
    ".sql": "sql",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".md": "markdown",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".xml": "xml",
}


def detect_file_type(path: Path) -> str:
    """Detect file type from extension."""
    return FILE_TYPE_MAP.get(path.suffix.lower(), "text")


def extract_python_structure(content: str) -> dict[str, Any]:
    """Extract structure from Python code using AST."""
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return {"parse_error": True}

    imports = []
    functions = []
    classes = []
    global_vars = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append(f"{module}.{alias.name}" if module else alias.name)
        elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            # Only top-level functions
            if any(isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                   for parent in ast.walk(tree) if hasattr(parent, 'body') and node in getattr(parent, 'body', [])):
                continue
            func_info = {
                "name": node.name,
                "args": [arg.arg for arg in node.args.args],
                "decorators": [ast.unparse(d) if hasattr(ast, 'unparse') else str(d) for d in node.decorator_list],
                "is_async": isinstance(node, ast.AsyncFunctionDef),
                "line": node.lineno,
            }
            functions.append(func_info)
        elif isinstance(node, ast.ClassDef):
            class_info = {
                "name": node.name,
                "bases": [ast.unparse(b) if hasattr(ast, 'unparse') else str(b) for b in node.bases],
                "methods": [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))],
                "line": node.lineno,
            }
            classes.append(class_info)

    # Get top-level assignments
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    global_vars.append(target.id)

    return {
        "imports": imports,
        "functions": functions,
        "classes": classes,
        "global_vars": global_vars,
    }


def extract_js_ts_structure(content: str) -> dict[str, Any]:
    """Extract structure from JavaScript/TypeScript using regex."""
    imports = []
    functions = []
    classes = []

    # Import patterns
    import_patterns = [
        r"import\s+(?:{[^}]+}|\*\s+as\s+\w+|\w+)\s+from\s+['\"]([^'\"]+)['\"]",
        r"const\s+\w+\s*=\s*require\(['\"]([^'\"]+)['\"]\)",
    ]
    for pattern in import_patterns:
        imports.extend(re.findall(pattern, content))

    # Function patterns
    func_patterns = [
        r"(?:export\s+)?(?:async\s+)?function\s+(\w+)",
        r"(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>",
        r"(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?function",
    ]
    for pattern in func_patterns:
        functions.extend(re.findall(pattern, content))

    # Class pattern
    class_pattern = r"(?:export\s+)?class\s+(\w+)"
    classes.extend(re.findall(class_pattern, content))

    return {
        "imports": list(set(imports)),
        "functions": list(set(functions)),
        "classes": list(set(classes)),
    }


def extract_structure(content: str, file_type: str) -> dict[str, Any]:
    """Extract code structure based on file type."""
    if file_type == "python":
        return extract_python_structure(content)
    elif file_type in ("javascript", "typescript"):
        return extract_js_ts_structure(content)
    else:
        # Generic: just count lines and look for common patterns
        lines = content.splitlines()
        return {
            "lines": len(lines),
            "non_empty_lines": len([l for l in lines if l.strip()]),
        }


@register_tool
class CodeExplainTool(BaseTool):
    """Gather code context for the external LLM to explain."""

    metadata = ToolMetadata(
        name="code_explain",
        approval_level=ApprovalLevel.AUTO,
        description="Gather code context including file content, structure, imports, and functions. Returns data for external LLM analysis.",
        params_model=CodeExplainParams,
    )

    def execute(self, params: CodeExplainParams) -> dict[str, Any]:
        """Gather code context."""
        file_path = self.context.resolve_path(params.path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise ValueError(f"Not a file: {file_path}")

        # Check file size
        size = file_path.stat().st_size
        if size > MAX_FILE_SIZE_BYTES:
            raise ValueError(f"File too large ({size} bytes)")

        # Read content
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = file_path.read_text(encoding="latin-1")

        # Detect file type
        file_type = detect_file_type(file_path)

        # Extract structure
        structure = extract_structure(content, file_type)

        result = {
            "path": str(file_path),
            "file_type": file_type,
            "content": content,
            "lines": len(content.splitlines()),
            "size_bytes": size,
            "structure": structure,
        }

        # Add question if provided
        if params.question:
            result["question"] = params.question

        return result


@register_tool
class CodeDebugTool(BaseTool):
    """Gather debugging context for the external LLM to analyze."""

    metadata = ToolMetadata(
        name="code_debug",
        approval_level=ApprovalLevel.AUTO,
        description="Gather debugging context including error messages, relevant file content, and surrounding context.",
        params_model=CodeDebugParams,
    )

    def execute(self, params: CodeDebugParams) -> dict[str, Any]:
        """Gather debugging context."""
        result: dict[str, Any] = {}

        # Add error info
        if params.error:
            result["error"] = params.error

            # Try to parse Python traceback for file/line info
            traceback_files = self._parse_traceback(params.error)
            if traceback_files:
                result["traceback_files"] = traceback_files

        # Add file content if specified
        if params.path:
            file_path = self.context.resolve_path(params.path)

            if file_path.exists() and file_path.is_file():
                try:
                    content = file_path.read_text(encoding="utf-8")
                    file_type = detect_file_type(file_path)

                    result["file"] = {
                        "path": str(file_path),
                        "file_type": file_type,
                        "content": content,
                        "lines": len(content.splitlines()),
                        "structure": extract_structure(content, file_type),
                    }
                except Exception as e:
                    result["file_error"] = str(e)

        # Add additional context
        if params.context:
            result["additional_context"] = params.context

        # Add project context if available
        if self.context.focus_path:
            result["project"] = str(self.context.focus_path)

        return result

    def _parse_traceback(self, error: str) -> list[dict[str, Any]]:
        """Parse Python traceback to extract file and line information."""
        files = []

        # Pattern for Python traceback lines
        pattern = r'File "([^"]+)", line (\d+)'

        for match in re.finditer(pattern, error):
            file_path = match.group(1)
            line_num = int(match.group(2))

            # Skip standard library and site-packages
            if "/lib/" in file_path or "site-packages" in file_path:
                continue

            file_info: dict[str, Any] = {
                "path": file_path,
                "line": line_num,
            }

            # Try to read a snippet around the error line
            try:
                path = Path(file_path)
                if path.exists():
                    content = path.read_text(encoding="utf-8")
                    lines = content.splitlines()

                    # Get context around error line (5 lines before and after)
                    start = max(0, line_num - 6)
                    end = min(len(lines), line_num + 5)

                    file_info["snippet"] = {
                        "start_line": start + 1,
                        "end_line": end,
                        "lines": lines[start:end],
                        "error_line": line_num,
                    }
            except Exception:
                pass

            files.append(file_info)

        return files
