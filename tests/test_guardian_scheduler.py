"""Regression tests for Protection Engine next-check scheduling."""

import threading
import unittest
from datetime import datetime

from wifi_ac_guardian_win.core.guardian import WifiACGuardianWin
from wifi_ac_guardian_win.core.models import GuardianConfig, GuardianState


class TestGuardianScheduler(unittest.TestCase):
    def _guardian_for_schedule_test(self, *, running: bool, paused: bool, interval: float) -> WifiACGuardianWin:
        guardian = object.__new__(WifiACGuardianWin)
        guardian.config = GuardianConfig(check_interval=interval, is_paused=paused)
        guardian.state = GuardianState(running=running)
        guardian._schedule_changed = threading.Event()
        return guardian

    def test_next_check_uses_saved_monitoring_interval(self):
        guardian = self._guardian_for_schedule_test(running=True, paused=False, interval=300.0)
        before = datetime.now()

        guardian.reschedule_checks()

        self.assertIsNotNone(guardian.state.next_check)
        remaining = (guardian.state.next_check - before).total_seconds()
        self.assertGreaterEqual(remaining, 299.0)
        self.assertLessEqual(remaining, 301.0)
        self.assertTrue(guardian._schedule_changed.is_set())

    def test_paused_engine_has_no_next_check_deadline(self):
        guardian = self._guardian_for_schedule_test(running=True, paused=True, interval=30.0)

        guardian.reschedule_checks()

        self.assertIsNone(guardian.state.next_check)
        self.assertTrue(guardian._schedule_changed.is_set())


if __name__ == "__main__":
    unittest.main()
