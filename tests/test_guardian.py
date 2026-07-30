"""Unit tests for guardian.py monitoring engine."""
import unittest
from unittest.mock import patch, MagicMock
from wifi_ac_guardian.core.models import (
    GuardianConfig,
    LinkInfo,
    PhyMode,
    StatusState,
)
from wifi_ac_guardian.core.guardian import WifiACGuardian


class TestGuardian(unittest.TestCase):
    def setUp(self):
        self.config = GuardianConfig(
            interface="wlp3s0",
            check_interval=1.0,
            reconnect_delay=0.01,
            max_attempts=3,
            enable_tray=False,
            enable_notifications=False
        )
        self.patcher = patch("wifi_ac_guardian.config.load_config", return_value=self.config)
        self.mock_load_config = self.patcher.start()
        self.guardian = WifiACGuardian(config=self.config)

    def tearDown(self):
        self.patcher.stop()

    @patch("wifi_ac_guardian.core.detector.WifiDetector.get_link_info")
    def test_perform_check_good_vht(self, mock_get_link):
        mock_get_link.return_value = LinkInfo(
            connected=True,
            interface="wlp3s0",
            ssid="lab5g",
            phy_mode=PhyMode.VHT,
            tx_bitrate="866.7 MBit/s VHT-MCS 9"
        )

        link = self.guardian.perform_check()
        self.assertTrue(link.is_good)
        self.assertEqual(self.guardian.state.status, StatusState.GOOD)
        self.assertEqual(self.guardian.state.attempts_count, 0)

    @patch("wifi_ac_guardian.core.reconnector.WifiReconnector.trigger_reconnect")
    @patch("wifi_ac_guardian.core.detector.WifiDetector.get_link_info")
    def test_perform_check_downgraded_ht_triggers_reconnect(self, mock_get_link, mock_reconnect):
        # Initial link returns Wi-Fi 4 (HT)
        initial_link = LinkInfo(
            connected=True,
            interface="wlp3s0",
            ssid="lab5g",
            phy_mode=PhyMode.HT,
            tx_bitrate="270.0 MBit/s MCS 14"
        )
        mock_get_link.return_value = initial_link

        # Reconnect succeeds back to VHT
        reconnected_link = LinkInfo(
            connected=True,
            interface="wlp3s0",
            ssid="lab5g",
            phy_mode=PhyMode.VHT,
            tx_bitrate="866.7 MBit/s VHT-MCS 9"
        )
        mock_reconnect.return_value = reconnected_link

        link = self.guardian.perform_check()
        self.assertEqual(self.guardian.state.status, StatusState.GOOD)
        mock_reconnect.assert_called_once()

    @patch("wifi_ac_guardian.core.reconnector.WifiReconnector.trigger_reconnect")
    @patch("wifi_ac_guardian.core.detector.WifiDetector.get_link_info")
    def test_max_attempts_exceeded(self, mock_get_link, mock_reconnect):
        ht_link = LinkInfo(
            connected=True,
            interface="wlp3s0",
            ssid="lab5g",
            phy_mode=PhyMode.HT,
            tx_bitrate="270.0 MBit/s MCS 14"
        )
        mock_get_link.return_value = ht_link
        mock_reconnect.return_value = ht_link

        # Pre-set attempt count to max_attempts (3)
        self.guardian.state.attempts_count = 3
        from datetime import datetime
        self.guardian.state.last_reconnect = datetime.now()

        link = self.guardian.perform_check()
        self.assertEqual(self.guardian.state.status, StatusState.FAILED)
        mock_reconnect.assert_not_called()

    @patch("wifi_ac_guardian.core.reconnector.WifiReconnector.trigger_reconnect")
    @patch("wifi_ac_guardian.core.detector.WifiDetector.get_link_info")
    def test_unlimited_max_attempts_zero(self, mock_get_link, mock_reconnect):
        ht_link = LinkInfo(
            connected=True,
            interface="wlp3s0",
            ssid="lab5g",
            phy_mode=PhyMode.HT,
            tx_bitrate="270.0 MBit/s MCS 14"
        )
        mock_get_link.return_value = ht_link
        mock_reconnect.return_value = ht_link

        self.guardian.config.max_attempts = 0
        self.guardian.state.attempts_count = 50

        link = self.guardian.perform_check()
        mock_reconnect.assert_called_once()
        self.assertEqual(self.guardian.state.attempts_count, 51)


if __name__ == "__main__":
    unittest.main()
