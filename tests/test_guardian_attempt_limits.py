"""Recovery-attempt limit semantics for finite and infinite settings."""

import unittest
from unittest.mock import MagicMock

from wifi_ac_guardian_win.core.guardian import WifiACGuardianWin
from wifi_ac_guardian_win.core.models import GuardianConfig, GuardianState, LinkInfo, PhyMode, RadioState, StatusState


def degraded_link() -> LinkInfo:
    return LinkInfo(
        connected=True,
        interface="Wi-Fi",
        ssid="lab5g",
        phy_mode=PhyMode.HT,
        tx_bitrate="300 Mbps",
        radio_state=RadioState.ACTIVE,
    )


class TestGuardianAttemptLimits(unittest.TestCase):
    def _guardian(self, max_attempts: int, attempts_count: int) -> WifiACGuardianWin:
        guardian = WifiACGuardianWin.__new__(WifiACGuardianWin)
        guardian.config = GuardianConfig(target_ssid="lab5g", max_attempts=max_attempts)
        guardian.state = GuardianState(current_link=degraded_link(), attempts_count=attempts_count)
        guardian._set_status = MagicMock()
        guardian._reset_degraded_confirmation = MagicMock()
        guardian.reconnector = MagicMock()
        return guardian

    def test_finite_limit_stops_before_starting_another_recovery(self):
        guardian = self._guardian(max_attempts=2, attempts_count=2)

        guardian._execute_reconnection_sequence(target_ssid="lab5g")

        guardian.reconnector.trigger_reconnect.assert_not_called()
        guardian._set_status.assert_called_once_with(StatusState.FAILED, guardian.state.current_link)
        self.assertEqual(guardian.state.attempts_count, 2)

    def test_zero_means_infinite_and_starts_next_recovery(self):
        guardian = self._guardian(max_attempts=0, attempts_count=99)
        guardian.reconnector.trigger_reconnect.return_value = degraded_link()

        guardian._execute_reconnection_sequence(target_ssid="lab5g")

        guardian.reconnector.trigger_reconnect.assert_called_once_with("Wi-Fi", ssid="lab5g")
        self.assertEqual(guardian.state.attempts_count, 100)

    def test_reset_recovery_tracking_only_fires_on_the_first_attempt_of_a_sequence(self):
        fresh_sequence = self._guardian(max_attempts=0, attempts_count=0)
        fresh_sequence.reconnector.trigger_reconnect.return_value = degraded_link()
        fresh_sequence._execute_reconnection_sequence(target_ssid="lab5g")
        fresh_sequence.reconnector.reset_recovery_tracking.assert_called_once()

        continuing_sequence = self._guardian(max_attempts=0, attempts_count=1)
        continuing_sequence.reconnector.trigger_reconnect.return_value = degraded_link()
        continuing_sequence._execute_reconnection_sequence(target_ssid="lab5g")
        continuing_sequence.reconnector.reset_recovery_tracking.assert_not_called()

    def test_recovery_start_time_and_attempt_count_proxy_to_reconnector(self):
        guardian = WifiACGuardianWin.__new__(WifiACGuardianWin)
        sentinel_start_time = object()
        guardian.reconnector = MagicMock(recovery_start_time=sentinel_start_time, recovery_attempt_count=5)

        self.assertIs(guardian.recovery_start_time, sentinel_start_time)
        self.assertEqual(guardian.recovery_attempt_count, 5)


if __name__ == "__main__":
    unittest.main()
