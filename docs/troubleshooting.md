# Troubleshooting

Common issues and solutions for VPS-CC-MCP.

## Installation Issues

### Python Version Error

**Symptom:**
```
SyntaxError: invalid syntax
```

**Cause:** Python version too old (< 3.10)

**Solution:**
```bash
# Check version
python3 --version

# Install newer Python
sudo apt install python3.11
python3.11 /opt/vps-cc-mcp/agent.py --list-tools
```

### Pydantic Not Found

**Symptom:**
```
ModuleNotFoundError: No module named 'pydantic'
```

**Solution:**
```bash
pip install pydantic>=2.0
# Or
pip install --user pydantic>=2.0
```

### Pydantic Version Error

**Symptom:**
```
ImportError: cannot import name 'field_validator' from 'pydantic'
```

**Cause:** Pydantic v1 installed instead of v2

**Solution:**
```bash
pip install --upgrade pydantic>=2.0
```

---

## Runtime Issues

### Tool Not Found

**Symptom:**
```json
{
  "success": false,
  "error": {
    "type": "ToolNotFound",
    "message": "Unknown tool: my_tool"
  }
}
```

**Solution:**
```bash
# List available tools
python3 agent.py --list-tools
```

### Approval Required

**Symptom:**
```json
{
  "success": false,
  "error": {
    "type": "ApprovalRequired",
    "message": "Tool 'bash_run' requires explicit approval"
  }
}
```

**Solution:**
```bash
python3 agent.py --auto-approve --tool bash_run --params '...'
```

### File Not Found

**Symptom:**
```json
{
  "success": false,
  "error": {
    "type": "FileNotFoundError",
    "message": "File not found: /path/to/file"
  }
}
```

**Causes:**
1. File doesn't exist
2. Relative path without project focus

**Solution:**
```bash
# Use absolute path
python3 agent.py --tool file_read --params '{"path": "/absolute/path/to/file"}'

# Or set project focus first
python3 agent.py --tool project_focus --params '{"path": "/root/myproject"}'
python3 agent.py --continue --tool file_read --params '{"path": "relative/path"}'
```

### Permission Denied

**Symptom:**
```json
{
  "success": false,
  "error": {
    "type": "PermissionError",
    "message": "Permission denied: /etc/shadow"
  }
}
```

**Cause:** Running as user without sufficient permissions

**Solution:**
- Run agent as appropriate user
- Use sudo if needed (carefully)

---

## Session Issues

### Session Not Found

**Symptom:**
```json
{
  "success": false,
  "error": {
    "type": "SessionNotFound",
    "message": "Session sess_xyz123 not found"
  }
}
```

**Causes:**
1. Session expired
2. Session file deleted
3. Wrong session ID

**Solution:**
```bash
# List available sessions
python3 agent.py --list-sessions

# Start new session
python3 agent.py --tool project_focus --params '{"path": "/root/myproject"}'
```

### Project Focus Lost

**Symptom:**
```json
{
  "success": false,
  "error": {
    "type": "ValueError",
    "message": "Cannot resolve relative path without project focus"
  }
}
```

**Cause:** `--continue` used but session expired or lost

**Solution:**
```bash
# Re-establish focus
python3 agent.py --tool project_focus --params '{"path": "/root/myproject"}'
python3 agent.py --continue --tool file_read --params '{"path": "relative/path"}'
```

### Session Directory Permission Error

**Symptom:**
```
PermissionError: [Errno 13] Permission denied: '/root/.vps-cc-mcp/sessions'
```

**Solution:**
```bash
mkdir -p ~/.vps-cc-mcp/sessions
chmod 700 ~/.vps-cc-mcp
chmod 700 ~/.vps-cc-mcp/sessions
```

---

## Service Issues

### Service Not Found

**Symptom:**
```json
{
  "success": false,
  "error": {
    "type": "ValueError",
    "message": "Could not find service 'myapp' in any manager"
  }
}
```

**Solution:**
```bash
# Check available services
python3 agent.py --tool service_list --params '{}'

# Specify manager explicitly
python3 agent.py --tool service_status --params '{"name": "myapp", "manager": "pm2"}'
```

### Systemctl Permission Denied

**Symptom:**
```json
{
  "result": {
    "success": false,
    "error": "Interactive authentication required"
  }
}
```

**Cause:** User lacks systemd permissions

**Solution:**
- Run as root
- Add user to appropriate groups
- Use polkit rules

### Docker Permission Denied

**Symptom:**
```
permission denied while trying to connect to the Docker daemon
```

**Solution:**
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in
```

---

## Bash Execution Issues

### Command Timeout

**Symptom:**
```json
{
  "result": {
    "timed_out": true,
    "stderr": "Command timed out after 60 seconds"
  }
}
```

**Solution:**
```bash
# Increase timeout
python3 agent.py --auto-approve --tool bash_run --params '{"command": "long_task", "timeout": 300}'
```

### Output Truncated

**Symptom:**
```json
{
  "result": {
    "stdout_truncated": true,
    "stdout": "... (output truncated)"
  }
}
```

**Cause:** Output exceeded 1MB limit

**Solution:**
- Redirect output to file, then read file
- Use `head` or `tail` to limit output
- Increase `BASH_MAX_OUTPUT_BYTES` in config

---

## JSON Issues

### Invalid JSON Parameters

**Symptom:**
```json
{
  "success": false,
  "error": {
    "type": "InvalidJSON",
    "message": "Invalid JSON in --params"
  }
}
```

**Causes:**
1. Unescaped quotes
2. Trailing commas
3. Single quotes instead of double

**Solution:**
```bash
# Use proper escaping
python3 agent.py --tool file_read --params '{"path": "/etc/hostname"}'

# For complex JSON, use a file
echo '{"path": "/etc/hostname"}' > /tmp/params.json
python3 agent.py --tool file_read --params "$(cat /tmp/params.json)"
```

### SSH Escaping Issues

**Symptom:** JSON parsing errors over SSH

**Solution:**
```bash
# Single quotes outside, escaped inside
ssh user@vps "python3 /opt/vps-cc-mcp/agent.py --tool file_read --params '{\"path\": \"/etc/hostname\"}'"

# Or use base64
PARAMS=$(echo '{"path": "/etc/hostname"}' | base64)
ssh user@vps "python3 /opt/vps-cc-mcp/agent.py --tool file_read --params \"\$(echo $PARAMS | base64 -d)\""
```

---

## Performance Issues

### Slow dir_tree

**Symptom:** dir_tree takes too long

**Solution:**
```bash
# Limit depth
python3 agent.py --tool dir_tree --params '{"max_depth": 2}'

# Filter by pattern
python3 agent.py --tool dir_tree --params '{"pattern": "*.py", "max_depth": 3}'
```

### Large File Read

**Symptom:** file_read slow or fails

**Solution:**
```bash
# Read specific lines
python3 agent.py --tool file_read --params '{"path": "huge.log", "start_line": 9000, "end_line": 10000}'
```

---

## Getting Help

### Check Tool Schema

```bash
python3 agent.py --list-tools | jq '.result.tools[] | select(.name == "file_read")'
```

### View Session History

```bash
cat ~/.vps-cc-mcp/sessions/sess_abc123.jsonl | jq
```

### Verify Installation

```bash
# Full verification
python3 agent.py --list-tools
python3 agent.py --tool vps_status --params '{}'
python3 agent.py --tool file_read --params '{"path": "/etc/hostname"}'
```

### Report Issues

When reporting issues, include:
1. Full error response (JSON)
2. Command that caused the error
3. Python version (`python3 --version`)
4. Pydantic version (`pip show pydantic`)
