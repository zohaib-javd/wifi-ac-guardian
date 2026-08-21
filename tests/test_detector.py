"""Unit tests for Windows Wi-Fi detector and LinkInfo quality threshold evaluation."""
import unittest
from unittest.mock import patch, MagicMock
from wifi_ac_guardian_win.core.models import LinkInfo, PhyMode, GuardianConfig
from wifi_ac_guardian_win.core.detector_win import parse_netsh_output, WifiDetectorWin


class TestWifiDetector(unittest.TestCase):
    def test_good_vht_high_bitrate(self):
        sample_output = """
        Name                   : Wi-Fi
        State                  : connected
        SSID                   : lab5g
        BSSID                  : 00:11:22:33:44:55
        Radio type             : 802.11ac
        Channel                : 36
        Signal                 : 95%
        Receive rate (Mbps)    : 866.7
        Transmit rate (Mbps)   : 866.7
        """
        link = parse_netsh_output(sample_output)
        self.assertTrue(link.connected)
        self.assertEqual(link.phy_mode, PhyMode.VHT)
        self.assertGreater(link.max_bitrate_mbps, 300.0)
        self.assertTrue(link.is_good)

    def test_downgraded_ht_low_bitrate(self):
        sample_output = """
        Name                   : Wi-Fi
        State                  : connected
        SSID                   : lab5g
        Radio type             : 802.11n
        Transmit rate (Mbps)   : 144
        Receive rate (Mbps)    : 144
        """
        link = parse_netsh_output(sample_output)
        self.assertTrue(link.connected)
        self.assertEqual(link.phy_mode, PhyMode.HT)
        self.assertLessEqual(link.max_bitrate_mbps, 300.0)
        self.assertFalse(link.is_good)

    def test_downgraded_vht_300mbps_limit(self):
        sample_output = """
        Name                   : Wi-Fi
        State                  : connected
        SSID                   : lab5g
        Radio type             : 802.11ac
        Transmit rate (Mbps)   : 300
        Receive rate (Mbps)    : 300
        """
        link = parse_netsh_output(sample_output)
        self.assertTrue(link.connected)
        self.assertEqual(link.phy_mode, PhyMode.VHT)
        self.assertEqual(link.max_bitrate_mbps, 300.0)
        # Rule: Bitrate must be strictly > 300.0 Mbps to be GOOD
        self.assertFalse(link.is_good)


if __name__ == "__main__":
    unittest.main()
