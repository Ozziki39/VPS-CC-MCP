# Session Management

Sessions persist context across multiple invocations, enabling multi-turn workflows.

## Overview

Each invocation of VPS-CC-MCP can be part of a session. Sessions store:

- **Current project focus** - The active project context
- **Tool call history** - Record of all tool invocations
- **Context changes** - Project focus switches

## Session Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                        NEW SESSION                               │
│  python3 agent.py --tool project_focus --params '...'           │
│                                                                  │
│  Returns: session_id: "sess_abc123"                             │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      CONTINUE SESSION                            │
│  python3 agent.py --continue --tool dir_tree --params '{}'      │
│                                                                  │
│  Uses: Most recent session (sess_abc123)                        │
│  Inherits: Project focus from previous call                     │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       RESUME SESSION                             │
│  python3 agent.py --resume sess_abc123 --tool file_read ...     │
│                                                                  │
│  Uses: Specific session by ID                                   │
│  Inherits: Full context from that session                       │
└─────────────────────────────────────────────────────────────────┘
```

## CLI Flags

### `--continue`

Continue the most recent session.

```bash
# First call - creates session
python3 agent.py --tool project_focus --params '{"path": "/root/myproject"}'
# Returns: session_id: "sess_abc123"

# Second call - continues same session
python3 agent.py --continue --tool dir_tree --params '{}'
# Uses project focus from first call
```

### `--resume <session_id>`

Resume a specific session by ID.

```bash
# Get session ID from previous response
# session_id: "sess_abc123"

# Resume later (hours/days later)
python3 agent.py --resume sess_abc123 --tool file_read --params '{"path": "main.py"}'
```

### `--list-sessions`

List all active sessions.

```bash
python3 agent.py --list-sessions
```

```json
{
  "success": true,
  "result": {
    "count": 3,
    "sessions": [
      {
        "session_id": "sess_abc123",
        "last_modified": "2024-01-15T10:30:00.000Z",
        "expired": false,
        "project_focus": "/root/myproject"
      },
      {
        "session_id": "sess_def456",
        "last_modified": "2024-01-14T15:20:00.000Z",
        "expired": false,
        "project_focus": "/root/api-server"
      }
    ]
  }
}
```

## Session Storage

Sessions are stored as append-only JSON Lines files in `~/.vps-cc-mcp/sessions/`.

### Storage Location

```
~/.vps-cc-mcp/
└── sessions/
    ├── sess_abc123.jsonl
    ├── sess_def456.jsonl
    └── ...
```

### File Format

Each session file contains one JSON object per line (JSON Lines format):

```jsonl
{"timestamp": "2024-01-15T10:30:00.000Z", "type": "session_start"}
{"timestamp": "2024-01-15T10:30:01.000Z", "type": "tool_call", "tool": "project_focus", "params": {"path": "/root/myproject"}, "result": {...}}
{"timestamp": "2024-01-15T10:30:01.000Z", "type": "context_change", "context": {"project_focus": "/root/myproject"}}
{"timestamp": "2024-01-15T10:35:00.000Z", "type": "session_continue"}
{"timestamp": "2024-01-15T10:35:01.000Z", "type": "tool_call", "tool": "dir_tree", "params": {}, "result": {...}}
```

### Why Append-Only?

1. **Debugging** - Full history of what happened
2. **Replay** - Can reconstruct any point in time
3. **Audit** - Complete log of all actions
4. **No corruption** - Never modify past entries

## Session State

### What Sessions Store

| State | Description | Persisted |
|-------|-------------|-----------|
| `session_id` | Unique session identifier | Yes |
| `project_focus` | Current project path | Yes |
| `tool_calls` | History of invocations | Yes |
| `errors` | Error history | Yes |

### What Sessions DON'T Store

| State | Why Not |
|-------|---------|
| File contents | Too large, changes frequently |
| System state | Ephemeral, not session-specific |
| Credentials | Security risk |
| Process state | Not persistent |

## Session Expiry

Sessions expire after 24 hours of inactivity (configurable in `config.py`).

### Checking Expiry

```bash
python3 agent.py --list-sessions
```

Expired sessions show `"expired": true`.

### Expired Session Behavior

```bash
# Try to resume expired session
python3 agent.py --resume sess_old123 --tool file_read --params '...'

# Falls back to creating new session
# Returns: new session_id
```

### Cleanup

Expired sessions are not automatically deleted. To clean up:

```bash
# Manual cleanup
rm ~/.vps-cc-mcp/sessions/sess_*.jsonl

# Or write a cron job
find ~/.vps-cc-mcp/sessions/ -mtime +7 -delete
```

## Session ID Format

Session IDs follow the pattern: `sess_<8-char-random>`

```
sess_abc12345
│    │
│    └─ 8 random alphanumeric characters
└────── Prefix for identification
```

## Multi-Project Workflows

Sessions enable seamless multi-project workflows:

```bash
# Work on project A
python3 agent.py --tool project_focus --params '{"path": "/root/projectA"}'
# session_id: sess_aaa111

python3 agent.py --continue --tool file_read --params '{"path": "config.py"}'

# Switch to project B (same session)
python3 agent.py --continue --tool project_focus --params '{"path": "/root/projectB"}'

python3 agent.py --continue --tool file_read --params '{"path": "config.py"}'
# Reads from projectB

# Come back to project A later
python3 agent.py --continue --tool project_focus --params '{"path": "/root/projectA"}'
```

## Session Context in Responses

Every response includes session context:

```json
{
  "success": true,
  "session_id": "sess_abc123",
  "tool": "file_read",
  "result": {...},
  "context": {
    "project": "/root/myproject",
    "session_id": "sess_abc123"
  }
}
```

## Best Practices

### Do

- ✅ Use `--continue` for sequential operations
- ✅ Save session IDs for long-running tasks
- ✅ Use `project_focus` to establish context first
- ✅ Check session list before resuming old sessions

### Don't

- ❌ Parse session files directly (use the API)
- ❌ Manually edit session files
- ❌ Rely on sessions for critical state
- ❌ Assume sessions persist forever

## Configuration

In `config.py`:

```python
# Session storage location
SESSION_DIR = Path.home() / ".vps-cc-mcp" / "sessions"

# Session expiry (hours)
SESSION_TTL_HOURS = 24

# Session ID format
SESSION_ID_PREFIX = "sess_"
SESSION_ID_LENGTH = 8
```

## Troubleshooting

### Session Not Found

```json
{
  "success": false,
  "error": {
    "type": "SessionNotFound",
    "message": "Session sess_xyz789 not found or expired"
  }
}
```

**Solution:** Start a new session or use `--list-sessions` to find valid sessions.

### Project Focus Lost

If `--continue` doesn't preserve project focus:

1. Check the session file exists
2. Verify the session hasn't expired
3. Look for errors in the session log

### Permission Errors

```bash
# Ensure directory exists with correct permissions
mkdir -p ~/.vps-cc-mcp/sessions
chmod 700 ~/.vps-cc-mcp
```
