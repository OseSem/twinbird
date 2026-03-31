from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import typer


def _task_name(name: str) -> str:
    return f"twinbird-{name}"


def _build_netbird_cmd(
    netbird_bin: str,
    config_dir: Path,
    daemon_addr: str,
    log_file: Path,
) -> list[str]:
    return [
        netbird_bin,
        "service",
        "run",
        "--config",
        str(config_dir / "config.json"),
        "--daemon-addr",
        daemon_addr,
        "--log-file",
        str(log_file),
    ]


def register_service(
    name: str,
    netbird_bin: str,
    config_dir: Path,
    daemon_addr: str,
    log_file: Path,
) -> None:
    if sys.platform == "win32":
        _register_windows(name, netbird_bin, config_dir, daemon_addr, log_file)
    elif sys.platform == "darwin":
        _register_macos(name, netbird_bin, config_dir, daemon_addr, log_file)
    else:
        _register_linux(name, netbird_bin, config_dir, daemon_addr, log_file)


def unregister_service(name: str) -> None:
    if sys.platform == "win32":
        _unregister_windows(name)
    elif sys.platform == "darwin":
        _unregister_macos(name)
    else:
        _unregister_linux(name)


def is_service_registered(name: str) -> bool:
    if sys.platform == "win32":
        return _is_registered_windows(name)
    elif sys.platform == "darwin":
        return _is_registered_macos(name)
    else:
        return _is_registered_linux(name)


# --- Windows: Task Scheduler ---


def _register_windows(
    name: str,
    netbird_bin: str,
    config_dir: Path,
    daemon_addr: str,
    log_file: Path,
) -> None:
    parts = _build_netbird_cmd(netbird_bin, config_dir, daemon_addr, log_file)
    cmd_str = " ".join(f'"{part}"' for part in parts)
    result = subprocess.run(
        [
            "schtasks",
            "/create",
            "/tn",
            _task_name(name),
            "/tr",
            cmd_str,
            "/sc",
            "ONLOGON",
            "/f",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        typer.echo(
            f"Warning: failed to register service for '{name}': {result.stderr}",
            err=True,
        )


def _unregister_windows(name: str) -> None:
    subprocess.run(
        ["schtasks", "/delete", "/tn", _task_name(name), "/f"],
        capture_output=True,
        text=True,
        check=False,
    )


def _is_registered_windows(name: str) -> bool:
    result = subprocess.run(
        ["schtasks", "/query", "/tn", _task_name(name)],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


# --- Linux: systemd user unit ---
# (stub — implemented in Task 3)


def _register_linux(
    name: str,
    netbird_bin: str,
    config_dir: Path,
    daemon_addr: str,
    log_file: Path,
) -> None:
    pass


def _unregister_linux(name: str) -> None:
    pass


def _is_registered_linux(name: str) -> bool:
    return False


# --- macOS: launchd user agent ---
# (stub — implemented in Task 4)


def _register_macos(
    name: str,
    netbird_bin: str,
    config_dir: Path,
    daemon_addr: str,
    log_file: Path,
) -> None:
    pass


def _unregister_macos(name: str) -> None:
    pass


def _is_registered_macos(name: str) -> bool:
    return False
