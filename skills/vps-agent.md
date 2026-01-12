# VPS-CC-MCP Agent Skill

This skill enables you to control a VPS through the VPS-CC-MCP tool execution server via SSH MCP.

## Overview

You have access to a VPS-resident agent that can:
- Read and write files on the VPS
- Explore project codebases
- Manage services (systemd, Docker, pm2)
- Check system status
- Execute bash commands

**Your role:** You are the "brain" that decides what to do. The VPS-CC-MCP agent is the "hands" that executes your commands.

## How to Invoke Tools

Invoke tools via SSH MCP using this pattern:

```bash
ssh user@vps "python3 /opt/vps-cc-mcp/agent.py --tool <tool_name> --params '<json>'"
```

All responses are structured JSON with this format:
```json
{
  "success": true,
  "session_id": "sess_abc123",
  "tool": "tool_name",
  "result": { ... },
  "error": null
}
```

## Available Tools

### Project Context
| Tool | Description | Example |
|------|-------------|---------|
| `project_focus` | Set active project | `{"path": "/root/myproject"}` |
| `project_list` | List projects | `{"base_path": "/root"}` |
| `project_info` | Get project details | `{}` (uses focus) |

### Files
| Tool | Description | Example |
|------|-------------|---------|
| `file_read` | Read file content | `{"path": "main.py"}` |
| `file_write` | Write to file | `{"path": "config.json", "content": "..."}` |
| `dir_tree` | Directory structure | `{"max_depth": 3}` |

### Code Intelligence
| Tool | Description | Example |
|------|-------------|---------|
| `code_explain` | Get code structure | `{"path": "auth.py"}` |
| `code_debug` | Gather debug context | `{"error": "Traceback..."}` |

### Services
| Tool | Description | Example |
|------|-------------|---------|
| `service_list` | List all services | `{"manager": "systemd"}` |
| `service_status` | Check service | `{"name": "nginx"}` |
| `service_start` | Start service | `{"name": "nginx"}` |
| `service_stop` | Stop service | `{"name": "nginx"}` |
| `service_restart` | Restart service | `{"name": "nginx"}` |

### System
| Tool | Description | Example |
|------|-------------|---------|
| `vps_status` | System status | `{"include_processes": true}` |
| `bash_run` | Run command | `{"command": "git status"}` |

## Approval Levels

Tools have three approval levels:

| Level | Behavior | Tools |
|-------|----------|-------|
| **Auto** | Execute immediately | file_read, dir_tree, vps_status, etc. |
| **Confirm** | Ask user first | file_write, service_start, service_restart |
| **Explicit** | Requires `--auto-approve` | bash_run, service_stop |

### For Confirm-level tools:
Before invoking, show the user what you're about to do:
```
"I'm going to write this content to config.json:
[content preview]
Should I proceed?"
```

### For Explicit-level tools:
Add `--auto-approve` flag:
```bash
python3 agent.py --auto-approve --tool bash_run --params '{"command": "..."}'
```

## Session Management

Sessions maintain context across invocations.

### Start a session:
```bash
python3 agent.py --tool project_focus --params '{"path": "/root/myproject"}'
# Returns: session_id: "sess_abc123"
```

### Continue session:
```bash
python3 agent.py --continue --tool file_read --params '{"path": "main.py"}'
```

### Resume specific session:
```bash
python3 agent.py --resume sess_abc123 --tool dir_tree --params '{}'
```

## Best Practices

### 1. Establish Context First
Always start by setting project focus:
```bash
--tool project_focus --params '{"path": "/root/myproject"}'
```

### 2. Use --continue for Related Operations
```bash
--tool project_focus --params '{"path": "/root/api"}'
--continue --tool dir_tree --params '{}'
--continue --tool file_read --params '{"path": "src/index.ts"}'
```

### 3. Confirm Before Modifying
For file_write, service_start, etc., always show the user:
- What you're about to change
- The new content/action
- Ask for confirmation

### 4. Use Dry Run for Preview
```bash
--tool file_write --params '{"path": "config.json", "content": "...", "dry_run": true}'
```

### 5. Prefer Specific Tools Over bash_run
- Use `file_read` instead of `cat`
- Use `dir_tree` instead of `find` or `ls -R`
- Use `service_status` instead of `systemctl status`

### 6. Handle Errors Gracefully
Check `success` field in response:
```json
{"success": false, "error": {"type": "FileNotFoundError", ...}}
```

## Common Workflows

### Explore a Project
1. `project_focus` - Set context
2. `project_info` - Get overview
3. `dir_tree` - See structure
4. `file_read` - Read key files
5. `code_explain` - Understand code

### Debug an Issue
1. `code_debug` - Pass error message
2. `file_read` - Read relevant files
3. Analyze and explain to user
4. `file_write` - Fix the issue (with confirmation)

### Service Maintenance
1. `service_status` - Check current state
2. Make config changes with `file_write`
3. `service_restart` - Apply changes
4. `service_status` - Verify

### System Check
1. `vps_status` - Overall health
2. `service_list` - All services
3. Report findings to user

## Error Handling

| Error Type | Cause | Solution |
|------------|-------|----------|
| `FileNotFoundError` | File doesn't exist | Check path, use absolute path |
| `ApprovalRequired` | Needs --auto-approve | Add flag for explicit tools |
| `ValidationError` | Bad parameters | Check parameter schema |
| `PermissionError` | Access denied | Check file/service permissions |

## Response Interpretation

### code_explain Response
The agent returns raw code context. YOU provide the explanation:
```json
{
  "content": "def authenticate(user): ...",
  "imports": ["jwt", "bcrypt"],
  "functions": ["authenticate", "generate_token"],
  "classes": ["AuthManager"]
}
```
Analyze this structure and explain it to the user in natural language.

### code_debug Response
The agent returns context around errors. YOU diagnose the bug:
```json
{
  "error": "TypeError: ...",
  "traceback_files": [{"path": "api.py", "line": 42, "snippet": {...}}]
}
```
Analyze the code and explain the bug to the user.

## Important Notes

1. **You are the orchestrator** - The agent only executes, it doesn't think
2. **Always use sessions** - Context is maintained across calls
3. **Confirm modifications** - Ask user before file_write, service changes
4. **Interpret results** - The agent returns data, you explain it
5. **Handle JSON carefully** - Escape quotes properly in SSH commands
