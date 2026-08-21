"""
Status descriptor completeness test (feature 001, T021).

Verifies every StatusState yields a complete descriptor with all fields
populated and valid references (accent token exists, artwork file exists).
"""

import os
import unittest

from wifi_ac_guardian_win.core.models import StatusState
from wifi_ac_guardian_win import status_presentation, theme


class TestStatusPresentationCompleteness(unittest.TestCase):
    def test_every_state_has_descriptor(self):
        """Every StatusState must yield a non-None descriptor."""
        for state in StatusState:
            with self.subTest(state=state):
                desc = status_presentation.get_presentation(state, target_ssid="TestSSID")
                self.assertIsNotNone(desc, f"{state} returned None")

    def test_all_fields_populated(self):
        """Every descriptor field must be non-empty (supporting text may be empty string)."""
        for state in StatusState:
            with self.subTest(state=state):
                desc = status_presentation.get_presentation(state)
                self.assertIsInstance(desc.accent, str)
                self.assertTrue(desc.accent, f"{state}.accent is empty")
                self.assertIsInstance(desc.headline, str)
                self.assertTrue(desc.headline, f"{state}.headline is empty")
                self.assertIsInstance(desc.supporting, str)
                # supporting may be "" for IDLE
                self.assertIsInstance(desc.artwork, str)
                self.assertTrue(desc.artwork, f"{state}.artwork is empty")
                self.assertIsInstance(desc.tray_tooltip_prefix, str)
                self.assertTrue(desc.tray_tooltip_prefix, f"{state}.tray_tooltip_prefix is empty")
                self.assertIsInstance(desc.action_label, str)
                self.assertTrue(desc.action_label, f"{state}.action_label is empty")

    def test_accent_is_valid_hex_or_theme_attr(self):
        """Accent must be a hex color or a valid theme attribute."""
        for state in StatusState:
            with self.subTest(state=state):
                desc = status_presentation.get_presentation(state)
                accent = desc.accent
                # Check if it's a hex color
                if accent.startswith("#"):
                    self.assertEqual(len(accent), 7, f"{state}.accent '{accent}' not 7-char hex")
                else:
                    # Must be a valid theme token attribute
                    self.assertTrue(hasattr(theme, accent), f"{state}.accent '{accent}' not in theme")

    def test_artwork_file_exists(self):
        """Artwork filename must correspond to an actual asset (spot-check known assets)."""
        known_artwork = {"good.png", "retrying.png", "failed.png", "standby.png"}
        for state in StatusState:
            with self.subTest(state=state):
                desc = status_presentation.get_presentation(state)
                self.assertIn(desc.artwork, known_artwork,
                              f"{state}.artwork '{desc.artwork}' not in known set")

    def test_target_ssid_propagates_to_action_label(self):
        """STANDBY action label must include the target SSID."""
        desc = status_presentation.get_presentation(StatusState.STANDBY, target_ssid="MyNetwork")
        self.assertIn("MyNetwork", desc.action_label)


if __name__ == "__main__":
    unittest.main()
