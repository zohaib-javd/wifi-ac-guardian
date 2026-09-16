"""Guardian state tests for the dashboard's active Connecting presentation."""

import unittest
from unittest.mock import MagicMock

from wifi_ac_guardian_win.core.guardian import WifiACGuardianWin
from wifi_ac_guardian_win.core.models import GuardianConfig, GuardianState, LinkInfo, PhyMode, RadioState


class TestGuardianRecoveryState(unittest.TestCase):
    def test_approved_phy_stops_recovery_even_when_bitrate_temporarily_dips_below_threshold(self):
        guardian = WifiACGuardianWin.__new__(WifiACGuardianWin)
        guardian.config = GuardianConfig(target_ssid="Office-5G", min_bitrate_threshold=300)
        guardian._consecutive_good_readings = 0
        guardian._consecutive_degraded_readings = 0

        low_rate_vht = LinkInfo(
            connected=True,
            interface="WLAN-Office",
            ssid="Office-5G",
            phy_mode=PhyMode.VHT,
            tx_bitrate="100 Mbps",
            rx_bitrate="100 Mbps",
            radio_state=RadioState.ACTIVE,
        )

        self.assertTrue(low_rate_vht.has_approved_phy())
        self.assertFalse(low_rate_vht.is_good(min_bitrate_threshold=300))
        self.assertFalse(guardian._is_confirmable_degraded_link(low_rate_vht))
        self.assertTrue(guardian._observe_good_target_link(low_rate_vht))

    def test_recovery_sets_active_status_and_clears_next_deadline_until_complete(self):
        guardian = WifiACGuardianWin.__new__(WifiACGuardianWin)
        guardian.config = GuardianConfig(target_ssid="Office-5G", min_bitrate_threshold=300)
        guardian.state = GuardianState(
            current_link=LinkInfo(
                connected=True,
                interface="WLAN-Office",
                adapter="Wi-Fi Adapter",
                ssid="Office-5G",
                phy_mode=PhyMode.HT,
                tx_bitrate="144 Mbps",
                radio_state=RadioState.ACTIVE,
            )
        )
        guardian._has_established_target_link = False
        guardian._consecutive_degraded_readings = 0
        guardian._reset_degraded_confirmation = MagicMock()
        guardian._set_status = MagicMock()

        recovered = LinkInfo(
            connected=True,
            interface="WLAN-Office",
            adapter="Wi-Fi Adapter",
            ssid="Office-5G",
            phy_mode=PhyMode.VHT,
            tx_bitrate="866 Mbps",
            radio_state=RadioState.ACTIVE,
        )

        def recovery(*_args, **_kwargs):
            self.assertTrue(guardian.state.recovery_active)
            self.assertEqual(guardian.state.recovery_status, "Connecting")
            self.assertIsNone(guardian.state.next_check)
            return recovered

        guardian.reconnector = MagicMock()
        guardian.reconnector.trigger_reconnect.side_effect = recovery

        guardian._execute_reconnection_sequence(target_ssid="Office-5G")

        self.assertFalse(guardian.state.recovery_active)
        self.assertEqual(guardian.state.recovery_status, "")
        self.assertIs(guardian.state.current_link, recovered)
