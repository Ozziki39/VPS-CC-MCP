# Architecture

VPS-CC-MCP follows a clear separation of concerns between reasoning (external LLM) and execution (this agent).

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     EXTERNAL LLM CHAT CLIENT                            │
│                     (Claude / ChatGPT / Mobile)                         │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  • Receives user requests                                        │   │
│  │  • Analyzes context and decides actions                          │   │
│  │  • Chooses which tools to invoke                                 │   │
│  │  • Interprets results and formulates responses                   │   │
│  │  • Asks user for confirmation when needed                        │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                │ SSH MCP
                                │ (Transport + Authentication)
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         VPS-CC-MCP AGENT                                │
│                         (Tool Execution Server)                         │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  • Receives structured JSON commands                             │   │
│  │  • Validates input parameters                                    │   │
│  │  • Executes tools deterministically                              │   │
│  │  • Returns structured JSON responses                             │   │
│  │  • Manages session state                                         │   │
│  │  • Enforces approval levels                                      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │   Session    │  │   Project    │  │    Tool      │                  │
│  │   Manager    │  │   Context    │  │   Registry   │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                         TOOLS                                     │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐ │  │
│  │  │ Project │ │  Files  │ │  Code   │ │Services │ │ VPS │ Bash  │ │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────────┘ │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          VPS RESOURCES                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │Filesystem│  │ Services │  │ Processes│  │  Network │               │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘               │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### External LLM (Claude/GPT)

| Responsibility | Description |
|----------------|-------------|
| **Reasoning** | Understands user intent, plans actions |
| **Tool Selection** | Decides which tools to invoke |
| **Result Analysis** | Interprets returned context |
| **User Interaction** | Asks for confirmation, provides explanations |
| **Error Recovery** | Handles failures, suggests alternatives |

### SSH MCP Layer

| Responsibility | Description |
|----------------|-------------|
| **Authentication** | SSH key-based auth, user verification |
| **Transport** | Secure command delivery |
| **Routing** | Directs tool invocations to agent |
| **Isolation** | Enforces host-level access control |

### VPS-CC-MCP Agent

| Responsibility | Description |
|----------------|-------------|
| **Execution** | Runs tools deterministically |
| **Validation** | Validates input parameters |
| **Session Management** | Persists context across invocations |
| **Approval Enforcement** | Checks permission levels |
| **Error Handling** | Returns structured error responses |

## Data Flow

### Request Flow

```
1. User → LLM: "What files are in myproject?"
2. LLM decides: Use project_focus then dir_tree
3. LLM → SSH MCP → Agent: {"tool": "project_focus", "params": {"path": "/root/myproject"}}
4. Agent validates, executes, returns JSON
5. LLM → SSH MCP → Agent: {"tool": "dir_tree", "params": {}}
6. Agent uses session context, returns tree
7. LLM analyzes results, responds to user
```

### Session State Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Invocation 1│     │ Invocation 2│     │ Invocation 3│
│             │     │ --continue  │     │ --resume ID │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌──────────────────────────────────────────────────────┐
│                    Session Store                      │
│            ~/.vps-cc-mcp/sessions/                    │
│                                                       │
│  sess_abc123.jsonl                                   │
│  ├─ {"type": "session_start", ...}                   │
│  ├─ {"type": "tool_call", "tool": "project_focus"}   │
│  ├─ {"type": "context_change", "project": "/root/p"} │
│  ├─ {"type": "session_continue", ...}                │
│  ├─ {"type": "tool_call", "tool": "dir_tree"}        │
│  └─ ...                                              │
└──────────────────────────────────────────────────────┘
```

## Design Principles

### 1. Execution, Not Reasoning

The agent never decides what to do. It only executes what it's told. All reasoning happens in the external LLM.

```
❌ Agent decides to fix a bug
✅ LLM decides to fix a bug, tells agent which files to read/write
```

### 2. Deterministic Behavior

Given the same input, the agent produces the same output. No randomness, no AI inference.

```python
# Tool execution is pure function
result = tool.execute(validated_params)
```

### 3. Structured Everything

All input and output is structured JSON. No parsing stdout, no regex extraction.

```json
// Input
{"tool": "file_read", "params": {"path": "/etc/hostname"}}

// Output
{"success": true, "result": {"content": "myhost\n", "lines": 1}}
```

### 4. Fail Fast, Fail Loud

Errors are caught immediately and returned as structured responses. No silent failures.

```json
{
  "success": false,
  "error": {
    "type": "FileNotFoundError",
    "message": "File not found: /nonexistent",
    "tool": "file_read"
  }
}
```

### 5. Context Return, Not Analysis

Code intelligence tools return context for the LLM to analyze, not analysis results.

```json
// code_explain returns:
{
  "content": "def main(): ...",
  "imports": ["os", "sys"],
  "functions": ["main", "helper"],
  "classes": []
}
// LLM does the explaining
```

## Security Model

### Trust Boundaries

```
┌─────────────────────────────────────────┐
│           TRUSTED BOUNDARY              │
│  ┌───────────────────────────────────┐  │
│  │  User's LLM Chat Client           │  │
│  │  (Claude/GPT with user context)   │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
                    │
                    │ SSH (authenticated)
                    ▼
┌─────────────────────────────────────────┐
│         VPS EXECUTION BOUNDARY          │
│  ┌───────────────────────────────────┐  │
│  │  VPS-CC-MCP Agent                 │  │
│  │  (runs as SSH user)               │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### Security Features

| Feature | Implementation |
|---------|----------------|
| **Authentication** | SSH key-based (handled by SSH MCP) |
| **Authorization** | Approval levels (auto/confirm/explicit) |
| **Isolation** | Runs as SSH user, inherits permissions |
| **Audit** | Session logs all tool calls |
| **Rate Limiting** | Not implemented (rely on SSH MCP) |

## Scalability

### Single VPS Model

VPS-CC-MCP is designed for single-VPS deployments:

- One agent instance per VPS
- Stateless execution (no memory between calls)
- Session state on local disk
- No clustering or distribution

### Resource Usage

| Resource | Usage |
|----------|-------|
| **Memory** | ~50MB Python process per invocation |
| **CPU** | Minimal (tool execution only) |
| **Disk** | Session logs grow slowly |
| **Network** | SSH connections only |

## Future Considerations (v2+)

The architecture supports these potential enhancements:

- **On-VPS AI**: Claude Code CLI via OAuth for local reasoning
- **Background Jobs**: Long-running command tracking
- **Webhooks**: Event notifications
- **Multi-VPS**: Coordination across servers

These are explicitly **out of scope for v1**.
