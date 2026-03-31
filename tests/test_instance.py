from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from twinbird.config import (
    InstanceMetadata,
    ensure_instance_dir,
    read_metadata,
    write_metadata,
    write_pid,
)
from twinbird.platform import PlatformConfig


def _mock_platform(tmp_path: Path) -> PlatformConfig:
    return PlatformConfig(config_root=tmp_path, interface_prefix="wt")


class TestUp:
    def test_starts_and_connects(self, tmp_path: Path) -> None:
        from twinbird.instance import up

        platform = _mock_platform(tmp_path)

        with (
            patch("twinbird.instance.get_platform_config", return_value=platform),
            patch("twinbird.instance.find_netbird_bin", return_value="netbird"),
            patch("twinbird.instance.start_daemon", return_value=42),
            patch("twinbird.instance.read_pid", return_value=None),
            patch(
                "twinbird.instance.run_up",
                return_value=MagicMock(returncode=0, stdout="Connected"),
            ),
            patch(
                "twinbird.instance.derive_daemon_addr",
                return_value="tcp://127.0.0.1:52200",
            ),
            patch("twinbird.instance.derive_interface_name", return_value="wt7"),
        ):
            up(
                name="office",
                management_url="https://mgmt.example.com",
                setup_key="KEY123",
            )

        metadata = read_metadata(tmp_path, "office")
        assert metadata is not None
        assert metadata.name == "office"
        assert metadata.pid == 42

    def test_already_running(self, tmp_path: Path, capsys) -> None:
        from twinbird.instance import up

        platform = _mock_platform(tmp_path)
        ensure_instance_dir(tmp_path, "office")
        write_pid(tmp_path, "office", 42)
        meta = InstanceMetadata("office", "url", "addr", "wt7", 42, "t")
        write_metadata(tmp_path, meta)

        with (
            patch("twinbird.instance.get_platform_config", return_value=platform),
            patch("twinbird.instance.find_netbird_bin", return_value="netbird"),
            patch("twinbird.instance.is_process_alive", return_value=True),
            patch("twinbird.instance.read_pid", return_value=42),
        ):
            up(
                name="office",
                management_url="https://mgmt.example.com",
                setup_key="KEY123",
            )

        captured = capsys.readouterr()
        assert "already running" in captured.out


class TestDown:
    def test_stops_instance(self, tmp_path: Path) -> None:
        from twinbird.instance import down

        platform = _mock_platform(tmp_path)
        ensure_instance_dir(tmp_path, "office")
        meta = InstanceMetadata(
            "office", "url", "tcp://127.0.0.1:52200", "wt7", 42, "t"
        )
        write_metadata(tmp_path, meta)
        write_pid(tmp_path, "office", 42)

        with (
            patch("twinbird.instance.get_platform_config", return_value=platform),
            patch("twinbird.instance.find_netbird_bin", return_value="netbird"),
            patch("twinbird.instance.read_pid", return_value=42),
            patch("twinbird.instance.is_process_alive", return_value=True),
            patch("twinbird.instance.run_down", return_value=MagicMock(returncode=0)),
            patch("twinbird.instance.stop_daemon"),
        ):
            down("office")

    def test_not_found(self, tmp_path: Path) -> None:
        from twinbird.instance import down

        platform = _mock_platform(tmp_path)

        import click

        with patch("twinbird.instance.get_platform_config", return_value=platform):
            try:
                down("nonexistent")
                raise AssertionError("Should have raised SystemExit")
            except (SystemExit, click.exceptions.Exit):
                pass


class TestListAll:
    def test_no_instances(self, tmp_path: Path, capsys) -> None:
        from twinbird.instance import list_all

        platform = _mock_platform(tmp_path)

        with patch("twinbird.instance.get_platform_config", return_value=platform):
            list_all()

        captured = capsys.readouterr()
        assert "No instances found" in captured.out
