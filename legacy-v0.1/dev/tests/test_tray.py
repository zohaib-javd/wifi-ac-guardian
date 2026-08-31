"""Unit tests for tray.py system tray interface."""
import unittest
from unittest.mock import patch, MagicMock
from wifi_ac_guardian.core.models import GuardianConfig, StatusState, LinkInfo, PhyMode
from wifi_ac_guardian.tray import SystemTrayApp


class TestSystemTrayApp(unittest.TestCase):
    def setUp(self):
        self.config = GuardianConfig(enable_tray=True)
        self.mock_quit_cb = MagicMock()
        self.mock_reconnect_cb = MagicMock()
        self.app = SystemTrayApp(
            on_reconnect_click=self.mock_reconnect_cb,
            on_quit_click=self.mock_quit_cb,
            config=self.config
        )

    def test_tray_initialization(self):
        self.assertEqual(self.app.current_state, StatusState.IDLE)
        self.assertIsNotNone(self.app.config)

    @patch("subprocess.run")
    def test_handle_quit_triggers_callbacks_and_stops(self, mock_run):
        mock_icon = MagicMock()
        self.app.icon_instance = mock_icon

        self.app._handle_quit()

        self.mock_quit_cb.assert_called_once()
        mock_icon.stop.assert_called_once()
        mock_run.assert_called()


if __name__ == "__main__":
    unittest.main()
