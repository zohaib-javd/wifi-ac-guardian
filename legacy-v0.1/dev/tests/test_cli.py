"""Unit tests for cli.py."""
import unittest
from unittest.mock import patch, MagicMock
from wifi_ac_guardian.cli import main, print_status_report
from wifi_ac_guardian.core.models import LinkInfo, PhyMode


class TestCLI(unittest.TestCase):
    @patch("wifi_ac_guardian.core.detector.WifiDetector.get_link_info")
    def test_print_status_report_connected(self, mock_get_link):
        mock_get_link.return_value = LinkInfo(
            connected=True,
            interface="wlp3s0",
            ssid="lab5g",
            bssid="08:5C:1B:17:7D:80",
            freq_mhz=5805.0,
            channel=161,
            signal_dbm=-44,
            phy_mode=PhyMode.VHT,
            tx_bitrate="866.7 MBit/s VHT-MCS 9"
        )
        # Verify call succeeds without exception
        print_status_report(interface_override="wlp3s0")

    def test_cli_version_flag(self):
        with self.assertRaises(SystemExit) as cm:
            main(["--version"])
        self.assertEqual(cm.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
