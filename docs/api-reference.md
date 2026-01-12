# API Reference

Complete JSON schema documentation for VPS-CC-MCP.

## CLI Interface

### Basic Invocation

```bash
python3 agent.py --tool <tool_name> --params '<json>'
```

### All Options

| Option | Description |
|--------|-------------|
| `--tool <name>` | Tool to execute |
| `--params '<json>'` | JSON parameters (default: `{}`) |
| `--continue` | Continue most recent session |
| `--resume <id>` | Resume specific session |
| `--auto-approve` | Bypass explicit approval requirement |
| `--list-tools` | List available tools |
| `--list-sessions` | List active sessions |

## Request Format

Requests are passed via CLI `--params` as JSON:

```json
{
  "path": "/path/to/file",
  "content": "file content",
  "dry_run": false
}
```

## Response Format

All responses follow this structure:

```json
{
  "success": true,
  "session_id": "sess_abc123",
  "tool": "file_read",
  "approval_level": "auto",
  "dry_run": false,
  "result": { ... },
  "context": {
    "project": "/root/myproject",
    "session_id": "sess_abc123",
    "additional": {}
  },
  "error": null,
  "timestamp": "2024-01-15T10:30:00.000000Z"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether the operation succeeded |
| `session_id` | string | Session identifier |
| `tool` | string | Tool that was executed |
| `approval_level` | string | Tool's approval level |
| `dry_run` | boolean | Whether this was a dry run |
| `result` | object/null | Tool-specific result data |
| `context` | object | Execution context |
| `error` | object/null | Error details if failed |
| `timestamp` | string | ISO 8601 timestamp |

## Error Response Format

```json
{
  "success": false,
  "session_id": "sess_abc123",
  "tool": "file_read",
  "approval_level": "auto",
  "dry_run": false,
  "result": null,
  "context": {
    "project": null,
    "session_id": "sess_abc123",
    "additional": {}
  },
  "error": {
    "type": "FileNotFoundError",
    "message": "File not found: /nonexistent",
    "tool": "file_read",
    "details": {}
  },
  "timestamp": "2024-01-15T10:30:00.000000Z"
}
```

### Error Types

| Type | Description |
|------|-------------|
| `ValidationError` | Invalid input parameters |
| `FileNotFoundError` | File does not exist |
| `PermissionError` | Access denied |
| `ValueError` | Invalid value |
| `ApprovalRequired` | Needs `--auto-approve` |
| `TimeoutError` | Command timed out |
| `ToolNotFound` | Unknown tool name |
| `SessionNotFound` | Session doesn't exist |

---

## Parameter Schemas

### Base Parameters

All tools accept:

```json
{
  "dry_run": false
}
```

### Project Tools

#### project_focus

```json
{
  "path": "/absolute/path/to/project",
  "dry_run": false
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `path` | string | Yes | Absolute path to project |
| `dry_run` | boolean | No | Preview mode |

#### project_list

```json
{
  "base_path": "/path/to/search",
  "dry_run": false
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `base_path` | string | No | ~/projects | Search directory |
| `dry_run` | boolean | No | false | Preview mode |

#### project_info

```json
{
  "path": "/path/to/project",
  "dry_run": false
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `path` | string | No | (focus) | Project path |
| `dry_run` | boolean | No | false | Preview mode |

### File Tools

#### file_read

```json
{
  "path": "relative/or/absolute/path",
  "start_line": 1,
  "end_line": 100,
  "encoding": "utf-8",
  "dry_run": false
}
```

| Field | Type | Required | Default | Constraints |
|-------|------|----------|---------|-------------|
| `path` | string | Yes | - | - |
| `start_line` | integer | No | null | >= 1 |
| `end_line` | integer | No | null | >= 1 |
| `encoding` | string | No | "utf-8" | - |
| `dry_run` | boolean | No | false | - |

#### file_write

```json
{
  "path": "relative/or/absolute/path",
  "content": "file content here",
  "create_dirs": true,
  "encoding": "utf-8",
  "dry_run": false
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `path` | string | Yes | - | File path |
| `content` | string | Yes | - | Content to write |
| `create_dirs` | boolean | No | true | Create parent dirs |
| `encoding` | string | No | "utf-8" | File encoding |
| `dry_run` | boolean | No | false | Preview mode |

#### dir_tree

```json
{
  "path": "/path/to/directory",
  "max_depth": 3,
  "include_hidden": false,
  "pattern": "*.py",
  "dry_run": false
}
```

| Field | Type | Required | Default | Constraints |
|-------|------|----------|---------|-------------|
| `path` | string | No | (focus) | - |
| `max_depth` | integer | No | 3 | 1-10 |
| `include_hidden` | boolean | No | false | - |
| `pattern` | string | No | null | Glob pattern |
| `dry_run` | boolean | No | false | - |

### Code Tools

#### code_explain

```json
{
  "path": "path/to/file.py",
  "question": "How does this work?",
  "dry_run": false
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `path` | string | Yes | - | File to analyze |
| `question` | string | No | null | Specific question |
| `dry_run` | boolean | No | false | Preview mode |

#### code_debug

```json
{
  "path": "path/to/file.py",
  "error": "Traceback...",
  "context": "Additional info",
  "dry_run": false
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `path` | string | No | null | File with error |
| `error` | string | No | null | Error/traceback |
| `context` | string | No | null | Additional context |
| `dry_run` | boolean | No | false | Preview mode |

### Service Tools

#### service_list

```json
{
  "manager": "systemd",
  "dry_run": false
}
```

| Field | Type | Required | Default | Options |
|-------|------|----------|---------|---------|
| `manager` | string | No | null | systemd, docker, pm2 |
| `dry_run` | boolean | No | false | - |

#### service_status

```json
{
  "name": "nginx",
  "manager": "systemd",
  "dry_run": false
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | Yes | - | Service name |
| `manager` | string | No | null | Auto-detect |
| `dry_run` | boolean | No | false | Preview mode |

#### service_start / service_stop / service_restart

```json
{
  "name": "nginx",
  "manager": "systemd",
  "dry_run": false
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | Yes | - | Service name |
| `manager` | string | No | null | Auto-detect |
| `dry_run` | boolean | No | false | Preview mode |

### VPS Tools

#### vps_status

```json
{
  "include_processes": true,
  "include_network": true,
  "dry_run": false
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `include_processes` | boolean | No | false | Top processes |
| `include_network` | boolean | No | false | Network info |
| `dry_run` | boolean | No | false | Preview mode |

### Bash Tools

#### bash_run

```json
{
  "command": "ls -la",
  "timeout": 60,
  "cwd": "/path/to/directory",
  "dry_run": false
}
```

| Field | Type | Required | Default | Constraints |
|-------|------|----------|---------|-------------|
| `command` | string | Yes | - | - |
| `timeout` | integer | No | 60 | 1-300 |
| `cwd` | string | No | (focus) | - |
| `dry_run` | boolean | No | false | - |

---

## Result Schemas

### project_info Result

```json
{
  "path": "/root/myproject",
  "name": "myproject",
  "exists": true,
  "is_dir": true,
  "is_git": true,
  "files_count": 156,
  "directories_count": 23,
  "config_files": ["package.json", "tsconfig.json"],
  "readme": "README.md",
  "languages": ["TypeScript", "JavaScript"]
}
```

### file_read Result

```json
{
  "path": "/root/myproject/main.py",
  "content": "#!/usr/bin/env python3\n...",
  "lines": 50,
  "total_lines": 200,
  "size_bytes": 4532,
  "encoding": "utf-8",
  "truncated": true
}
```

### dir_tree Result

```json
{
  "path": "/root/myproject",
  "tree": {
    "name": "myproject",
    "type": "directory",
    "children": [
      {
        "name": "src",
        "type": "directory",
        "children": [...]
      },
      {
        "name": "main.py",
        "type": "file",
        "size": 1234
      }
    ]
  },
  "total_files": 42,
  "total_dirs": 8,
  "truncated": false
}
```

### code_explain Result

```json
{
  "path": "/root/myproject/auth.py",
  "file_type": "python",
  "content": "#!/usr/bin/env python3\n...",
  "lines": 150,
  "size_bytes": 4500,
  "structure": {
    "imports": ["jwt", "datetime"],
    "functions": [
      {"name": "create_token", "args": ["user_id"], "line": 15}
    ],
    "classes": [
      {"name": "AuthHandler", "methods": ["login"], "line": 60}
    ],
    "global_vars": ["SECRET_KEY"]
  },
  "question": "How does authentication work?"
}
```

### service_status Result

```json
{
  "name": "nginx",
  "manager": "systemd",
  "status": "active",
  "sub_state": "running",
  "pid": 1234,
  "enabled": true,
  "started_at": "2024-01-15 10:30:00 UTC"
}
```

### vps_status Result

```json
{
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
    "percent_used": 40.0,
    "total_human": "100.0 GB",
    "used_human": "40.0 GB"
  },
  "cpu": {
    "count": 4,
    "model": "Intel Xeon E5-2680"
  },
  "processes": [...],
  "network": {...}
}
```

### bash_run Result

```json
{
  "command": "git status",
  "exit_code": 0,
  "stdout": "On branch main\n...",
  "stderr": "",
  "timed_out": false,
  "duration_seconds": 0.045,
  "cwd": "/root/myproject",
  "stdout_truncated": false,
  "stderr_truncated": false
}
```

---

## Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | Error (check JSON response) |

## HTTP-like Status Mapping

For API gateways that need HTTP status codes:

| Scenario | Status |
|----------|--------|
| `success: true` | 200 |
| `error.type: ValidationError` | 400 |
| `error.type: ApprovalRequired` | 403 |
| `error.type: ToolNotFound` | 404 |
| `error.type: *` | 500 |
