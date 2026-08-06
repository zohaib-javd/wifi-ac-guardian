"""
Unit tests for the animation engine's pure logic (feature 001, M6 / T060-T061).

Covers only the framework-free parts — easing math, color interpolation, and
the global enable / fallback state machine. The after()-driven animate() loop
needs a live Tk mainloop and is verified on the desktop (SC-008), not here.
"""

import unittest

from wifi_ac_guardian_win import animation


class TestEaseInOut(unittest.TestCase):
    def test_endpoints_and_midpoint(self):
        self.assertAlmostEqual(animation.ease_in_out(0.0), 0.0, places=6)
        self.assertAlmostEqual(animation.ease_in_out(1.0), 1.0, places=6)
        self.assertAlmostEqual(animation.ease_in_out(0.5), 0.5, places=6)

    def test_monotonic_non_decreasing(self):
        prev = -1.0
        for i in range(0, 101):
            t = i / 100.0
            val = animation.ease_in_out(t)
            with self.subTest(t=t):
                self.assertGreaterEqual(val, prev)
                self.assertGreaterEqual(val, 0.0)
                self.assertLessEqual(val, 1.0)
            prev = val


class TestLerpColor(unittest.TestCase):
    def test_endpoints(self):
        self.assertEqual(animation.lerp_color("#000000", "#FFFFFF", 0.0), "#000000")
        self.assertEqual(animation.lerp_color("#000000", "#FFFFFF", 1.0), "#FFFFFF")

    def test_midpoint(self):
        # Halfway from black to white is mid-grey (#7f or #80 depending on rounding).
        mid = animation.lerp_color("#000000", "#FFFFFF", 0.5)
        r = int(mid[1:3], 16)
        self.assertIn(r, (127, 128))

    def test_parse_failure_falls_back_to_end(self):
        self.assertEqual(animation.lerp_color("not-a-color", "#123456", 0.3), "#123456")


class TestEnableFallbackStateMachine(unittest.TestCase):
    def setUp(self):
        # Snapshot and reset module globals so tests don't leak into each other.
        self._prev_enabled = animation._enabled
        self._prev_fallback = animation._disabled_by_fallback
        animation.set_enabled(False)

    def tearDown(self):
        animation._enabled = self._prev_enabled
        animation._disabled_by_fallback = self._prev_fallback

    def test_default_off(self):
        animation.set_enabled(False)
        self.assertFalse(animation.is_enabled())

    def test_enable_then_active(self):
        animation.set_enabled(True)
        self.assertTrue(animation.is_enabled())

    def test_fallback_disables_even_when_enabled(self):
        animation.set_enabled(True)
        animation._trip_fallback()
        self.assertTrue(animation._enabled)
        self.assertFalse(animation.is_enabled())

    def test_reenable_clears_fallback(self):
        animation.set_enabled(True)
        animation._trip_fallback()
        self.assertFalse(animation.is_enabled())
        animation.set_enabled(True)
        self.assertTrue(animation.is_enabled())


if __name__ == "__main__":
    unittest.main()
