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
