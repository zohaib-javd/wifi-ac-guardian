"""Regression coverage for the bounded preferred-radio recovery cadence."""

import unittest
from unittest.mock import MagicMock, call, patch

from wifi_ac_guardian_win.core.models import GuardianConfig, LinkInfo, PhyMode, RadioState
from wifi_ac_guardian_win.core.reconnector_win import WifiReconnectorWin


class TestWifiReconnector(unittest.TestCase):
    def _link(self, *, connected=True, ssid="lab5g", phy=PhyMode.VHT, tx="866.7 Mbps", rx="866.7 Mbps", channel=161):
        return LinkInfo(
            connected=connected,
            interface="Wi-Fi",
            adapter="Intel(R) Wi-Fi 6 AX201 160MHz",
            ssid=ssid if connected else None,
            phy_mode=phy if connected else PhyMode.DISCONNECTED,
            tx_bitrate=tx if connected else None,
            rx_bitrate=rx if connected else None,
            channel=channel if connected else None,
            radio_type=phy.value if connected else "",
            radio_state=RadioState.ACTIVE if connected else RadioState.DISCONNECTED,
        )

    @patch("wifi_ac_guardian_win.core.reconnector_win.time.sleep")
    @patch("wifi_ac_guardian_win.core.reconnector_win.cycle_preferred_radio_state", return_value="per-radio")
    def test_uses_three_cycle_cadence_with_3_second_hold_and_no_fallback_when_autoconfig_succeeds(self, cycle_radio, mock_sleep):
        reconnector = WifiReconnectorWin(GuardianConfig(target_ssid="lab5g"))
        reconnector.detector.get_link_info = MagicMock(return_value=self._link())
        with patch.object(reconnector, "_disconnect_interface", return_value=True) as disconnect, patch.object(reconnector, "_flush_network_caches") as flush, patch.object(reconnector, "_wait_for_native_auto_association", return_value=self._link()) as observe, patch.object(reconnector, "_connect_interface") as fallback:
            result = reconnector.trigger_reconnect("Wi-Fi", "lab5g")

        self.assertTrue(result.is_good())
        disconnect.assert_called_once_with("Wi-Fi")
        flush.assert_called_once_with()
        cycle_radio.assert_called_once_with(hold_seconds=3.0)
        observe.assert_called_once_with("Wi-Fi", "lab5g", timeout_seconds=20.0)
        fallback.assert_not_called()
        # 1.5s post-disconnect wait, 2.0s post-scan settle, 6.0s post-connect verification.
        self.assertEqual(mock_sleep.call_args_list, [call(1.5), call(2.0), call(6.0)])

    @patch("wifi_ac_guardian_win.core.reconnector_win.time.sleep")
    @patch("wifi_ac_guardian_win.core.reconnector_win.cycle_preferred_radio_state", return_value="system-airplane")
    def test_runs_at_most_three_cycles_and_fallback_only_after_each_autoconfig_window(self, cycle_radio, _sleep):
        reconnector = WifiReconnectorWin(GuardianConfig(target_ssid="lab5g"))
        reconnector.detector.get_link_info = MagicMock(return_value=self._link())
        stuck = self._link(phy=PhyMode.HT, tx="300 Mbps", rx="300 Mbps")
        with patch.object(reconnector, "_disconnect_interface"), patch.object(reconnector, "_flush_network_caches"), patch.object(reconnector, "_wait_for_native_auto_association", return_value=stuck) as observe, patch.object(reconnector, "_connect_interface") as fallback:
            result = reconnector.trigger_reconnect("Wi-Fi", "lab5g")

        self.assertEqual(result.phy_mode, PhyMode.HT)
        self.assertEqual(cycle_radio.call_count, 3)
        self.assertEqual(observe.call_count, 3)
        fallback.assert_not_called()

    @patch("wifi_ac_guardian_win.core.reconnector_win.time.sleep")
    @patch("wifi_ac_guardian_win.core.reconnector_win.time.monotonic", side_effect=[0.0, 0.0, 1.0])
    def test_passive_observation_returns_first_target_association_even_if_stuck_ht(self, _monotonic, mock_sleep):
        reconnector = WifiReconnectorWin(GuardianConfig(target_ssid="lab5g"))
        disconnected = self._link(connected=False)
        stuck = self._link(phy=PhyMode.HT, tx="300 Mbps", rx="300 Mbps")
        reconnector.detector.get_link_info = MagicMock(side_effect=[disconnected, stuck])

        observed = reconnector._wait_for_native_auto_association("Wi-Fi", "lab5g", timeout_seconds=20.0)

        self.assertEqual(observed.phy_mode, PhyMode.HT)
        mock_sleep.assert_called_once_with(1.0)

    def test_profile_connect_command_is_reserved_for_post_window_fallback(self):
        reconnector = WifiReconnectorWin(GuardianConfig(target_ssid="lab5g"))
        with patch.object(reconnector, "_run_command", return_value=MagicMock(returncode=0, stdout="Success", stderr="")) as command:
            self.assertTrue(reconnector._connect_interface("Wi-Fi", "lab5g"))

        self.assertEqual(command.call_args.args[0], ["netsh", "wlan", "connect", "name=lab5g", "interface=Wi-Fi"])

    def test_recovery_tracking_is_empty_before_any_attempt(self):
        reconnector = WifiReconnectorWin(GuardianConfig(target_ssid="lab5g"))
        self.assertIsNone(reconnector.recovery_start_time)
        self.assertEqual(reconnector.recovery_attempt_count, 0)

    @patch("wifi_ac_guardian_win.core.reconnector_win.time.sleep")
    @patch("wifi_ac_guardian_win.core.reconnector_win.cycle_preferred_radio_state", return_value="per-radio")
    def test_recovery_tracking_sets_start_time_once_and_counts_every_call(self, _cycle_radio, _sleep):
        reconnector = WifiReconnectorWin(GuardianConfig(target_ssid="lab5g"))
        reconnector.detector.get_link_info = MagicMock(return_value=self._link())
        with patch.object(reconnector, "_disconnect_interface", return_value=True), \
                patch.object(reconnector, "_flush_network_caches"), \
                patch.object(reconnector, "_wait_for_native_auto_association", return_value=self._link()), \
                patch.object(reconnector, "_connect_interface"):
            reconnector.trigger_reconnect("Wi-Fi", "lab5g")

        self.assertIsNotNone(reconnector.recovery_start_time)
        self.assertEqual(reconnector.recovery_attempt_count, 1)
        first_start_time = reconnector.recovery_start_time

        # A second call within the same (unreset) sequence keeps the original
        # start time but advances the attempt count — this is what lets the
        # dashboard show "2 attempts (Started at <first attempt's time>)".
        with patch.object(reconnector, "_disconnect_interface", return_value=True), \
                patch.object(reconnector, "_flush_network_caches"), \
                patch.object(reconnector, "_wait_for_native_auto_association", return_value=self._link()), \
                patch.object(reconnector, "_connect_interface"):
            reconnector.trigger_reconnect("Wi-Fi", "lab5g")

        self.assertEqual(reconnector.recovery_start_time, first_start_time)
        self.assertEqual(reconnector.recovery_attempt_count, 2)

    def test_reset_recovery_tracking_clears_start_time_and_count(self):
        reconnector = WifiReconnectorWin(GuardianConfig(target_ssid="lab5g"))
        reconnector.recovery_start_time = MagicMock()
        reconnector.recovery_attempt_count = 3

        reconnector.reset_recovery_tracking()

        self.assertIsNone(reconnector.recovery_start_time)
        self.assertEqual(reconnector.recovery_attempt_count, 0)

    def test_recovery_tracking_untouched_when_no_interface_is_available(self):
        reconnector = WifiReconnectorWin(GuardianConfig(target_ssid="lab5g", interface=None))
        reconnector.detector.get_link_info = MagicMock(return_value=self._link(connected=False))
        reconnector.detector.get_link_info.return_value.interface = ""

        reconnector.trigger_reconnect(interface=None, ssid="lab5g")

        self.assertIsNone(reconnector.recovery_start_time)
        self.assertEqual(reconnector.recovery_attempt_count, 0)


if __name__ == "__main__":
    unittest.main()
