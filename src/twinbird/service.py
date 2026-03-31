from __future__ import annotations

import shlex
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


def _systemd_unit_dir() -> Path:
    return Path.home() / ".config" / "systemd" / "user"


def _systemd_unit_path(name: str) -> Path:
    return _systemd_unit_dir() / f"twinbird-{name}.service"


_SYSTEMD_UNIT_TEMPLATE = """\
[Unit]
Description=Twinbird instance: {name}

[Service]
ExecStart={exec_start}
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
"""


def _register_linux(
    name: str,
    netbird_bin: str,
    config_dir: Path,
    daemon_addr: str,
    log_file: Path,
) -> None:
    unit_dir = _systemd_unit_dir()
    unit_dir.mkdir(parents=True, exist_ok=True)

    cmd_parts = _build_netbird_cmd(netbird_bin, config_dir, daemon_addr, log_file)
    exec_start = " ".join(shlex.quote(part) for part in cmd_parts)

    unit_path = _systemd_unit_path(name)
    unit_path.write_text(
        _SYSTEMD_UNIT_TEMPLATE.format(name=name, exec_start=exec_start)
    )

    reload_result = subprocess.run(
        ["systemctl", "--user", "daemon-reload"],
        capture_output=True,
        text=True,
        check=False,
    )
    enable_result = subprocess.run(
        ["systemctl", "--user", "enable", f"twinbird-{name}.service"],
        capture_output=True,
        text=True,
        check=False,
    )
    if reload_result.returncode != 0 or enable_result.returncode != 0:
        stderr = " | ".join(
            s for s in (reload_result.stderr, enable_result.stderr) if s
        )
        typer.echo(
            f"Warning: failed to register service for '{name}': {stderr}",
            err=True,
        )


def _unregister_linux(name: str) -> None:
    subprocess.run(
        ["systemctl", "--user", "disable", f"twinbird-{name}.service"],
        capture_output=True,
        text=True,
        check=False,
    )
    unit_path = _systemd_unit_path(name)
    if unit_path.exists():
        unit_path.unlink()
    subprocess.run(
        ["systemctl", "--user", "daemon-reload"],
        capture_output=True,
        text=True,
        check=False,
    )


def _is_registered_linux(name: str) -> bool:
    result = subprocess.run(
        ["systemctl", "--user", "is-enabled", f"twinbird-{name}.service"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


# --- macOS: launchd user agent ---


def _launchd_plist_dir() -> Path:
    return Path.home() / "Library" / "LaunchAgents"


def _launchd_plist_path(name: str) -> Path:
    return _launchd_plist_dir() / f"com.twinbird.{name}.plist"


_LAUNCHD_PLIST_TEMPLATE = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" \
"http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.twinbird.{name}</string>
    <key>ProgramArguments</key>
    <array>
{program_arguments}
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{log_file}</string>
    <key>StandardErrorPath</key>
    <string>{log_file}</string>
</dict>
</plist>
"""


def _register_macos(
    name: str,
    netbird_bin: str,
    config_dir: Path,
    daemon_addr: str,
    log_file: Path,
) -> None:
    plist_dir = _launchd_plist_dir()
    plist_dir.mkdir(parents=True, exist_ok=True)

    cmd_parts = _build_netbird_cmd(netbird_bin, config_dir, daemon_addr, log_file)
    program_arguments = "\n".join(
        f"        <string>{part}</string>" for part in cmd_parts
    )

    plist_path = _launchd_plist_path(name)
    plist_path.write_text(
        _LAUNCHD_PLIST_TEMPLATE.format(
            name=name,
            program_arguments=program_arguments,
            log_file=str(log_file),
        )
    )

    result = subprocess.run(
        ["launchctl", "load", str(plist_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        typer.echo(
            f"Warning: failed to register service for '{name}': {result.stderr}",
            err=True,
        )


def _unregister_macos(name: str) -> None:
    plist_path = _launchd_plist_path(name)
    if plist_path.exists():
        subprocess.run(
            ["launchctl", "unload", str(plist_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        plist_path.unlink()


def _is_registered_macos(name: str) -> bool:
    return _launchd_plist_path(name).exists()
