# Tools Reference

Complete documentation for all 15 VPS-CC-MCP tools.

## Overview

| Category | Tool | Approval | Description |
|----------|------|----------|-------------|
| Project | `project_focus` | Auto | Set current project context |
| Project | `project_list` | Auto | List available projects |
| Project | `project_info` | Auto | Get project information |
| Files | `file_read` | Auto | Read file contents |
| Files | `file_write` | Confirm | Write content to file |
| Files | `dir_tree` | Auto | Get directory structure |
| Code | `code_explain` | Auto | Gather code context |
| Code | `code_debug` | Auto | Gather debugging context |
| Services | `service_list` | Auto | List services |
| Services | `service_status` | Auto | Get service status |
| Services | `service_start` | Confirm | Start a service |
| Services | `service_stop` | Explicit | Stop a service |
| Services | `service_restart` | Confirm | Restart a service |
| VPS | `vps_status` | Auto | Get system status |
| Bash | `bash_run` | Explicit | Execute shell command |

---

## Project Tools

### project_focus

Set the current project context. Subsequent relative paths will resolve against this project.

**Approval Level:** Auto

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `path` | string | Yes | - | Absolute path to project directory |
| `dry_run` | boolean | No | false | Preview without executing |

**Example:**

```bash
python3 agent.py --tool project_focus --params '{"path": "/root/myproject"}'
```

**Response:**

```json
{
  "success": true,
  "session_id": "sess_abc123",
  "tool": "project_focus",
  "result": {
    "focused": true,
    "path": "/root/myproject",
    "project": {
      "path": "/root/myproject",
      "name": "myproject",
      "exists": true,
      "is_git": true,
      "files_count": 42,
      "directories_count": 5,
      "languages": ["Python", "JavaScript"],
      "config_files": ["package.json", "requirements.txt"]
    }
  }
}
```

---

### project_list

List available projects in a directory.

**Approval Level:** Auto

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `base_path` | string | No | ~/projects | Directory to search |
| `dry_run` | boolean | No | false | Preview without executing |

**Example:**

```bash
python3 agent.py --tool project_list --params '{"base_path": "/root"}'
```

**Response:**

```json
{
  "success": true,
  "result": {
    "base_path": "/root",
    "count": 3,
    "projects": [
      {"path": "/root/api-server", "name": "api-server", "type": "node", "markers": ["package.json", ".git"]},
      {"path": "/root/ml-pipeline", "name": "ml-pipeline", "type": "python", "markers": ["requirements.txt", ".git"]},
      {"path": "/root/infra", "name": "infra", "type": "unknown", "markers": ["Makefile"]}
    ]
  }
}
```

---

### project_info

Get detailed information about a project.

**Approval Level:** Auto

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `path` | string | No | (current focus) | Project path |
| `dry_run` | boolean | No | false | Preview without executing |

**Example:**

```bash
# Use current focus
python3 agent.py --continue --tool project_info --params '{}'

# Specify path
python3 agent.py --tool project_info --params '{"path": "/root/myproject"}'
```

**Response:**

```json
{
  "success": true,
  "result": {
    "path": "/root/myproject",
    "name": "myproject",
    "exists": true,
    "is_dir": true,
    "is_git": true,
    "files_count": 156,
    "directories_count": 23,
    "config_files": ["package.json", "tsconfig.json", ".eslintrc"],
    "readme": "README.md",
    "languages": ["TypeScript", "JavaScript", "Shell"]
  }
}
```

---

## File Tools

### file_read

Read the contents of a file.

**Approval Level:** Auto

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `path` | string | Yes | - | File path (relative or absolute) |
| `start_line` | integer | No | null | Start line (1-indexed) |
| `end_line` | integer | No | null | End line (1-indexed) |
| `encoding` | string | No | "utf-8" | File encoding |
| `dry_run` | boolean | No | false | Preview without executing |

**Example:**

```bash
# Read entire file
python3 agent.py --tool file_read --params '{"path": "/etc/hostname"}'

# Read specific lines
python3 agent.py --tool file_read --params '{"path": "main.py", "start_line": 1, "end_line": 50}'
```

**Response:**

```json
{
  "success": true,
  "result": {
    "path": "/root/myproject/main.py",
    "content": "#!/usr/bin/env python3\nimport os\n...",
    "lines": 50,
    "total_lines": 200,
    "size_bytes": 4532,
    "encoding": "utf-8",
    "truncated": true
  }
}
```

---

### file_write

Write content to a file.

**Approval Level:** Confirm

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `path` | string | Yes | - | File path (relative or absolute) |
| `content` | string | Yes | - | Content to write |
| `create_dirs` | boolean | No | true | Create parent directories |
| `encoding` | string | No | "utf-8" | File encoding |
| `dry_run` | boolean | No | false | Preview without executing |

**Example:**

```bash
# Write file
python3 agent.py --tool file_write --params '{"path": "config.json", "content": "{\"key\": \"value\"}"}'

# Dry run first
python3 agent.py --tool file_write --params '{"path": "config.json", "content": "...", "dry_run": true}'
```

**Response:**

```json
{
  "success": true,
  "result": {
    "path": "/root/myproject/config.json",
    "created": true,
    "modified": false,
    "old_size_bytes": 0,
    "new_size_bytes": 18,
    "lines": 1,
    "encoding": "utf-8"
  }
}
```

---

### dir_tree

Get directory structure as a tree.

**Approval Level:** Auto

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `path` | string | No | (current focus) | Directory path |
| `max_depth` | integer | No | 3 | Max traversal depth (1-10) |
| `include_hidden` | boolean | No | false | Include hidden files |
| `pattern` | string | No | null | Glob pattern filter |
| `dry_run` | boolean | No | false | Preview without executing |

**Example:**

```bash
# Current project
python3 agent.py --continue --tool dir_tree --params '{}'

# Filter Python files
python3 agent.py --tool dir_tree --params '{"path": "/root/project", "pattern": "*.py", "max_depth": 5}'
```

**Response:**

```json
{
  "success": true,
  "result": {
    "path": "/root/myproject",
    "tree": {
      "name": "myproject",
      "type": "directory",
      "children": [
        {"name": "src", "type": "directory", "children": [...]},
        {"name": "main.py", "type": "file", "size": 1234},
        {"name": "README.md", "type": "file", "size": 567}
      ]
    },
    "total_files": 42,
    "total_dirs": 8,
    "truncated": false
  }
}
```

---

## Code Tools

### code_explain

Gather code context for the external LLM to explain. Does NOT call any LLM API.

**Approval Level:** Auto

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `path` | string | Yes | - | File to explain |
| `question` | string | No | null | Specific question |
| `dry_run` | boolean | No | false | Preview without executing |

**Example:**

```bash
python3 agent.py --tool code_explain --params '{"path": "auth.py", "question": "How does authentication work?"}'
```

**Response:**

```json
{
  "success": true,
  "result": {
    "path": "/root/myproject/auth.py",
    "file_type": "python",
    "content": "#!/usr/bin/env python3\nimport jwt\n...",
    "lines": 150,
    "size_bytes": 4500,
    "structure": {
      "imports": ["jwt", "datetime", "os"],
      "functions": [
        {"name": "create_token", "args": ["user_id", "expires"], "line": 15},
        {"name": "verify_token", "args": ["token"], "line": 35}
      ],
      "classes": [
        {"name": "AuthHandler", "methods": ["login", "logout", "refresh"], "line": 60}
      ],
      "global_vars": ["SECRET_KEY", "TOKEN_EXPIRY"]
    },
    "question": "How does authentication work?"
  }
}
```

---

### code_debug

Gather debugging context for the external LLM to analyze.

**Approval Level:** Auto

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `path` | string | No | null | File with error |
| `error` | string | No | null | Error message/traceback |
| `context` | string | No | null | Additional context |
| `dry_run` | boolean | No | false | Preview without executing |

**Example:**

```bash
python3 agent.py --tool code_debug --params '{
  "path": "api.py",
  "error": "Traceback (most recent call last):\n  File \"api.py\", line 42\nKeyError: \"user_id\"",
  "context": "Happens when processing login requests"
}'
```

**Response:**

```json
{
  "success": true,
  "result": {
    "error": "Traceback (most recent call last):\n  File \"api.py\", line 42\nKeyError: \"user_id\"",
    "traceback_files": [
      {
        "path": "/root/myproject/api.py",
        "line": 42,
        "snippet": {
          "start_line": 37,
          "end_line": 47,
          "lines": ["def process_login(data):", "    ...", "    user_id = data['user_id']"],
          "error_line": 42
        }
      }
    ],
    "file": {
      "path": "/root/myproject/api.py",
      "file_type": "python",
      "content": "...",
      "lines": 200
    },
    "additional_context": "Happens when processing login requests",
    "project": "/root/myproject"
  }
}
```

---

## Service Tools

### service_list

List services from systemd, Docker, or pm2.

**Approval Level:** Auto

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `manager` | string | No | null | "systemd", "docker", or "pm2" (all if null) |
| `dry_run` | boolean | No | false | Preview without executing |

**Example:**

```bash
# List all
python3 agent.py --tool service_list --params '{}'

# Specific manager
python3 agent.py --tool service_list --params '{"manager": "docker"}'
```

**Response:**

```json
{
  "success": true,
  "result": {
    "services": {
      "systemd": [
        {"name": "nginx", "active": "active", "sub": "running"},
        {"name": "postgresql", "active": "active", "sub": "running"}
      ],
      "docker": [
        {"name": "redis", "status": "running", "image": "redis:7"},
        {"name": "api", "status": "running", "image": "myapi:latest"}
      ],
      "pm2": [
        {"name": "frontend", "pm_id": 0, "status": "online", "cpu": 0.5, "memory": 52428800}
      ]
    }
  }
}
```

---

### service_status

Get detailed status of a service.

**Approval Level:** Auto

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | string | Yes | - | Service name |
| `manager` | string | No | null | Auto-detect if null |
| `dry_run` | boolean | No | false | Preview without executing |

**Example:**

```bash
python3 agent.py --tool service_status --params '{"name": "nginx"}'
```

**Response:**

```json
{
  "success": true,
  "result": {
    "name": "nginx",
    "manager": "systemd",
    "status": "active",
    "sub_state": "running",
    "pid": 1234,
    "enabled": true,
    "started_at": "2024-01-15 10:30:00 UTC"
  }
}
```

---

### service_start

Start a stopped service.

**Approval Level:** Confirm

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | string | Yes | - | Service name |
| `manager` | string | No | null | Auto-detect if null |
| `dry_run` | boolean | No | false | Preview without executing |

**Example:**

```bash
python3 agent.py --tool service_start --params '{"name": "nginx"}'
```

---

### service_stop

Stop a running service.

**Approval Level:** Explicit (requires `--auto-approve`)

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | string | Yes | - | Service name |
| `manager` | string | No | null | Auto-detect if null |
| `dry_run` | boolean | No | false | Preview without executing |

**Example:**

```bash
# Will fail without --auto-approve
python3 agent.py --tool service_stop --params '{"name": "nginx"}'

# With approval
python3 agent.py --auto-approve --tool service_stop --params '{"name": "nginx"}'
```

---

### service_restart

Restart a service.

**Approval Level:** Confirm

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | string | Yes | - | Service name |
| `manager` | string | No | null | Auto-detect if null |
| `dry_run` | boolean | No | false | Preview without executing |

---

## VPS Tools

### vps_status

Get VPS system status.

**Approval Level:** Auto

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `include_processes` | boolean | No | false | Include top processes |
| `include_network` | boolean | No | false | Include network info |
| `dry_run` | boolean | No | false | Preview without executing |

**Example:**

```bash
python3 agent.py --tool vps_status --params '{"include_processes": true}'
```

**Response:**

```json
{
  "success": true,
  "result": {
    "hostname": "my-vps",
    "uptime": "15d 3h 42m",
    "load_average": [0.5, 0.7, 0.6],
    "memory": {
      "total_bytes": 8589934592,
      "available_bytes": 5368709120,
      "used_bytes": 3221225472,
      "percent_used": 37.5,
      "total_human": "8.0 GB",
      "used_human": "3.0 GB",
      "available_human": "5.0 GB"
    },
    "disk": {
      "total_bytes": 107374182400,
      "used_bytes": 42949672960,
      "available_bytes": 64424509440,
      "percent_used": 40.0,
      "total_human": "100.0 GB",
      "used_human": "40.0 GB",
      "available_human": "60.0 GB"
    },
    "cpu": {
      "count": 4,
      "model": "Intel Xeon E5-2680"
    },
    "processes": [
      {"pid": 1234, "user": "www-data", "cpu_percent": 15.2, "memory_percent": 5.1, "command": "nginx: worker"},
      {"pid": 2345, "user": "postgres", "cpu_percent": 8.5, "memory_percent": 12.3, "command": "postgres"}
    ]
  }
}
```

---

## Bash Tools

### bash_run

Execute arbitrary bash commands. Escape hatch for operations not covered by other tools.

**Approval Level:** Explicit (requires `--auto-approve`)

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `command` | string | Yes | - | Shell command |
| `timeout` | integer | No | 60 | Timeout in seconds (1-300) |
| `cwd` | string | No | (project focus) | Working directory |
| `dry_run` | boolean | No | false | Preview without executing |

**Example:**

```bash
# Will fail without --auto-approve
python3 agent.py --tool bash_run --params '{"command": "ls -la"}'

# With approval
python3 agent.py --auto-approve --tool bash_run --params '{"command": "git status", "cwd": "/root/myproject"}'
```

**Response:**

```json
{
  "success": true,
  "result": {
    "command": "git status",
    "exit_code": 0,
    "stdout": "On branch main\nYour branch is up to date with 'origin/main'.\n\nnothing to commit, working tree clean\n",
    "stderr": "",
    "timed_out": false,
    "duration_seconds": 0.045,
    "cwd": "/root/myproject",
    "stdout_truncated": false,
    "stderr_truncated": false
  }
}
```

**Timeout Example:**

```bash
python3 agent.py --auto-approve --tool bash_run --params '{"command": "sleep 120", "timeout": 5}'
```

```json
{
  "success": true,
  "result": {
    "command": "sleep 120",
    "exit_code": -1,
    "stdout": "",
    "stderr": "Command timed out after 5 seconds",
    "timed_out": true,
    "duration_seconds": 5.001
  }
}
```

---

## Common Parameters

All tools support these parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dry_run` | boolean | false | Preview action without executing |

## Error Responses

All tools return structured errors:

```json
{
  "success": false,
  "session_id": "sess_abc123",
  "tool": "file_read",
  "approval_level": "auto",
  "result": null,
  "error": {
    "type": "FileNotFoundError",
    "message": "File not found: /nonexistent",
    "tool": "file_read",
    "details": {}
  }
}
```

Common error types:

| Error Type | Description |
|------------|-------------|
| `ValidationError` | Invalid parameters |
| `FileNotFoundError` | File doesn't exist |
| `PermissionError` | Access denied |
| `ValueError` | Invalid value |
| `ApprovalRequired` | Needs `--auto-approve` |
| `TimeoutError` | Command timed out |
