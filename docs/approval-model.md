# Approval Model

VPS-CC-MCP uses a tiered approval system to balance automation with safety.

## Overview

Every tool has an **approval level** that determines how it can be executed:

| Level | Description | Flag Required |
|-------|-------------|---------------|
| **Auto** | Execute immediately | None |
| **Confirm** | LLM should confirm with user first | None |
| **Explicit** | Requires `--auto-approve` flag | `--auto-approve` |

## Approval Levels

### Auto

Tools that are safe, read-only, or have minimal impact.

**Behavior:** Execute immediately without any confirmation.

**Tools:**
- `project_list`, `project_info`, `project_focus`
- `file_read`, `dir_tree`
- `code_explain`, `code_debug`
- `service_list`, `service_status`
- `vps_status`

**Example:**
```bash
# Executes immediately
python3 agent.py --tool file_read --params '{"path": "/etc/hostname"}'
```

### Confirm

Tools that modify state but are generally reversible.

**Behavior:**
- Agent executes the tool
- External LLM should confirm with user before invoking
- Confirmation happens in the LLM chat, not in the agent

**Tools:**
- `file_write`
- `service_start`, `service_restart`

**Example:**
```bash
# External LLM should ask user first:
# "I'm about to write to config.json. Proceed?"
# User: "Yes"
# Then LLM invokes:
python3 agent.py --tool file_write --params '{"path": "config.json", "content": "..."}'
```

**Important:** The agent itself doesn't prompt for confirmation. The external LLM is responsible for confirming with the user before invoking Confirm-level tools.

### Explicit

Tools that are dangerous, destructive, or have significant impact.

**Behavior:**
- Agent requires `--auto-approve` flag
- Without flag, returns an error
- This is a hard enforcement, not a suggestion

**Tools:**
- `bash_run`
- `service_stop`

**Example:**
```bash
# Without --auto-approve: ERROR
python3 agent.py --tool bash_run --params '{"command": "rm -rf /tmp/old"}'
# Returns: {"success": false, "error": {"type": "ApprovalRequired", ...}}

# With --auto-approve: Executes
python3 agent.py --auto-approve --tool bash_run --params '{"command": "rm -rf /tmp/old"}'
```

## Tool Approval Matrix

| Tool | Level | Rationale |
|------|-------|-----------|
| `project_focus` | Auto | Context switch is safe |
| `project_list` | Auto | Read-only listing |
| `project_info` | Auto | Read-only info |
| `file_read` | Auto | Read-only |
| `file_write` | Confirm | Modifies files |
| `dir_tree` | Auto | Read-only |
| `code_explain` | Auto | Read-only analysis |
| `code_debug` | Auto | Read-only analysis |
| `service_list` | Auto | Read-only listing |
| `service_status` | Auto | Read-only status |
| `service_start` | Confirm | Starts processes |
| `service_stop` | Explicit | Stops critical services |
| `service_restart` | Confirm | Brief interruption |
| `vps_status` | Auto | Read-only system info |
| `bash_run` | Explicit | Arbitrary command execution |

## The `--auto-approve` Flag

### Purpose

Bypasses the Explicit approval requirement. Use for:
- Trusted, supervised batch operations
- Automated scripts where you've pre-verified safety
- Emergency situations requiring quick action

### Usage

```bash
python3 agent.py --auto-approve --tool bash_run --params '{"command": "..."}'
```

### Security Considerations

- The flag grants full access to Explicit tools
- Should only be used in trusted contexts
- The SSH MCP layer still provides authentication
- Consider logging all `--auto-approve` invocations

## Dry Run Mode

All tools support `dry_run` for previewing actions:

```bash
# Preview what would happen
python3 agent.py --tool file_write --params '{
  "path": "config.json",
  "content": "{\"key\": \"value\"}",
  "dry_run": true
}'
```

Response:
```json
{
  "success": true,
  "dry_run": true,
  "result": {
    "dry_run": true,
    "would_execute": "file_write",
    "params": {"path": "config.json", "content": "..."},
    "approval_level": "confirm"
  }
}
```

### Dry Run Workflow

1. External LLM decides to write a file
2. LLM invokes with `dry_run: true`
3. Agent returns preview
4. LLM shows preview to user
5. User confirms
6. LLM invokes without `dry_run`

## Confirmation Flow

### Headless Confirmation Model

Because the agent runs headless (no TTY), confirmation cannot happen during execution. Instead:

```
┌──────────────────────────────────────────────────────────────────┐
│ External LLM Chat                                                │
│                                                                  │
│ 1. User: "Update the config file"                               │
│ 2. LLM: "I'll update config.json. Here's the new content:       │
│          [shows content]                                         │
│          Should I proceed?"                                      │
│ 3. User: "Yes"                                                   │
│ 4. LLM invokes tool ─────────────────────────────────────────────┼──┐
└──────────────────────────────────────────────────────────────────┘  │
                                                                       │
┌──────────────────────────────────────────────────────────────────┐  │
│ VPS-CC-MCP Agent                                                 │  │
│                                                                  │◄─┘
│ Receives: {"tool": "file_write", "params": {...}}               │
│ Executes: Writes file immediately                                │
│ Returns: {"success": true, ...}                                  │
└──────────────────────────────────────────────────────────────────┘
```

Key points:
- Confirmation happens in the LLM chat
- The agent assumes confirmation already occurred
- The agent never prompts or waits

### Error Response for Missing Approval

When an Explicit tool is called without `--auto-approve`:

```json
{
  "success": false,
  "session_id": "sess_abc123",
  "tool": "bash_run",
  "approval_level": "explicit",
  "error": {
    "type": "ApprovalRequired",
    "message": "Tool 'bash_run' requires explicit approval. Use --auto-approve flag to execute.",
    "tool": "bash_run",
    "details": {}
  }
}
```

## Customizing Approval Levels

Approval levels are defined in `config.py`:

```python
TOOL_APPROVAL_LEVELS = {
    # Change file_write to explicit if needed
    "file_write": ApprovalLevel.EXPLICIT,

    # Or make service_stop confirm-only
    "service_stop": ApprovalLevel.CONFIRM,
}
```

⚠️ **Warning:** Lowering approval levels reduces safety. Only do this if you understand the risks.

## Best Practices

### For LLM Integration

1. **Always show intent before Confirm tools:**
   ```
   LLM: "I'm going to write this content to config.json:
         [content]
         Proceed?"
   ```

2. **Use dry_run for previews:**
   ```bash
   # First: preview
   agent.py --tool file_write --params '{"...", "dry_run": true}'
   # Then: execute
   agent.py --tool file_write --params '{"..."}'
   ```

3. **Only use --auto-approve when needed:**
   - Batch operations with pre-verified commands
   - Scripts running in supervised environments
   - Emergency maintenance

### For Security

1. **Audit Explicit tool usage:**
   - Log all `--auto-approve` invocations
   - Review session files regularly

2. **Limit bash_run usage:**
   - Prefer specific tools over bash_run
   - Use bash_run only for operations not covered

3. **Monitor service_stop:**
   - Stopping services can cause outages
   - Always have restart plan ready

## Comparison with Claude Code

VPS-CC-MCP's approval model is inspired by Claude Code's permission modes:

| Claude Code | VPS-CC-MCP |
|-------------|------------|
| `--permission-mode default` | Auto + Confirm |
| `--permission-mode acceptEdits` | Auto + Confirm (LLM confirms) |
| `--permission-mode bypassPermissions` | `--auto-approve` |

The key difference: VPS-CC-MCP runs headless, so confirmation must happen before invocation, not during.
