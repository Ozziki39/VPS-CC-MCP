---
name: vps-ssh-mcp
description: Control Ozz's VPS via SSH MCP. Use when the user asks to check VPS status, read/write files on VPS, manage services, explore projects, run commands, check system resources (RAM, disk, CPU), or work with any project on the remote server. Provides access to VPS-CC-MCP tool server and direct SSH command execution. Key directories include /root/SSH-MCP, /root/va-plan-staging, /root/mcp-mtg-server, /root/Anthony.
---

# VPS-SSH-MCP Skill

Control Ozz's Hostinger VPS via the VPS-SSH MCP tools.

## Available Tools

| Tool | Purpose |
|------|---------|
| `VPS-SSH:exec` | Execute shell commands on VPS |
| `VPS-SSH:sudo-exec` | Execute with sudo privileges |

## Key VPS Directories

```
/root/
├── SSH-MCP/                    # SSH MCP infrastructure
│   ├── VPS-CC-MCP/             # Tool execution server (15 tools)
│   │   ├── agent.py            # Main CLI entrypoint
│   │   ├── tools/              # Tool implementations
│   │   ├── docs/               # Full documentation
│   │   └── skills/             # LLM skill files
│   └── bin/                    # Claude Code CLI wrappers
│       └── mcp-claude          # AI-powered commands
├── va-plan-staging/            # Versatile Athletics web app (most active)
├── mcp-mtg-server/             # MTG MCP Server (production)
├── Anthony/                    # Anthony chatbot system
├── Codex-VA/                   # VA Plan earlier iteration
└── .vps-cc-mcp/sessions/       # VPS-CC-MCP session storage
```

## VPS-CC-MCP Agent

The agent at `/root/SSH-MCP/VPS-CC-MCP/agent.py` provides structured tool execution.

### Invocation Pattern

```bash
python3 /root/SSH-MCP/VPS-CC-MCP/agent.py --tool <tool_name> --params '<json>'
```

### Available Agent Tools

| Category | Tools |
|----------|-------|
| **Project** | `project_focus`, `project_list`, `project_info` |
| **Files** | `file_read`, `file_write`, `dir_tree` |
| **Code** | `code_explain`, `code_debug` |
| **Services** | `service_list`, `service_status`, `service_start`, `service_stop`, `service_restart` |
| **VPS** | `vps_status` |
| **Bash** | `bash_run` (requires `--auto-approve`) |

### Approval Levels

| Level | Tools | Flag |
|-------|-------|------|
| **Auto** | project_*, file_read, dir_tree, code_*, service_list, service_status, vps_status | None |
| **Confirm** | file_write, service_start, service_restart | Ask user first |
| **Explicit** | bash_run, service_stop | `--auto-approve` |

### Session Management

```bash
# Start session
python3 agent.py --tool project_focus --params '{"path": "/root/myproject"}'
# Returns session_id

# Continue session
python3 agent.py --continue --tool dir_tree --params '{}'

# Resume specific session
python3 agent.py --resume sess_abc123 --tool file_read --params '{"path": "main.py"}'
```

## Common Operations

### System Status

```bash
# Quick RAM/disk/CPU check
free -h && df -h / && uptime

# Full status via agent
python3 /root/SSH-MCP/VPS-CC-MCP/agent.py --tool vps_status --params '{"include_processes": true}'
```

### File Operations

```bash
# Direct read
cat /path/to/file

# Via agent (structured response)
python3 /root/SSH-MCP/VPS-CC-MCP/agent.py --tool file_read --params '{"path": "/path/to/file"}'

# Directory listing
ls -la /root/project/

# Via agent (tree structure)
python3 /root/SSH-MCP/VPS-CC-MCP/agent.py --tool dir_tree --params '{"path": "/root/project", "max_depth": 3}'
```

### Git Operations

```bash
cd /root/project && git status
cd /root/project && git log -5 --oneline
cd /root/project && git add . && git commit -m "message" && git push
```

### Service Management

```bash
# List services
systemctl list-units --type=service --state=running
pm2 list
docker ps

# Via agent
python3 /root/SSH-MCP/VPS-CC-MCP/agent.py --tool service_list --params '{}'
```

### Project Exploration

```bash
# Find recently modified files
find /root/project -type f -mtime -7 ! -path '*/.git/*' | head -20

# Check git activity
cd /root/project && git log --since="2025-01-01" --oneline | wc -l
```

## File Transfer: Claude.ai → VPS

Use base64 encoding to transfer files from Claude's ephemeral computer to VPS:

```bash
# 1. Create file locally (bash_tool)
echo "content" > /home/claude/file.md

# 2. Encode (bash_tool)
base64 /home/claude/file.md
# Returns: BASE64_STRING

# 3. Decode on VPS (VPS-SSH:exec)
echo 'BASE64_STRING' | base64 -d > /root/destination/file.md

# 4. Verify (VPS-SSH:exec)
cat /root/destination/file.md
```

For files >750 bytes, chunk the base64 and append with `>>`.

## Best Practices

1. **Direct commands for simple tasks** — Use `VPS-SSH:exec` with standard bash
2. **Agent for structured data** — Use VPS-CC-MCP when JSON responses are useful
3. **Check before modify** — Read files before writing, check service status before restart
4. **Use git for changes** — Commit meaningful changes to tracked projects
5. **Session continuity** — Use `--continue` for multi-step agent workflows

## Quick Reference

```bash
# RAM
free -h

# Disk
df -h /

# Top processes
ps aux --sort=-%mem | head -10

# Recent project activity
for d in /root/*/; do [ -d "$d/.git" ] && (cd "$d" && echo "$(git log -1 --format='%ci' 2>/dev/null) $(basename $d)"); done | sort -r | head -10

# Find project by name
ls -d /root/*pattern*

# Read agent docs
cat /root/SSH-MCP/VPS-CC-MCP/docs/index.md
```
