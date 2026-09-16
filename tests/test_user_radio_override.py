"""Guardian must respect Wi-Fi states explicitly controlled by the user or system."""

import threading
import unittest
from unittest.mock import MagicMock

from wifi_ac_guardian_win.core.guardian import WifiACGuardianWin
from wifi_ac_guardian_win.core.models import GuardianConfig, GuardianState, LinkInfo, PhyMode, RadioState, StatusState


class TestUserRadioOverride(unittest.TestCase):
    def _guardian(self, radio_state: RadioState) -> WifiACGuardianWin:
        guardian = object.__new__(WifiACGuardianWin)
        guardian._lock = threading.RLock()
        guardian.config = GuardianConfig(is_paused=False, target_ssid="Office-5G")
        guardian.state = GuardianState(running=True)
        guardian.detector = MagicMock(
            get_link_info=MagicMock(
                return_value=LinkInfo(
                    connected=False,
                    phy_mode=PhyMode.DISCONNECTED,
                    radio_state=radio_state,
                )
            )
        )
        guardian._has_established_target_link = True
        guardian._consecutive_degraded_readings = 0
        guardian._reset_degraded_confirmation = MagicMock()
        guardian._set_status = MagicMock()
        guardian._execute_reconnection_sequence = MagicMock()
        return guardian

    def test_airplane_mode_radio_off_is_observed_without_recovery(self):
        guardian = self._guardian(RadioState.RADIO_OFF)

        guardian.perform_check()

        guardian._execute_reconnection_sequence.assert_not_called()
        guardian._set_status.assert_called_once()
        self.assertEqual(guardian._set_status.call_args.args[0], StatusState.STANDBY)

    def test_user_disabled_adapter_is_observed_without_recovery(self):
        guardian = self._guardian(RadioState.ADAPTER_DISABLED)

        guardian.perform_check()

        guardian._execute_reconnection_sequence.assert_not_called()
        guardian._set_status.assert_called_once()
        self.assertEqual(guardian._set_status.call_args.args[0], StatusState.STANDBY)


if __name__ == "__main__":
    unittest.main()
