"""Unit tests for reconnector.py module."""
import unittest
from unittest.mock import patch, MagicMock
from wifi_ac_guardian.core.models import GuardianConfig, LinkInfo, PhyMode
from wifi_ac_guardian.core.reconnector import WifiReconnector


class TestReconnector(unittest.TestCase):
    def setUp(self):
        self.config = GuardianConfig(reconnect_delay=0.1)
        self.reconnector = WifiReconnector(config=self.config)

    @patch("subprocess.run")
    def test_disconnect_interface_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        res = self.reconnector._disconnect_interface("wlp3s0", ssid="test_ssid")
        self.assertTrue(res)
        mock_run.assert_called()

    @patch("wifi_ac_guardian.core.detector.WifiDetector.get_link_info")
    @patch("subprocess.run")
    def test_trigger_reconnect_flow(self, mock_run, mock_get_link):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        mock_get_link.return_value = LinkInfo(
            connected=True,
            interface="wlp3s0",
            ssid="lab5g",
            phy_mode=PhyMode.VHT
        )

        res_link = self.reconnector.trigger_reconnect("wlp3s0", ssid="lab5g")
        self.assertTrue(res_link.connected)
        self.assertEqual(res_link.phy_mode, PhyMode.VHT)


if __name__ == "__main__":
    unittest.main()
