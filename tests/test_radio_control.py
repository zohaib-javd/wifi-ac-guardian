"""Tests for preferred Windows radio-cycle path selection."""

from unittest.mock import patch

from wifi_ac_guardian_win.core.radio_control_win import cycle_preferred_radio_state


def test_uses_system_path_only_when_the_runtime_method_succeeds():
    with patch("wifi_ac_guardian_win.core.radio_control_win.cycle_system_radio_state", return_value=True) as system, patch("wifi_ac_guardian_win.core.radio_control_win.cycle_airplane_mode_radios") as per_radio:
        assert cycle_preferred_radio_state(3.5) == "system-airplane"

    system.assert_called_once_with(3.5)
    per_radio.assert_not_called()


def test_falls_back_to_per_radio_when_system_method_is_unavailable():
    with patch("wifi_ac_guardian_win.core.radio_control_win.cycle_system_radio_state", return_value=False) as system, patch("wifi_ac_guardian_win.core.radio_control_win.cycle_airplane_mode_radios", return_value=True) as per_radio:
        assert cycle_preferred_radio_state(3.5) == "per-radio"

    system.assert_called_once_with(3.5)
    per_radio.assert_called_once_with(3.5)


def test_reports_unavailable_when_neither_path_can_be_confirmed():
    with patch("wifi_ac_guardian_win.core.radio_control_win.cycle_system_radio_state", return_value=False), patch("wifi_ac_guardian_win.core.radio_control_win.cycle_airplane_mode_radios", return_value=False):
        assert cycle_preferred_radio_state(3.5) == "unavailable"
