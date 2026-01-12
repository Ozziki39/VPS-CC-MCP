# Usage Examples

Real-world workflows and patterns for VPS-CC-MCP.

## Basic Operations

### Check VPS Status

```bash
python3 agent.py --tool vps_status --params '{"include_processes": true}'
```

### Read a File

```bash
python3 agent.py --tool file_read --params '{"path": "/etc/nginx/nginx.conf"}'
```

### List Projects

```bash
python3 agent.py --tool project_list --params '{"base_path": "/root"}'
```

---

## Multi-Step Workflows

### Explore a New Project

```bash
# 1. Set project focus
python3 agent.py --tool project_focus --params '{"path": "/root/api-server"}'
# Save the session_id: sess_abc123

# 2. Get project info
python3 agent.py --continue --tool project_info --params '{}'

# 3. View directory structure
python3 agent.py --continue --tool dir_tree --params '{"max_depth": 4}'

# 4. Read the main entry point
python3 agent.py --continue --tool file_read --params '{"path": "src/index.ts"}'

# 5. Understand the code
python3 agent.py --continue --tool code_explain --params '{"path": "src/index.ts", "question": "What does this application do?"}'
```

### Debug an Error

```bash
# 1. Start with the error message
python3 agent.py --tool code_debug --params '{
  "error": "TypeError: Cannot read property '\''id'\'' of undefined\n    at processUser (/app/src/users.js:42)",
  "context": "Happens when creating a new user"
}'

# 2. Read the problematic file
python3 agent.py --continue --tool file_read --params '{"path": "/app/src/users.js", "start_line": 35, "end_line": 55}'

# 3. Check related code
python3 agent.py --continue --tool code_explain --params '{"path": "/app/src/users.js"}'
```

### Service Maintenance

```bash
# 1. Check current status
python3 agent.py --tool service_list --params '{"manager": "systemd"}'

# 2. Get details on specific service
python3 agent.py --tool service_status --params '{"name": "nginx"}'

# 3. Restart after config change
python3 agent.py --tool service_restart --params '{"name": "nginx"}'

# 4. Verify it's running
python3 agent.py --tool service_status --params '{"name": "nginx"}'
```

### Edit a Configuration File

```bash
# 1. Read current config
python3 agent.py --tool file_read --params '{"path": "/etc/nginx/sites-available/default"}'

# 2. Dry run the change
python3 agent.py --tool file_write --params '{
  "path": "/etc/nginx/sites-available/default",
  "content": "server {\n    listen 80;\n    ...\n}",
  "dry_run": true
}'

# 3. Apply the change
python3 agent.py --tool file_write --params '{
  "path": "/etc/nginx/sites-available/default",
  "content": "server {\n    listen 80;\n    ...\n}"
}'

# 4. Test and restart
python3 agent.py --auto-approve --tool bash_run --params '{"command": "nginx -t"}'
python3 agent.py --tool service_restart --params '{"name": "nginx"}'
```

---

## SSH MCP Integration

### Remote Invocation

```bash
# From external LLM via SSH MCP
ssh user@vps "python3 /opt/vps-cc-mcp/agent.py --tool vps_status --params '{}'"
```

### Multi-Command Session

```bash
# Session start
SESSION=$(ssh user@vps "python3 /opt/vps-cc-mcp/agent.py --tool project_focus --params '{\"path\": \"/root/myproject\"}'" | jq -r '.session_id')

# Continue session
ssh user@vps "python3 /opt/vps-cc-mcp/agent.py --resume $SESSION --tool dir_tree --params '{}'"

ssh user@vps "python3 /opt/vps-cc-mcp/agent.py --resume $SESSION --tool file_read --params '{\"path\": \"main.py\"}'"
```

---

## LLM Chat Patterns

### Pattern: Explore Then Act

1. **User**: "What's in the myproject folder?"
2. **LLM**: Invokes `project_focus` + `dir_tree`
3. **LLM**: Shows structure to user
4. **User**: "Read the main.py file"
5. **LLM**: Invokes `file_read` (using session)
6. **LLM**: Shows file content

### Pattern: Confirm Before Write

1. **User**: "Update the config with new database settings"
2. **LLM**: Invokes `file_read` to see current config
3. **LLM**: "Here's the current config. I'll change X to Y. Proceed?"
4. **User**: "Yes"
5. **LLM**: Invokes `file_write`
6. **LLM**: "Done. Should I restart the service?"

### Pattern: Debug Workflow

1. **User**: "I'm getting this error: [pastes error]"
2. **LLM**: Invokes `code_debug` with error
3. **LLM**: Invokes `file_read` on error locations
4. **LLM**: Analyzes and explains the bug
5. **LLM**: "I can fix this by changing line 42. Proceed?"
6. **User**: "Yes"
7. **LLM**: Invokes `file_write`

---

## Batch Operations

### Backup Multiple Configs

```bash
# Create backup directory
python3 agent.py --auto-approve --tool bash_run --params '{"command": "mkdir -p /backup/configs"}'

# Copy configs
for file in nginx.conf redis.conf postgresql.conf; do
  python3 agent.py --auto-approve --tool bash_run --params "{\"command\": \"cp /etc/$file /backup/configs/\"}"
done
```

### Check All Services

```bash
# Get all services as JSON, then check each
python3 agent.py --tool service_list --params '{}' | jq -r '.result.services.systemd[].name' | while read service; do
  python3 agent.py --tool service_status --params "{\"name\": \"$service\"}"
done
```

---

## Error Handling Patterns

### Graceful Error Recovery

```bash
# Try to read file, handle not found
RESULT=$(python3 agent.py --tool file_read --params '{"path": "config.json"}')

if echo "$RESULT" | jq -e '.success == false' > /dev/null; then
  echo "File not found, creating default..."
  python3 agent.py --tool file_write --params '{"path": "config.json", "content": "{}"}'
fi
```

### Validate Before Execute

```bash
# Dry run first
DRY=$(python3 agent.py --tool file_write --params '{
  "path": "important.cfg",
  "content": "new content",
  "dry_run": true
}')

# Check it's what we expect
if echo "$DRY" | jq -e '.result.would_execute == "file_write"' > /dev/null; then
  # Execute for real
  python3 agent.py --tool file_write --params '{
    "path": "important.cfg",
    "content": "new content"
  }'
fi
```

---

## Security Patterns

### Principle of Least Privilege

```bash
# Prefer specific tools over bash_run
# Good:
python3 agent.py --tool file_read --params '{"path": "/var/log/nginx/error.log"}'

# Avoid when possible:
python3 agent.py --auto-approve --tool bash_run --params '{"command": "cat /var/log/nginx/error.log"}'
```

### Audit Trail

```bash
# All tool calls are logged in session files
cat ~/.vps-cc-mcp/sessions/sess_abc123.jsonl | jq -c '{time: .timestamp, tool: .tool, params: .params}'
```

---

## Performance Tips

### Minimize Round Trips

```bash
# Instead of multiple file_read calls, use code_explain for structure
python3 agent.py --tool code_explain --params '{"path": "src/main.py"}'
# Returns content + structure in one call
```

### Use Line Ranges for Large Files

```bash
# Don't read entire 10000-line log
python3 agent.py --tool file_read --params '{"path": "/var/log/app.log", "start_line": 9900, "end_line": 10000}'
```

### Filter Directory Trees

```bash
# Instead of full tree, filter by pattern
python3 agent.py --tool dir_tree --params '{"pattern": "*.py", "max_depth": 5}'
```
