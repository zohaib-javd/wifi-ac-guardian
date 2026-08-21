"""Unit tests for Windows Wi-Fi hardware adapter reset (Disable-NetAdapter / Enable-NetAdapter) and reconnector."""
import unittest
from unittest.mock import patch, MagicMock
from wifi_ac_guardian_win.core.models import GuardianConfig, LinkInfo, PhyMode
from wifi_ac_guardian_win.core.reconnector_win import WifiReconnectorWin


class TestWifiReconnector(unittest.TestCase):
    @patch("subprocess.run")
    @patch("time.sleep")
    def test_hardware_adapter_reset_sequence(self, mock_sleep, mock_subproc):
        # Mock subprocess.run to simulate PowerShell Disable/Enable NetAdapter success
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = "Success"
        mock_subproc.return_value = mock_res

        config = GuardianConfig(reconnect_delay=1.0)
        reconnector = WifiReconnectorWin(config=config)

        # Mock detector.get_link_info to return connected GOOD link
        reconnector.detector.get_link_info = MagicMock(return_value=LinkInfo(
            connected=True,
            ssid="lab5g",
            phy_mode=PhyMode.VHT,
            tx_bitrate="866.7 Mbps"
        ))

        res_link = reconnector.trigger_reconnect(interface="Wi-Fi", ssid="lab5g")
        self.assertTrue(res_link.is_good)

        # Verify subprocess was called for Disable-NetAdapter and Enable-NetAdapter
        cmd_strings = [" ".join(call.args[0]) if isinstance(call.args[0], list) else str(call.args[0]) for call in mock_subproc.call_args_list]
        self.assertTrue(any("Disable-NetAdapter" in cmd for cmd in cmd_strings))
        self.assertTrue(any("Enable-NetAdapter" in cmd for cmd in cmd_strings))
        self.assertTrue(any("netsh wlan connect" in cmd for cmd in cmd_strings))


if __name__ == "__main__":
    unittest.main()
