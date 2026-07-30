"""Unit tests for models.py dataclasses and enums."""
import unittest
from wifi_ac_guardian.core.models import (
    LinkInfo,
    PhyMode,
    StatusState,
    GuardianConfig,
    GuardianState,
)


class TestModels(unittest.TestCase):
    def test_link_info_is_good_vht(self):
        link = LinkInfo(connected=True, phy_mode=PhyMode.VHT)
        self.assertTrue(link.is_good)

    def test_link_info_is_good_he_eht(self):
        link_he = LinkInfo(connected=True, phy_mode=PhyMode.HE)
        self.assertTrue(link_he.is_good)

        link_eht = LinkInfo(connected=True, phy_mode=PhyMode.EHT)
        self.assertTrue(link_eht.is_good)

    def test_link_info_is_not_good_ht(self):
        link_ht = LinkInfo(connected=True, phy_mode=PhyMode.HT)
        self.assertFalse(link_ht.is_good)

        link_legacy = LinkInfo(connected=True, phy_mode=PhyMode.LEGACY)
        self.assertFalse(link_legacy.is_good)

    def test_link_info_disconnected(self):
        link = LinkInfo(connected=False, phy_mode=PhyMode.DISCONNECTED)
        self.assertFalse(link.is_good)

    def test_guardian_config_defaults(self):
        config = GuardianConfig()
        self.assertEqual(config.check_interval, 10.0)
        self.assertEqual(config.reconnect_delay, 2.0)
        self.assertEqual(config.max_attempts, 10)


if __name__ == "__main__":
    unittest.main()
