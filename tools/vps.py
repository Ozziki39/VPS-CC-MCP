"""
VPS status tool for VPS-CC-MCP.

Provides system-level information about the VPS.
"""

import os
import subprocess
from typing import Any

from config import ApprovalLevel
from schemas.requests import VpsStatusParams
from tools.base import BaseTool, ToolMetadata, register_tool


def run_command(cmd: list[str], timeout: int = 10) -> tuple[int, str, str]:
    """Run a command and return (exit_code, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)


def get_hostname() -> str:
    """Get system hostname."""
    try:
        return os.uname().nodename
    except Exception:
        return "unknown"


def get_uptime() -> str:
    """Get system uptime."""
    try:
        with open("/proc/uptime", "r") as f:
            uptime_seconds = float(f.read().split()[0])

        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)

        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        parts.append(f"{minutes}m")

        return " ".join(parts)
    except Exception:
        return "unknown"


def get_load_average() -> list[float]:
    """Get system load average."""
    try:
        with open("/proc/loadavg", "r") as f:
            parts = f.read().split()
            return [float(parts[0]), float(parts[1]), float(parts[2])]
    except Exception:
        return [0.0, 0.0, 0.0]


def get_memory_info() -> dict[str, Any]:
    """Get memory information."""
    try:
        with open("/proc/meminfo", "r") as f:
            info = {}
            for line in f:
                if ":" in line:
                    key, value = line.split(":", 1)
                    # Parse kB values
                    parts = value.strip().split()
                    if parts:
                        info[key] = int(parts[0]) * 1024  # Convert to bytes

            total = info.get("MemTotal", 0)
            available = info.get("MemAvailable", 0)
            free = info.get("MemFree", 0)
            buffers = info.get("Buffers", 0)
            cached = info.get("Cached", 0)
            used = total - available

            return {
                "total_bytes": total,
                "available_bytes": available,
                "used_bytes": used,
                "free_bytes": free,
                "buffers_bytes": buffers,
                "cached_bytes": cached,
                "percent_used": round((used / total) * 100, 1) if total > 0 else 0,
                "total_human": _human_size(total),
                "used_human": _human_size(used),
                "available_human": _human_size(available),
            }
    except Exception as e:
        return {"error": str(e)}


def get_disk_info() -> dict[str, Any]:
    """Get disk information for root filesystem."""
    try:
        stat = os.statvfs("/")
        total = stat.f_blocks * stat.f_frsize
        free = stat.f_bfree * stat.f_frsize
        available = stat.f_bavail * stat.f_frsize
        used = total - free

        return {
            "total_bytes": total,
            "used_bytes": used,
            "free_bytes": free,
            "available_bytes": available,
            "percent_used": round((used / total) * 100, 1) if total > 0 else 0,
            "total_human": _human_size(total),
            "used_human": _human_size(used),
            "available_human": _human_size(available),
        }
    except Exception as e:
        return {"error": str(e)}


def get_cpu_info() -> dict[str, Any]:
    """Get CPU information."""
    try:
        # Count CPUs
        cpu_count = os.cpu_count() or 1

        # Get CPU model from /proc/cpuinfo
        model = "unknown"
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if line.startswith("model name"):
                    model = line.split(":", 1)[1].strip()
                    break

        return {
            "count": cpu_count,
            "model": model,
        }
    except Exception as e:
        return {"error": str(e)}


def get_top_processes(limit: int = 10) -> list[dict[str, Any]]:
    """Get top processes by CPU/memory usage."""
    try:
        code, stdout, _ = run_command([
            "ps", "aux", "--sort=-pcpu"
        ])
        if code != 0:
            return []

        processes = []
        lines = stdout.splitlines()

        # Skip header, take top N
        for line in lines[1:limit + 1]:
            parts = line.split(None, 10)
            if len(parts) >= 11:
                processes.append({
                    "user": parts[0],
                    "pid": int(parts[1]),
                    "cpu_percent": float(parts[2]),
                    "memory_percent": float(parts[3]),
                    "vsz": int(parts[4]),
                    "rss": int(parts[5]),
                    "command": parts[10][:80],  # Truncate long commands
                })

        return processes
    except Exception:
        return []


def get_network_info() -> dict[str, Any]:
    """Get network information."""
    try:
        # Get network interfaces and their IPs
        code, stdout, _ = run_command(["ip", "-j", "addr", "show"])

        if code == 0:
            import json
            interfaces = json.loads(stdout)
            result = {"interfaces": []}

            for iface in interfaces:
                if iface.get("ifname") == "lo":
                    continue

                iface_info = {
                    "name": iface.get("ifname"),
                    "state": iface.get("operstate"),
                    "addresses": [],
                }

                for addr in iface.get("addr_info", []):
                    iface_info["addresses"].append({
                        "address": addr.get("local"),
                        "family": addr.get("family"),
                        "prefixlen": addr.get("prefixlen"),
                    })

                result["interfaces"].append(iface_info)

            return result
        else:
            return {"error": "Failed to get network info"}
    except Exception as e:
        return {"error": str(e)}


def _human_size(size_bytes: int) -> str:
    """Convert bytes to human readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


@register_tool
class VpsStatusTool(BaseTool):
    """Get VPS system status."""

    metadata = ToolMetadata(
        name="vps_status",
        approval_level=ApprovalLevel.AUTO,
        description="Get VPS system status including hostname, uptime, load, memory, disk, and CPU info.",
        params_model=VpsStatusParams,
    )

    def execute(self, params: VpsStatusParams) -> dict[str, Any]:
        """Get VPS status."""
        result = {
            "hostname": get_hostname(),
            "uptime": get_uptime(),
            "load_average": get_load_average(),
            "memory": get_memory_info(),
            "disk": get_disk_info(),
            "cpu": get_cpu_info(),
        }

        if params.include_processes:
            result["processes"] = get_top_processes()

        if params.include_network:
            result["network"] = get_network_info()

        return result
