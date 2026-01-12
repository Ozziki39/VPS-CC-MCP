"""
Service management tools for VPS-CC-MCP.

Supports systemd, Docker, and pm2 service managers.

Tools:
- service_list: List services
- service_status: Get service status
- service_start: Start a service
- service_stop: Stop a service
- service_restart: Restart a service
"""

import json
import shutil
import subprocess
from typing import Any, Optional

from config import ApprovalLevel, BASH_TIMEOUT_SECONDS
from schemas.requests import ServiceListParams, ServiceStatusParams, ServiceControlParams
from tools.base import BaseTool, ToolMetadata, register_tool


def run_command(cmd: list[str], timeout: int = BASH_TIMEOUT_SECONDS) -> tuple[int, str, str]:
    """Run a command and return (exit_code, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)


def is_available(manager: str) -> bool:
    """Check if a service manager is available."""
    if manager == "systemd":
        return shutil.which("systemctl") is not None
    elif manager == "docker":
        return shutil.which("docker") is not None
    elif manager == "pm2":
        return shutil.which("pm2") is not None
    return False


def detect_manager(service_name: str) -> Optional[str]:
    """Auto-detect which manager handles a service."""
    # Check systemd first
    if is_available("systemd"):
        code, _, _ = run_command(["systemctl", "cat", service_name])
        if code == 0:
            return "systemd"

    # Check docker
    if is_available("docker"):
        code, _, _ = run_command(["docker", "inspect", service_name])
        if code == 0:
            return "docker"

    # Check pm2
    if is_available("pm2"):
        code, stdout, _ = run_command(["pm2", "jlist"])
        if code == 0:
            try:
                processes = json.loads(stdout)
                for proc in processes:
                    if proc.get("name") == service_name:
                        return "pm2"
            except json.JSONDecodeError:
                pass

    return None


# =============================================================================
# Systemd helpers
# =============================================================================

def systemd_list() -> list[dict[str, Any]]:
    """List systemd services."""
    code, stdout, _ = run_command([
        "systemctl", "list-units", "--type=service", "--all", "--no-pager", "--plain"
    ])
    if code != 0:
        return []

    services = []
    for line in stdout.splitlines()[1:]:  # Skip header
        parts = line.split(None, 4)
        if len(parts) >= 4:
            services.append({
                "name": parts[0].replace(".service", ""),
                "load": parts[1],
                "active": parts[2],
                "sub": parts[3],
                "description": parts[4] if len(parts) > 4 else "",
            })
    return services


def systemd_status(name: str) -> dict[str, Any]:
    """Get systemd service status."""
    code, stdout, stderr = run_command(["systemctl", "show", name, "--no-pager"])

    if code != 0:
        return {"name": name, "status": "unknown", "error": stderr}

    info: dict[str, Any] = {"name": name, "manager": "systemd"}

    for line in stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            if key == "ActiveState":
                info["status"] = value
            elif key == "SubState":
                info["sub_state"] = value
            elif key == "MainPID":
                info["pid"] = int(value) if value != "0" else None
            elif key == "UnitFileState":
                info["enabled"] = value == "enabled"
            elif key == "ActiveEnterTimestamp":
                info["started_at"] = value

    return info


def systemd_control(name: str, action: str) -> dict[str, Any]:
    """Control a systemd service."""
    code, stdout, stderr = run_command(["systemctl", action, name])
    return {
        "name": name,
        "action": action,
        "success": code == 0,
        "output": stdout,
        "error": stderr if code != 0 else None,
    }


# =============================================================================
# Docker helpers
# =============================================================================

def docker_list() -> list[dict[str, Any]]:
    """List Docker containers."""
    code, stdout, _ = run_command([
        "docker", "ps", "-a", "--format", "{{json .}}"
    ])
    if code != 0:
        return []

    containers = []
    for line in stdout.splitlines():
        if line.strip():
            try:
                data = json.loads(line)
                containers.append({
                    "name": data.get("Names", ""),
                    "image": data.get("Image", ""),
                    "status": data.get("State", data.get("Status", "")),
                    "ports": data.get("Ports", ""),
                })
            except json.JSONDecodeError:
                pass
    return containers


def docker_status(name: str) -> dict[str, Any]:
    """Get Docker container status."""
    code, stdout, stderr = run_command([
        "docker", "inspect", name, "--format", "{{json .}}"
    ])

    if code != 0:
        return {"name": name, "status": "unknown", "error": stderr}

    try:
        data = json.loads(stdout)
        state = data.get("State", {})
        return {
            "name": name,
            "manager": "docker",
            "status": state.get("Status", "unknown"),
            "running": state.get("Running", False),
            "pid": state.get("Pid"),
            "started_at": state.get("StartedAt"),
            "image": data.get("Config", {}).get("Image"),
        }
    except json.JSONDecodeError:
        return {"name": name, "status": "unknown", "error": "Failed to parse response"}


def docker_control(name: str, action: str) -> dict[str, Any]:
    """Control a Docker container."""
    code, stdout, stderr = run_command(["docker", action, name])
    return {
        "name": name,
        "action": action,
        "success": code == 0,
        "output": stdout,
        "error": stderr if code != 0 else None,
    }


# =============================================================================
# PM2 helpers
# =============================================================================

def pm2_list() -> list[dict[str, Any]]:
    """List PM2 processes."""
    code, stdout, _ = run_command(["pm2", "jlist"])
    if code != 0:
        return []

    try:
        processes = json.loads(stdout)
        return [
            {
                "name": p.get("name", ""),
                "pm_id": p.get("pm_id"),
                "status": p.get("pm2_env", {}).get("status", "unknown"),
                "memory": p.get("monit", {}).get("memory"),
                "cpu": p.get("monit", {}).get("cpu"),
            }
            for p in processes
        ]
    except json.JSONDecodeError:
        return []


def pm2_status(name: str) -> dict[str, Any]:
    """Get PM2 process status."""
    code, stdout, _ = run_command(["pm2", "jlist"])

    if code != 0:
        return {"name": name, "status": "unknown", "error": "Failed to get process list"}

    try:
        processes = json.loads(stdout)
        for p in processes:
            if p.get("name") == name:
                pm2_env = p.get("pm2_env", {})
                monit = p.get("monit", {})
                return {
                    "name": name,
                    "manager": "pm2",
                    "pm_id": p.get("pm_id"),
                    "status": pm2_env.get("status", "unknown"),
                    "pid": p.get("pid"),
                    "memory": monit.get("memory"),
                    "cpu": monit.get("cpu"),
                    "restarts": pm2_env.get("restart_time", 0),
                    "uptime": pm2_env.get("pm_uptime"),
                }
        return {"name": name, "status": "not_found", "error": "Process not found"}
    except json.JSONDecodeError:
        return {"name": name, "status": "unknown", "error": "Failed to parse response"}


def pm2_control(name: str, action: str) -> dict[str, Any]:
    """Control a PM2 process."""
    code, stdout, stderr = run_command(["pm2", action, name])
    return {
        "name": name,
        "action": action,
        "success": code == 0,
        "output": stdout,
        "error": stderr if code != 0 else None,
    }


# =============================================================================
# Tool implementations
# =============================================================================

@register_tool
class ServiceListTool(BaseTool):
    """List services from one or all managers."""

    metadata = ToolMetadata(
        name="service_list",
        approval_level=ApprovalLevel.AUTO,
        description="List services from systemd, Docker, or pm2. Specify manager or list all.",
        params_model=ServiceListParams,
    )

    def execute(self, params: ServiceListParams) -> dict[str, Any]:
        """List services."""
        result: dict[str, Any] = {"services": {}}

        managers = [params.manager] if params.manager else ["systemd", "docker", "pm2"]

        for manager in managers:
            if not is_available(manager):
                continue

            if manager == "systemd":
                result["services"]["systemd"] = systemd_list()
            elif manager == "docker":
                result["services"]["docker"] = docker_list()
            elif manager == "pm2":
                result["services"]["pm2"] = pm2_list()

        return result


@register_tool
class ServiceStatusTool(BaseTool):
    """Get status of a service."""

    metadata = ToolMetadata(
        name="service_status",
        approval_level=ApprovalLevel.AUTO,
        description="Get detailed status of a service. Auto-detects manager if not specified.",
        params_model=ServiceStatusParams,
    )

    def execute(self, params: ServiceStatusParams) -> dict[str, Any]:
        """Get service status."""
        manager = params.manager or detect_manager(params.name)

        if not manager:
            raise ValueError(f"Could not find service '{params.name}' in any manager")

        if manager == "systemd":
            return systemd_status(params.name)
        elif manager == "docker":
            return docker_status(params.name)
        elif manager == "pm2":
            return pm2_status(params.name)
        else:
            raise ValueError(f"Unknown manager: {manager}")


@register_tool
class ServiceStartTool(BaseTool):
    """Start a service."""

    metadata = ToolMetadata(
        name="service_start",
        approval_level=ApprovalLevel.CONFIRM,
        description="Start a stopped service.",
        params_model=ServiceControlParams,
    )

    def execute(self, params: ServiceControlParams) -> dict[str, Any]:
        """Start service."""
        manager = params.manager or detect_manager(params.name)

        if not manager:
            raise ValueError(f"Could not find service '{params.name}' in any manager")

        if manager == "systemd":
            return systemd_control(params.name, "start")
        elif manager == "docker":
            return docker_control(params.name, "start")
        elif manager == "pm2":
            return pm2_control(params.name, "start")
        else:
            raise ValueError(f"Unknown manager: {manager}")


@register_tool
class ServiceStopTool(BaseTool):
    """Stop a service."""

    metadata = ToolMetadata(
        name="service_stop",
        approval_level=ApprovalLevel.EXPLICIT,
        description="Stop a running service. Requires explicit approval.",
        params_model=ServiceControlParams,
    )

    def execute(self, params: ServiceControlParams) -> dict[str, Any]:
        """Stop service."""
        manager = params.manager or detect_manager(params.name)

        if not manager:
            raise ValueError(f"Could not find service '{params.name}' in any manager")

        if manager == "systemd":
            return systemd_control(params.name, "stop")
        elif manager == "docker":
            return docker_control(params.name, "stop")
        elif manager == "pm2":
            return pm2_control(params.name, "stop")
        else:
            raise ValueError(f"Unknown manager: {manager}")


@register_tool
class ServiceRestartTool(BaseTool):
    """Restart a service."""

    metadata = ToolMetadata(
        name="service_restart",
        approval_level=ApprovalLevel.CONFIRM,
        description="Restart a service.",
        params_model=ServiceControlParams,
    )

    def execute(self, params: ServiceControlParams) -> dict[str, Any]:
        """Restart service."""
        manager = params.manager or detect_manager(params.name)

        if not manager:
            raise ValueError(f"Could not find service '{params.name}' in any manager")

        if manager == "systemd":
            return systemd_control(params.name, "restart")
        elif manager == "docker":
            return docker_control(params.name, "restart")
        elif manager == "pm2":
            return pm2_control(params.name, "restart")
        else:
            raise ValueError(f"Unknown manager: {manager}")
