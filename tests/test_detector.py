"""Unit tests for Windows Wi-Fi detector and LinkInfo quality threshold evaluation."""
import unittest
from unittest.mock import patch, MagicMock
from wifi_ac_guardian_win.core.models import LinkInfo, PhyMode, GuardianConfig
from wifi_ac_guardian_win.core.detector_win import parse_netsh_output, WifiDetectorWin
from wifi_ac_guardian.core.detector import calculate_channel, WifiLinkParser
from wifi_ac_guardian.core.models import PhyMode as LinuxPhyMode


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

    def test_calculate_channel_6ghz(self):
        self.assertEqual(calculate_channel(5955.0), 1)
        self.assertEqual(calculate_channel(6115.0), 33)

    def test_parse_vht_link_output(self):
        raw_output = """Connected to 08:5c:1b:17:7d:80 (on wlp3s0)
\tSSID: HomeNetwork5G
\tfreq: 5805.0
\tRX: 1386618 bytes
\tTX: 2928666 bytes
\tsignal: -45 dBm
\trx bitrate: 866.7 MBit/s VHT-MCS 9 80MHz short GI VHT-NSS 2
\ttx bitrate: 866.7 MBit/s VHT-MCS 9 80MHz short GI VHT-NSS 2
"""
        info = WifiLinkParser.parse_link_output(raw_output, interface="wlp3s0")
        self.assertTrue(info.connected)
        self.assertEqual(info.ssid, "HomeNetwork5G")
        self.assertEqual(info.bssid, "08:5C:1B:17:7D:80")
        self.assertEqual(info.freq_mhz, 5805.0)
        self.assertEqual(info.channel, 161)
        self.assertEqual(info.signal_dbm, -45)
        self.assertEqual(info.phy_mode, LinuxPhyMode.VHT)
        self.assertTrue(info.is_good)

    def test_parse_ht_wifi4_link_output(self):
        raw_output = """Connected to 08:5c:1b:17:7d:80 (on wlp3s0)
\tSSID: lab24g
\tfreq: 2412.0
\tsignal: -44 dBm
\trx bitrate: 144.4 MBit/s MCS 15 short GI
\ttx bitrate: 270.0 MBit/s MCS 14 40MHz short GI
"""
        info = WifiLinkParser.parse_link_output(raw_output, interface="wlp3s0")
        self.assertTrue(info.connected)
        self.assertEqual(info.ssid, "lab24g")
        self.assertEqual(info.phy_mode, LinuxPhyMode.HT)
        self.assertFalse(info.is_good)

    def test_parse_he_wifi6_link_output(self):
        raw_output = """Connected to 11:22:33:44:55:66 (on wlp3s0)
\tSSID: UltraWifi6
\tfreq: 5200.0
\tsignal: -35 dBm
\ttx bitrate: 1201.0 MBit/s HE-MCS 11 80MHz HE-NSS 2
"""
        info = WifiLinkParser.parse_link_output(raw_output, interface="wlp3s0")
        self.assertTrue(info.connected)
        self.assertEqual(info.phy_mode, LinuxPhyMode.HE)
        self.assertTrue(info.is_good)

    def test_parse_eht_wifi7_link_output(self):
        raw_output = """Connected to 11:22:33:44:55:66 (on wlp3s0)
\tSSID: NextGenWifi7
\tfreq: 6115.0
\tsignal: -30 dBm
\ttx bitrate: 2400.0 MBit/s EHT-MCS 12 160MHz
"""
        info = WifiLinkParser.parse_link_output(raw_output, interface="wlp3s0")
        self.assertTrue(info.connected)
        self.assertEqual(info.phy_mode, LinuxPhyMode.EHT)
        self.assertTrue(info.is_good)

    def test_parse_disconnected_link_output(self):
        raw_output = "Not connected."
        info = WifiLinkParser.parse_link_output(raw_output, interface="wlp3s0")
        self.assertFalse(info.connected)
        self.assertEqual(info.phy_mode, LinuxPhyMode.DISCONNECTED)
        self.assertFalse(info.is_good)


if __name__ == "__main__":
    unittest.main()
