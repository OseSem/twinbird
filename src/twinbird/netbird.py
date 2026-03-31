from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def find_netbird_bin() -> str:
    bin_path = os.environ.get("TWINBIRD_NETBIRD_BIN", "netbird")
    if bin_path != "netbird":
        if not shutil.which(bin_path):
            msg = (
                f"netbird binary not found at '{bin_path}'"
                " (set via TWINBIRD_NETBIRD_BIN)."
            )
            raise FileNotFoundError(msg)
    elif shutil.which("netbird") is None:
        msg = "netbird not found on PATH. Install NetBird or set TWINBIRD_NETBIRD_BIN."
        raise FileNotFoundError(msg)
    return bin_path


def run_service(
    netbird_bin: str,
    config_dir: Path,
    daemon_addr: str,
    interface_name: str,
) -> subprocess.Popen[Any]:
    log_file = config_dir / "daemon.log"
    cmd = [
        netbird_bin,
        "service",
        "run",
        "--config",
        str(config_dir),
        "--daemon-addr",
        daemon_addr,
        "--log-file",
        str(log_file),
        "--interface-name",
        interface_name,
    ]

    kwargs: dict[str, Any] = {
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }

    if sys.platform == "win32":
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        DETACHED_PROCESS = 0x00000008
        kwargs["creationflags"] = CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS
    else:
        kwargs["start_new_session"] = True

    return subprocess.Popen(cmd, **kwargs)


def run_up(
    netbird_bin: str,
    daemon_addr: str,
    management_url: str,
    setup_key: str,
) -> subprocess.CompletedProcess[str]:
    cmd = [
        netbird_bin,
        "up",
        "--daemon-addr",
        daemon_addr,
        "--management-url",
        management_url,
        "--setup-key",
        setup_key,
    ]
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def run_down(
    netbird_bin: str,
    daemon_addr: str,
) -> subprocess.CompletedProcess[str]:
    cmd = [netbird_bin, "down", "--daemon-addr", daemon_addr]
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def run_status(
    netbird_bin: str,
    daemon_addr: str,
) -> subprocess.CompletedProcess[str]:
    cmd = [netbird_bin, "status", "--daemon-addr", daemon_addr]
    return subprocess.run(cmd, capture_output=True, text=True, check=False)
