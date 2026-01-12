# VPS-CC-MCP Documentation

**VPS-CC-MCP** is a VPS-resident development and operations agent, remotely controlled via external LLM chat clients (GPT and Claude) through an SSH-based MCP.

## Overview

VPS-CC-MCP is a **tool execution server**, not an autonomous agent. The external LLM chat client (Claude/GPT) is the "brain" that decides what to do, while VPS-CC-MCP is the "hands" that executes commands on your VPS.

### Key Characteristics

- **Headless execution** - No TTY, no interactive prompts
- **Structured JSON I/O** - All input/output is JSON
- **Stateless between invocations** - State persisted in sessions only
- **No LLM reasoning** - The agent executes, doesn't think
- **No paid API calls** - External LLM does all reasoning

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](architecture.md) | System design and data flow |
| [Installation](installation.md) | Setup and deployment guide |
| [Tools Reference](tools-reference.md) | Complete tool documentation |
| [Sessions](sessions.md) | Session management and persistence |
| [Approval Model](approval-model.md) | Permission levels and confirmation |
| [API Reference](api-reference.md) | JSON schemas and response formats |
| [Examples](examples.md) | Common workflows and use cases |
| [Configuration](configuration.md) | Customization options |
| [Troubleshooting](troubleshooting.md) | Common issues and solutions |

## Quick Start

```bash
# Install
cd /opt
git clone <repo> vps-cc-mcp
pip install -r vps-cc-mcp/requirements.txt

# Test
python3 vps-cc-mcp/agent.py --list-tools
python3 vps-cc-mcp/agent.py --tool vps_status --params '{}'

# Via SSH MCP
ssh user@vps "python3 /opt/vps-cc-mcp/agent.py --tool file_read --params '{\"path\": \"/etc/hostname\"}'"
```

## Tools at a Glance

| Category | Tools | Description |
|----------|-------|-------------|
| **Project** | `project_focus`, `project_list`, `project_info` | Multi-project context management |
| **Files** | `file_read`, `file_write`, `dir_tree` | File operations |
| **Code** | `code_explain`, `code_debug` | Code intelligence (context gathering) |
| **Services** | `service_list`, `service_status`, `service_start`, `service_stop`, `service_restart` | Service management |
| **VPS** | `vps_status` | System status |
| **Bash** | `bash_run` | Escape hatch for arbitrary commands |

## Version

- **Current**: v1.0.0
- **Python**: 3.10+
- **Dependencies**: pydantic >= 2.0
