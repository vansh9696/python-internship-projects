import os
import platform
import shutil
import subprocess
import sys
from typing import Any, Dict, List

DEFAULT_REQUIRED_TOOLS = ["git", "python"]
DEFAULT_ENV_VARS = ["PATH", "OS", "USERNAME"]

def check_python_version(min_major: int = 3, min_minor: int = 9) -> Dict[str, Any]:
    current = sys.version_info
    passed = (current.major, current.minor) >= (min_major, min_minor)
    return {
        "installed_version": f"{current.major}.{current.minor}.{current.micro}",
        "minimum_required": f"{min_major}.{min_minor}",
        "status": "PASS" if passed else "FAIL",
    }

def check_disk_space(path: str = ".", min_free_gb: float = 2.0) -> Dict[str, Any]:
    usage = shutil.disk_usage(path)
    free_gb = round(usage.free / (1024**3), 2)
    total_gb = round(usage.total / (1024**3), 2)
    return {
        "path": os.path.abspath(path),
        "free_gb": free_gb,
        "total_gb": total_gb,
        "status": "PASS" if free_gb >= min_free_gb else "FAIL",
    }

def check_environment_variables(keys: List[str] = None) -> Dict[str, Any]:
    target_keys = keys or DEFAULT_ENV_VARS
    results = {}
    all_present = True
    for key in target_keys:
        val = os.environ.get(key)
        results[key] = {
            "set": val is not None,
            "value_preview": (val[:30] + "...") if val and len(val) > 30 else val
        }
        if val is None:
            all_present = False
    return {
        "variables": results,
        "status": "PASS" if all_present else "FAIL"
    }

def check_developer_tools(tools: List[str] = None) -> Dict[str, Any]:
    tool_list = tools or DEFAULT_REQUIRED_TOOLS
    tool_status = {}
    all_found = True
    for tool in tool_list:
        path = shutil.which(tool)
        version = None
        if path:
            try:
                proc = subprocess.run(
                    [tool, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                version = (proc.stdout or proc.stderr).strip().split("\n")[0]
            except Exception:
                version = "Version check timed out or failed"
        else:
            all_found = False

        tool_status[tool] = {
            "found": path is not None,
            "path": path,
            "version": version,
        }
    return {
        "tools": tool_status,
        "status": "PASS" if all_found else "FAIL",
    }

def run_diagnostics(config_path: str = None) -> Dict[str, Any]:
    tools = DEFAULT_REQUIRED_TOOLS
    if config_path:
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        with open(config_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            if not lines:
                raise ValueError(f"Malformed configuration file: {config_path} contains no valid rules")
            tools = lines

    py = check_python_version()
    disk = check_disk_space()
    env = check_environment_variables()
    tool_checks = check_developer_tools(tools)

    passed = all(
        section["status"] == "PASS"
        for section in [py, disk, env, tool_checks]
    )

    return {
        "system": {
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
        "python": py,
        "disk": disk,
        "environment": env,
        "tools": tool_checks,
        "overall_status": "PASS" if passed else "FAIL",
    }