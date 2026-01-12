# VPS-CC-MCP

VPS-resident development and operations agent, remotely controlled via external LLM chat clients (GPT and Claude) through an SSH-based MCP.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  External LLM Chat (Claude / GPT) - The "Brain"         │
│  - Orchestrates workflows                               │
│  - Decides which tools to call                          │
│  - Analyzes returned context                            │
│  - Asks user for confirmation when needed               │
└─────────────────────┬───────────────────────────────────┘
                      │ SSH MCP (transport + auth)
                      ▼
┌─────────────────────────────────────────────────────────┐
│  VPS-CC-MCP Agent - The "Hands"                         │
│  - Executes tools deterministically                     │
│  - Returns structured JSON                              │
│  - Manages sessions                                     │
│  - No LLM reasoning                                     │
└─────────────────────────────────────────────────────────┘
```

## Installation

```bash
# Clone or copy to VPS
cd /opt
git clone <repo> vps-cc-mcp
cd vps-cc-mcp

# Install dependencies
pip install -r requirements.txt

# Verify installation
python3 agent.py --list-tools
```

## Usage

### Basic Invocation

```bash
# List available tools
python3 agent.py --list-tools

# Execute a tool
python3 agent.py --tool <tool_name> --params '<json>'

# Example: Read a file
python3 agent.py --tool file_read --params '{"path": "/etc/hostname"}'
```

### Session Management

```bash
# First invocation - creates new session
python3 agent.py --tool project_focus --params '{"path": "/root/myproject"}'
# Returns: {"session_id": "sess_abc123", ...}

# Continue the most recent session
python3 agent.py --continue --tool dir_tree --params '{}'

# Resume a specific session
python3 agent.py --resume sess_abc123 --tool file_read --params '{"path": "main.py"}'

# List all sessions
python3 agent.py --list-sessions
```

### Via SSH MCP

```bash
# Remote invocation through SSH
ssh user@vps "python3 /opt/vps-cc-mcp/agent.py --tool file_read --params '{\"path\": \"/root/project/main.py\"}'"
```

## Available Tools

### Project Context
| Tool | Approval | Description |
|------|----------|-------------|
| `project_focus` | Auto | Set the current project context |
| `project_list` | Auto | List available projects |
| `project_info` | Auto | Get project information |

### Files & Code
| Tool | Approval | Description |
|------|----------|-------------|
| `file_read` | Auto | Read file contents |
| `file_write` | Confirm | Write content to a file |
| `dir_tree` | Auto | Get directory structure |

### Code Intelligence
| Tool | Approval | Description |
|------|----------|-------------|
| `code_explain` | Auto | Gather code context for explanation |
| `code_debug` | Auto | Gather debugging context |

### Services
| Tool | Approval | Description |
|------|----------|-------------|
| `service_list` | Auto | List services (systemd/docker/pm2) |
| `service_status` | Auto | Get service status |
| `service_start` | Confirm | Start a service |
| `service_stop` | Explicit | Stop a service |
| `service_restart` | Confirm | Restart a service |

### VPS
| Tool | Approval | Description |
|------|----------|-------------|
| `vps_status` | Auto | Get VPS system status |

### Execution
| Tool | Approval | Description |
|------|----------|-------------|
| `bash_run` | Explicit | Execute arbitrary bash commands |

## Approval Levels

| Level | Behavior | Flag Required |
|-------|----------|---------------|
| **Auto** | Execute immediately | None |
| **Confirm** | External LLM should confirm before invoking | None |
| **Explicit** | Requires `--auto-approve` flag | `--auto-approve` |

```bash
# Explicit approval example
python3 agent.py --auto-approve --tool bash_run --params '{"command": "ls -la"}'
```

## Dry Run

All tools support `dry_run` parameter to preview actions without executing:

```bash
python3 agent.py --tool file_write --params '{"path": "test.txt", "content": "hello", "dry_run": true}'
```

## Response Format

All tools return structured JSON:

```json
{
  "success": true,
  "session_id": "sess_abc123",
  "tool": "file_read",
  "approval_level": "auto",
  "dry_run": false,
  "result": {
    "path": "/etc/hostname",
    "content": "my-vps\n",
    "lines": 1,
    "size_bytes": 7
  },
  "context": {
    "project": "/root/myproject",
    "session_id": "sess_abc123"
  },
  "error": null,
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### Error Response

```json
{
  "success": false,
  "session_id": "sess_abc123",
  "tool": "file_read",
  "approval_level": "auto",
  "result": null,
  "context": {},
  "error": {
    "type": "FileNotFoundError",
    "message": "File not found: /nonexistent",
    "tool": "file_read",
    "details": {}
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

## Session Storage

Sessions are stored in `~/.vps-cc-mcp/sessions/` as append-only JSON Lines files:

```
~/.vps-cc-mcp/sessions/
├── sess_abc123.jsonl
├── sess_def456.jsonl
└── ...
```

Each line in a session file is a JSON entry recording tool calls and context changes.

## Configuration

Edit `config.py` to customize:

- `SESSION_DIR` - Session storage location
- `SESSION_TTL_HOURS` - Session expiry time
- `DEFAULT_PROJECTS_DIR` - Default projects directory
- `BASH_TIMEOUT_SECONDS` - Bash command timeout
- `MAX_FILE_SIZE_BYTES` - Maximum file read size

## Key Constraints

- **Not a daemon** - Invoked on demand via SSH MCP
- **Headless execution** - No TTY, no interactive prompts
- **Stateless between invocations** - State persisted in sessions only
- **Structured JSON I/O** - All input/output is JSON
- **No GitHub dependency** - Works directly on VPS filesystem
- **No paid API calls** - External LLM does all reasoning

## License

MIT
