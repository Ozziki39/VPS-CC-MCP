# Unified VPS CLI - Implementation Roadmap

**Status:** Planned | **Priority:** v1.1 | **Location:** `/root/SSH-MCP/vps`

## Overview

Create single `vps` CLI integrating VPS-CC-MCP (tools) + mcp-claude (AI).

## Commands

```bash
# Tools
vps tool <n> --params JSON
vps status|read|tree|focus|services|bash

# AI
vps ai quick|edit|analyze|safe <prompt>

# Session
vps sessions|continue|resume
```

## Script Location

`/root/SSH-MCP/vps` - bash dispatcher to agent.py and mcp-claude

## Implementation

```bash
#!/bin/bash
AGENT="/root/SSH-MCP/VPS-CC-MCP/agent.py"
MCP="/root/SSH-MCP/bin/mcp-claude"

case "$1" in
  tool|--tool) shift; python3 $AGENT --tool "$@" ;;
  ai|claude)   shift; $MCP "$@" ;;
  status)   python3 $AGENT --tool vps_status --params "{}" ;;
  read)     python3 $AGENT --tool file_read --params "{\"path\":\"$2\"}" ;;
  tree)     python3 $AGENT --tool dir_tree --params "{}" ;;
  focus)    python3 $AGENT --tool project_focus --params "{\"path\":\"$2\"}" ;;
  services) python3 $AGENT --tool service_list --params "{}" ;;
  sessions) python3 $AGENT --list-sessions ;;
  tools)    python3 $AGENT --list-tools ;;
  help)     echo "vps [tool|ai|status|read|tree|focus|services|bash]" ;;
esac
```

## Usage via SSH MCP

```bash
exec command="vps status"
exec command="vps focus /root/myproject"
exec command="vps ai quick What is this?"
```

## Checklist

- [ ] Create /root/SSH-MCP/vps script
- [ ] chmod +x
- [ ] Test tool shortcuts
- [ ] Test AI mode
- [ ] Symlink to /usr/local/bin/vps
- [ ] Update docs
