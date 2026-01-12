# Installation

This guide covers installing VPS-CC-MCP on your VPS.

## Prerequisites

### System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **OS** | Linux (any distro) | Ubuntu 22.04+ / Debian 12+ |
| **Python** | 3.10+ | 3.11+ |
| **Memory** | 512 MB | 1 GB |
| **Disk** | 100 MB | 500 MB |

### SSH MCP

VPS-CC-MCP requires an existing SSH MCP connection. The SSH MCP:
- Handles authentication (SSH keys)
- Provides the transport layer
- Routes tool invocations to the agent

This guide assumes your SSH MCP is already configured and working.

## Installation Methods

### Method 1: Direct Clone (Recommended)

```bash
# SSH into your VPS
ssh user@your-vps

# Clone to /opt (or your preferred location)
cd /opt
git clone <repository-url> vps-cc-mcp

# Install dependencies
pip install -r vps-cc-mcp/requirements.txt

# Verify installation
python3 vps-cc-mcp/agent.py --list-tools
```

### Method 2: Manual Copy

If git is not available:

```bash
# On your local machine
scp -r ./vps-cc-mcp user@your-vps:/opt/

# On the VPS
ssh user@your-vps
pip install pydantic>=2.0
python3 /opt/vps-cc-mcp/agent.py --list-tools
```

### Method 3: Single User Install

For user-local installation:

```bash
# Clone to home directory
cd ~
git clone <repository-url> vps-cc-mcp

# Use user-local pip
pip install --user -r vps-cc-mcp/requirements.txt

# Add to PATH (optional)
echo 'alias vps-agent="python3 ~/vps-cc-mcp/agent.py"' >> ~/.bashrc
source ~/.bashrc

# Test
vps-agent --list-tools
```

## Dependencies

VPS-CC-MCP has minimal dependencies:

| Package | Version | Purpose |
|---------|---------|---------|
| `pydantic` | >= 2.0, < 3.0 | Input validation, JSON schemas |

All other functionality uses Python standard library.

### Installing Dependencies

```bash
# System-wide (requires root)
sudo pip install pydantic>=2.0

# User-local
pip install --user pydantic>=2.0

# In a virtual environment (recommended for development)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Directory Structure

After installation:

```
/opt/vps-cc-mcp/           # Installation directory
├── agent.py               # Main entrypoint
├── config.py              # Configuration
├── context.py             # Project context
├── session.py             # Session management
├── schemas/               # Pydantic models
│   ├── requests.py
│   └── responses.py
├── tools/                 # Tool implementations
│   ├── base.py
│   ├── project.py
│   ├── files.py
│   ├── code.py
│   ├── services.py
│   ├── vps.py
│   └── bash.py
├── docs/                  # Documentation
└── requirements.txt

~/.vps-cc-mcp/             # Runtime data (created automatically)
└── sessions/              # Session storage
    ├── sess_abc123.jsonl
    └── ...
```

## Configuration

### Environment Variables

VPS-CC-MCP doesn't require environment variables but respects:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOME` | (system) | Location for session storage |

### Config File

Edit `config.py` for customization:

```python
# Session settings
SESSION_DIR = Path.home() / ".vps-cc-mcp" / "sessions"
SESSION_TTL_HOURS = 24

# Execution limits
BASH_TIMEOUT_SECONDS = 60
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB
```

## Verification

### Test Basic Functionality

```bash
# List tools
python3 /opt/vps-cc-mcp/agent.py --list-tools

# Check VPS status
python3 /opt/vps-cc-mcp/agent.py --tool vps_status --params '{}'

# Read a file
python3 /opt/vps-cc-mcp/agent.py --tool file_read --params '{"path": "/etc/hostname"}'

# Test session creation
python3 /opt/vps-cc-mcp/agent.py --tool project_focus --params '{"path": "/tmp"}'
python3 /opt/vps-cc-mcp/agent.py --continue --tool dir_tree --params '{}'
```

### Test via SSH MCP

From your LLM chat client's perspective:

```bash
# Invoke through SSH
ssh user@vps "python3 /opt/vps-cc-mcp/agent.py --tool vps_status --params '{}'"
```

Expected output: Structured JSON response with VPS information.

## Troubleshooting Installation

### Python Version Too Old

```bash
# Check Python version
python3 --version

# If < 3.10, install newer Python
sudo apt install python3.11
python3.11 /opt/vps-cc-mcp/agent.py --list-tools
```

### Pydantic Not Found

```bash
# Install pydantic
pip install pydantic>=2.0

# Or with sudo
sudo pip install pydantic>=2.0
```

### Permission Denied

```bash
# Make agent.py executable
chmod +x /opt/vps-cc-mcp/agent.py

# Or always use python3 prefix
python3 /opt/vps-cc-mcp/agent.py --list-tools
```

### Session Directory Issues

```bash
# Create session directory manually
mkdir -p ~/.vps-cc-mcp/sessions
chmod 700 ~/.vps-cc-mcp
```

## Updating

### Update from Git

```bash
cd /opt/vps-cc-mcp
git pull origin main
pip install -r requirements.txt
```

### Manual Update

```bash
# Backup sessions (optional)
cp -r ~/.vps-cc-mcp/sessions ~/.vps-cc-mcp/sessions.bak

# Replace files
scp -r ./vps-cc-mcp/* user@vps:/opt/vps-cc-mcp/

# Verify
python3 /opt/vps-cc-mcp/agent.py --list-tools
```

## Uninstallation

```bash
# Remove installation
rm -rf /opt/vps-cc-mcp

# Remove session data (optional)
rm -rf ~/.vps-cc-mcp

# Remove pydantic (if not used elsewhere)
pip uninstall pydantic
```

## Next Steps

- [Configure your tools](configuration.md)
- [Learn the approval model](approval-model.md)
- [See usage examples](examples.md)
