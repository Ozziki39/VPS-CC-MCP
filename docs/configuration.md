# Configuration

Customize VPS-CC-MCP behavior through `config.py`.

## Configuration File

All configuration is in `/opt/vps-cc-mcp/config.py`:

```python
from enum import Enum
from pathlib import Path
from typing import Final


class ApprovalLevel(str, Enum):
    AUTO = "auto"
    CONFIRM = "confirm"
    EXPLICIT = "explicit"


# Session configuration
SESSION_DIR: Final[Path] = Path.home() / ".vps-cc-mcp" / "sessions"
SESSION_TTL_HOURS: Final[int] = 24
SESSION_ID_PREFIX: Final[str] = "sess_"
SESSION_ID_LENGTH: Final[int] = 8

# Project configuration
DEFAULT_PROJECTS_DIR: Final[Path] = Path.home() / "projects"
MAX_FILE_SIZE_BYTES: Final[int] = 10 * 1024 * 1024  # 10MB
MAX_DIR_TREE_DEPTH: Final[int] = 10
MAX_DIR_TREE_FILES: Final[int] = 1000

# Bash execution limits
BASH_TIMEOUT_SECONDS: Final[int] = 60
BASH_MAX_OUTPUT_BYTES: Final[int] = 1 * 1024 * 1024  # 1MB

# Service management
SUPPORTED_SERVICE_MANAGERS: Final[list[str]] = ["systemd", "docker", "pm2"]

# Tool approval levels
TOOL_APPROVAL_LEVELS: Final[dict[str, ApprovalLevel]] = {
    "project_list": ApprovalLevel.AUTO,
    "project_info": ApprovalLevel.AUTO,
    "project_focus": ApprovalLevel.AUTO,
    "file_read": ApprovalLevel.AUTO,
    "file_write": ApprovalLevel.CONFIRM,
    "dir_tree": ApprovalLevel.AUTO,
    "code_explain": ApprovalLevel.AUTO,
    "code_debug": ApprovalLevel.AUTO,
    "service_list": ApprovalLevel.AUTO,
    "service_status": ApprovalLevel.AUTO,
    "service_start": ApprovalLevel.CONFIRM,
    "service_stop": ApprovalLevel.EXPLICIT,
    "service_restart": ApprovalLevel.CONFIRM,
    "vps_status": ApprovalLevel.AUTO,
    "bash_run": ApprovalLevel.EXPLICIT,
}
```

## Configuration Options

### Session Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `SESSION_DIR` | `~/.vps-cc-mcp/sessions` | Where session files are stored |
| `SESSION_TTL_HOURS` | `24` | Hours until session expires |
| `SESSION_ID_PREFIX` | `"sess_"` | Prefix for session IDs |
| `SESSION_ID_LENGTH` | `8` | Random suffix length |

**Example: Change session location**
```python
SESSION_DIR = Path("/var/lib/vps-cc-mcp/sessions")
```

**Example: Longer session TTL**
```python
SESSION_TTL_HOURS = 168  # 1 week
```

### Project Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `DEFAULT_PROJECTS_DIR` | `~/projects` | Default for project_list |
| `MAX_FILE_SIZE_BYTES` | `10MB` | Maximum file read size |
| `MAX_DIR_TREE_DEPTH` | `10` | Maximum dir_tree depth |
| `MAX_DIR_TREE_FILES` | `1000` | Maximum files in dir_tree |

**Example: Different projects directory**
```python
DEFAULT_PROJECTS_DIR = Path("/srv/projects")
```

**Example: Larger file limit**
```python
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50MB
```

### Bash Execution Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `BASH_TIMEOUT_SECONDS` | `60` | Default command timeout |
| `BASH_MAX_OUTPUT_BYTES` | `1MB` | Maximum stdout/stderr size |

**Example: Longer timeout for slow commands**
```python
BASH_TIMEOUT_SECONDS = 300  # 5 minutes
```

### Approval Levels

Modify which tools require which approval level:

**Example: Make file_write require explicit approval**
```python
TOOL_APPROVAL_LEVELS = {
    ...
    "file_write": ApprovalLevel.EXPLICIT,  # Changed from CONFIRM
    ...
}
```

**Example: Allow service_stop without explicit approval**
```python
TOOL_APPROVAL_LEVELS = {
    ...
    "service_stop": ApprovalLevel.CONFIRM,  # Changed from EXPLICIT
    ...
}
```

⚠️ **Warning:** Lowering approval levels reduces safety.

## Environment Variables

VPS-CC-MCP respects these environment variables:

| Variable | Usage |
|----------|-------|
| `HOME` | Session storage location |
| `PATH` | For finding service managers |

## Runtime Configuration

Some settings can be overridden at runtime:

### Per-Tool Timeout

```bash
python3 agent.py --auto-approve --tool bash_run --params '{"command": "long_task", "timeout": 300}'
```

### Per-Call Dry Run

```bash
python3 agent.py --tool file_write --params '{"...", "dry_run": true}'
```

## Directory Permissions

Ensure proper permissions:

```bash
# Session directory
mkdir -p ~/.vps-cc-mcp/sessions
chmod 700 ~/.vps-cc-mcp
chmod 700 ~/.vps-cc-mcp/sessions

# Installation directory (if not world-readable)
chmod 755 /opt/vps-cc-mcp
```

## Logging

VPS-CC-MCP logs through session files, not traditional logs:

```bash
# View recent activity
tail -f ~/.vps-cc-mcp/sessions/sess_*.jsonl | jq

# Search for errors
grep '"error"' ~/.vps-cc-mcp/sessions/*.jsonl | jq
```

## Customization Examples

### High-Security Setup

```python
# config.py
SESSION_TTL_HOURS = 1  # Short sessions
MAX_FILE_SIZE_BYTES = 1 * 1024 * 1024  # 1MB limit
BASH_TIMEOUT_SECONDS = 30  # Short timeout

# All modifications require explicit approval
TOOL_APPROVAL_LEVELS = {
    ...
    "file_write": ApprovalLevel.EXPLICIT,
    "service_start": ApprovalLevel.EXPLICIT,
    "service_restart": ApprovalLevel.EXPLICIT,
    ...
}
```

### Development Setup

```python
# config.py
SESSION_TTL_HOURS = 168  # 1 week sessions
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100MB
BASH_TIMEOUT_SECONDS = 600  # 10 minutes

# More permissive for development
TOOL_APPROVAL_LEVELS = {
    ...
    "bash_run": ApprovalLevel.CONFIRM,  # Just confirm, not explicit
    ...
}
```

### Multi-User Setup

```python
# config.py
# Each user gets their own session directory
import os
user = os.environ.get("USER", "default")
SESSION_DIR = Path(f"/var/lib/vps-cc-mcp/sessions/{user}")
```
