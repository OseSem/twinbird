from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch


class TestWindowsRegister:
    def test_creates_scheduled_task(self) -> None:
        from twinbird.service import register_service

        mock_run = MagicMock(return_value=MagicMock(returncode=0))
        with (
            patch("twinbird.service.sys.platform", "win32"),
            patch("twinbird.service.subprocess.run", mock_run),
        ):
            register_service(
                name="office",
                netbird_bin="C:/Program Files/netbird/netbird.exe",
                config_dir=Path("C:/Users/user/AppData/Roaming/twinbird/office"),
                daemon_addr="tcp://127.0.0.1:52200",
                log_file=Path(
                    "C:/Users/user/AppData/Roaming/twinbird/office/daemon.log"
                ),
            )

        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "schtasks"
        assert "/create" in cmd
        assert "twinbird-office" in cmd
        assert "/sc" in cmd
        assert "ONLOGON" in cmd

    def test_register_warns_on_failure(self, capsys) -> None:
        from twinbird.service import register_service

        mock_run = MagicMock(
            return_value=MagicMock(returncode=1, stderr="access denied")
        )
        with (
            patch("twinbird.service.sys.platform", "win32"),
            patch("twinbird.service.subprocess.run", mock_run),
        ):
            register_service(
                name="office",
                netbird_bin="netbird",
                config_dir=Path("/tmp/twinbird/office"),
                daemon_addr="tcp://127.0.0.1:52200",
                log_file=Path("/tmp/twinbird/office/daemon.log"),
            )
        captured = capsys.readouterr()
        assert "Warning" in captured.err


class TestWindowsUnregister:
    def test_deletes_scheduled_task(self) -> None:
        from twinbird.service import unregister_service

        mock_run = MagicMock(return_value=MagicMock(returncode=0))
        with (
            patch("twinbird.service.sys.platform", "win32"),
            patch("twinbird.service.subprocess.run", mock_run),
        ):
            unregister_service("office")

        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "schtasks"
        assert "/delete" in cmd
        assert "twinbird-office" in cmd
        assert "/f" in cmd

    def test_unregister_idempotent(self) -> None:
        from twinbird.service import unregister_service

        mock_run = MagicMock(return_value=MagicMock(returncode=1, stderr="not found"))
        with (
            patch("twinbird.service.sys.platform", "win32"),
            patch("twinbird.service.subprocess.run", mock_run),
        ):
            unregister_service("office")  # should not raise


class TestWindowsIsRegistered:
    def test_returns_true_when_exists(self) -> None:
        from twinbird.service import is_service_registered

        mock_run = MagicMock(return_value=MagicMock(returncode=0))
        with (
            patch("twinbird.service.sys.platform", "win32"),
            patch("twinbird.service.subprocess.run", mock_run),
        ):
            assert is_service_registered("office") is True

    def test_returns_false_when_missing(self) -> None:
        from twinbird.service import is_service_registered

        mock_run = MagicMock(return_value=MagicMock(returncode=1))
        with (
            patch("twinbird.service.sys.platform", "win32"),
            patch("twinbird.service.subprocess.run", mock_run),
        ):
            assert is_service_registered("office") is False


class TestLinuxRegister:
    def test_writes_unit_file_and_enables(self, tmp_path: Path) -> None:
        from twinbird.service import register_service

        unit_dir = tmp_path / ".config" / "systemd" / "user"
        mock_run = MagicMock(return_value=MagicMock(returncode=0))

        with (
            patch("twinbird.service.sys.platform", "linux"),
            patch("twinbird.service.Path.home", return_value=tmp_path),
            patch("twinbird.service.subprocess.run", mock_run),
        ):
            register_service(
                name="office",
                netbird_bin="/usr/bin/netbird",
                config_dir=Path("/home/user/.config/twinbird/office"),
                daemon_addr="unix:///home/user/.config/twinbird/office/office.sock",
                log_file=Path("/home/user/.config/twinbird/office/daemon.log"),
            )

        unit_file = unit_dir / "twinbird-office.service"
        assert unit_file.exists()
        content = unit_file.read_text()
        assert "ExecStart=/usr/bin/netbird service run" in content
        assert (
            "--daemon-addr unix:///home/user/.config/twinbird/office/office.sock"
            in content
        )
        assert "WantedBy=default.target" in content

        assert mock_run.call_count == 2  # daemon-reload + enable
        cmds = [c[0][0] for c in mock_run.call_args_list]
        assert ["systemctl", "--user", "daemon-reload"] in cmds
        assert ["systemctl", "--user", "enable", "twinbird-office.service"] in cmds

    def test_register_warns_on_failure(self, tmp_path: Path, capsys) -> None:
        from twinbird.service import register_service

        mock_run = MagicMock(
            return_value=MagicMock(returncode=1, stderr="Failed to enable")
        )
        with (
            patch("twinbird.service.sys.platform", "linux"),
            patch("twinbird.service.Path.home", return_value=tmp_path),
            patch("twinbird.service.subprocess.run", mock_run),
        ):
            register_service(
                name="office",
                netbird_bin="/usr/bin/netbird",
                config_dir=Path("/tmp/twinbird/office"),
                daemon_addr="unix:///tmp/office.sock",
                log_file=Path("/tmp/twinbird/office/daemon.log"),
            )
        captured = capsys.readouterr()
        assert "Warning" in captured.err


class TestLinuxUnregister:
    def test_disables_and_removes_unit_file(self, tmp_path: Path) -> None:
        from twinbird.service import unregister_service

        unit_dir = tmp_path / ".config" / "systemd" / "user"
        unit_dir.mkdir(parents=True)
        unit_file = unit_dir / "twinbird-office.service"
        unit_file.write_text("[Unit]\nDescription=test\n")

        mock_run = MagicMock(return_value=MagicMock(returncode=0))
        with (
            patch("twinbird.service.sys.platform", "linux"),
            patch("twinbird.service.Path.home", return_value=tmp_path),
            patch("twinbird.service.subprocess.run", mock_run),
        ):
            unregister_service("office")

        assert not unit_file.exists()
        cmds = [c[0][0] for c in mock_run.call_args_list]
        assert ["systemctl", "--user", "disable", "twinbird-office.service"] in cmds
        assert ["systemctl", "--user", "daemon-reload"] in cmds

    def test_unregister_idempotent_no_file(self, tmp_path: Path) -> None:
        from twinbird.service import unregister_service

        mock_run = MagicMock(return_value=MagicMock(returncode=0))
        with (
            patch("twinbird.service.sys.platform", "linux"),
            patch("twinbird.service.Path.home", return_value=tmp_path),
            patch("twinbird.service.subprocess.run", mock_run),
        ):
            unregister_service("office")  # should not raise


class TestLinuxIsRegistered:
    def test_returns_true_when_enabled(self) -> None:
        from twinbird.service import is_service_registered

        mock_run = MagicMock(return_value=MagicMock(returncode=0))
        with (
            patch("twinbird.service.sys.platform", "linux"),
            patch("twinbird.service.subprocess.run", mock_run),
        ):
            assert is_service_registered("office") is True

    def test_returns_false_when_not_enabled(self) -> None:
        from twinbird.service import is_service_registered

        mock_run = MagicMock(return_value=MagicMock(returncode=1))
        with (
            patch("twinbird.service.sys.platform", "linux"),
            patch("twinbird.service.subprocess.run", mock_run),
        ):
            assert is_service_registered("office") is False


class TestMacosRegister:
    def test_writes_plist_and_loads(self, tmp_path: Path) -> None:
        from twinbird.service import register_service

        launch_agents = tmp_path / "Library" / "LaunchAgents"
        mock_run = MagicMock(return_value=MagicMock(returncode=0))

        with (
            patch("twinbird.service.sys.platform", "darwin"),
            patch("twinbird.service.Path.home", return_value=tmp_path),
            patch("twinbird.service.subprocess.run", mock_run),
        ):
            register_service(
                name="office",
                netbird_bin="/usr/local/bin/netbird",
                config_dir=Path("/Users/user/.config/twinbird/office"),
                daemon_addr="unix:///Users/user/.config/twinbird/office/office.sock",
                log_file=Path("/Users/user/.config/twinbird/office/daemon.log"),
            )

        plist = launch_agents / "com.twinbird.office.plist"
        assert plist.exists()
        content = plist.read_text()
        assert "<key>Label</key>" in content
        assert "<string>com.twinbird.office</string>" in content
        assert "<string>/usr/local/bin/netbird</string>" in content
        assert "<key>RunAtLoad</key>" in content

        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "launchctl"
        assert "load" in cmd

    def test_register_warns_on_failure(self, tmp_path: Path, capsys) -> None:
        from twinbird.service import register_service

        mock_run = MagicMock(
            return_value=MagicMock(returncode=1, stderr="permission denied")
        )
        with (
            patch("twinbird.service.sys.platform", "darwin"),
            patch("twinbird.service.Path.home", return_value=tmp_path),
            patch("twinbird.service.subprocess.run", mock_run),
        ):
            register_service(
                name="office",
                netbird_bin="/usr/local/bin/netbird",
                config_dir=Path("/tmp/twinbird/office"),
                daemon_addr="unix:///tmp/office.sock",
                log_file=Path("/tmp/twinbird/office/daemon.log"),
            )
        captured = capsys.readouterr()
        assert "Warning" in captured.err


class TestMacosUnregister:
    def test_unloads_and_removes_plist(self, tmp_path: Path) -> None:
        from twinbird.service import unregister_service

        launch_agents = tmp_path / "Library" / "LaunchAgents"
        launch_agents.mkdir(parents=True)
        plist = launch_agents / "com.twinbird.office.plist"
        plist.write_text("<plist>test</plist>")

        mock_run = MagicMock(return_value=MagicMock(returncode=0))
        with (
            patch("twinbird.service.sys.platform", "darwin"),
            patch("twinbird.service.Path.home", return_value=tmp_path),
            patch("twinbird.service.subprocess.run", mock_run),
        ):
            unregister_service("office")

        assert not plist.exists()
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "launchctl"
        assert cmd[1] == "unload"

    def test_unregister_idempotent_no_plist(self, tmp_path: Path) -> None:
        from twinbird.service import unregister_service

        mock_run = MagicMock(return_value=MagicMock(returncode=0))
        with (
            patch("twinbird.service.sys.platform", "darwin"),
            patch("twinbird.service.Path.home", return_value=tmp_path),
            patch("twinbird.service.subprocess.run", mock_run),
        ):
            unregister_service("office")  # should not raise


class TestMacosIsRegistered:
    def test_returns_true_when_plist_exists(self, tmp_path: Path) -> None:
        from twinbird.service import is_service_registered

        launch_agents = tmp_path / "Library" / "LaunchAgents"
        launch_agents.mkdir(parents=True)
        (launch_agents / "com.twinbird.office.plist").write_text("<plist/>")

        with (
            patch("twinbird.service.sys.platform", "darwin"),
            patch("twinbird.service.Path.home", return_value=tmp_path),
        ):
            assert is_service_registered("office") is True

    def test_returns_false_when_no_plist(self, tmp_path: Path) -> None:
        from twinbird.service import is_service_registered

        with (
            patch("twinbird.service.sys.platform", "darwin"),
            patch("twinbird.service.Path.home", return_value=tmp_path),
        ):
            assert is_service_registered("office") is False
