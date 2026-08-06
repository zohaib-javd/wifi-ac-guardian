"""Unit tests for Target SSID Lock and GuardianConfig."""
import unittest
from wifi_ac_guardian_win.core.models import GuardianConfig, LinkInfo, PhyMode


class TestTargetSSIDLock(unittest.TestCase):
    def test_guardian_config_target_ssid(self):
        config = GuardianConfig(target_ssid="lab5g", max_attempts=25, check_interval=15.0)
        self.assertEqual(config.target_ssid, "lab5g")
        self.assertEqual(config.max_attempts, 25)
        self.assertEqual(config.check_interval, 15.0)

    def test_link_info_target_ssid_matching(self):
        link_lab5g = LinkInfo(connected=True, ssid="lab5g", phy_mode=PhyMode.VHT, tx_bitrate="866.7 Mbps")
        self.assertTrue(link_lab5g.is_good)
        self.assertEqual(link_lab5g.ssid.lower(), "lab5g")


if __name__ == "__main__":
    unittest.main()
