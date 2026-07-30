"""Unit tests for detector.py module and iw link parser."""
import unittest
from wifi_ac_guardian.core.models import PhyMode
from wifi_ac_guardian.core.detector import WifiLinkParser, calculate_channel


class TestDetector(unittest.TestCase):
    def test_calculate_channel_24ghz(self):
        self.assertEqual(calculate_channel(2412.0), 1)
        self.assertEqual(calculate_channel(2437.0), 6)
        self.assertEqual(calculate_channel(2462.0), 11)
        self.assertEqual(calculate_channel(2484.0), 14)

    def test_calculate_channel_5ghz(self):
        self.assertEqual(calculate_channel(5180.0), 36)
        self.assertEqual(calculate_channel(5200.0), 40)
        self.assertEqual(calculate_channel(5805.0), 161)

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
        self.assertEqual(info.phy_mode, PhyMode.VHT)
        self.assertTrue(info.is_good)

    def test_parse_ht_wifi4_link_output(self):
        raw_output = """Connected to 08:5c:1b:17:7d:80 (on wlp3s0)
\tSSID: lab5g
\tfreq: 5805.0
\tsignal: -44 dBm
\trx bitrate: 144.4 MBit/s MCS 15 short GI
\ttx bitrate: 270.0 MBit/s MCS 14 40MHz short GI
"""
        info = WifiLinkParser.parse_link_output(raw_output, interface="wlp3s0")
        self.assertTrue(info.connected)
        self.assertEqual(info.ssid, "lab5g")
        self.assertEqual(info.phy_mode, PhyMode.HT)
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
        self.assertEqual(info.phy_mode, PhyMode.HE)
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
        self.assertEqual(info.phy_mode, PhyMode.EHT)
        self.assertTrue(info.is_good)

    def test_parse_disconnected_link_output(self):
        raw_output = "Not connected."
        info = WifiLinkParser.parse_link_output(raw_output, interface="wlp3s0")
        self.assertFalse(info.connected)
        self.assertEqual(info.phy_mode, PhyMode.DISCONNECTED)
        self.assertFalse(info.is_good)


if __name__ == "__main__":
    unittest.main()
