"""
WCAG-AA contrast tests for the design-token palette (feature 001, T011).

Verifies every text/surface pairing that ships in the UI meets WCAG 2.1 AA:
- >= 4.5:1 for normal body/caption text
- >= 3.0:1 for large text and non-text UI (accent fills, borders)
"""

import unittest

from wifi_ac_guardian_win import theme


AA_NORMAL = 4.5
AA_LARGE = 3.0


class TestContrastRatio(unittest.TestCase):
    def test_known_ratios(self):
        # White on black is the maximum (~21); identical colors are 1.0.
        self.assertAlmostEqual(theme.contrast_ratio("#FFFFFF", "#000000"), 21.0, places=1)
        self.assertAlmostEqual(theme.contrast_ratio("#777777", "#777777"), 1.0, places=2)

    def test_symmetry(self):
        self.assertAlmostEqual(
            theme.contrast_ratio(theme.TEXT_PRIMARY, theme.CARD),
            theme.contrast_ratio(theme.CARD, theme.TEXT_PRIMARY),
            places=6,
        )


class TestPaletteMeetsAA(unittest.TestCase):
    SURFACES = (theme.BG, theme.CARD, theme.PANEL)

    def test_body_text_on_all_surfaces(self):
        """Primary and secondary text must clear AA-normal on every surface."""
        for fg in (theme.TEXT_PRIMARY, theme.TEXT_SECONDARY):
            for bg in self.SURFACES:
                with self.subTest(fg=fg, bg=bg):
                    self.assertGreaterEqual(theme.contrast_ratio(fg, bg), AA_NORMAL)

    def test_muted_text_on_all_surfaces(self):
        """Muted captions must clear AA-normal on every surface (F-13 fix)."""
        for bg in self.SURFACES:
            with self.subTest(bg=bg):
                self.assertGreaterEqual(theme.contrast_ratio(theme.TEXT_MUTED, bg), AA_NORMAL)

    def test_accent_text_on_surfaces(self):
        """Accent-colored status text must clear AA-large on card surfaces."""
        pairs = [
            (theme.ACCENT, theme.CARD),
            (theme.WARN, theme.CARD),
            (theme.ERROR, theme.CARD),
            (theme.INFO, theme.CARD),
        ]
        for fg, bg in pairs:
            with self.subTest(fg=fg, bg=bg):
                self.assertGreaterEqual(theme.contrast_ratio(fg, bg), AA_LARGE)

    def test_button_ink_on_accent_fills(self):
        """Text drawn on filled buttons must clear AA-large against the fill."""
        pairs = [
            (theme.ON_ACCENT, theme.ACCENT),
            (theme.ON_ERROR, theme.ERROR),
            (theme.ON_WARN, theme.WARN),
        ]
        for fg, bg in pairs:
            with self.subTest(fg=fg, bg=bg):
                self.assertGreaterEqual(theme.contrast_ratio(fg, bg), AA_LARGE)


if __name__ == "__main__":
    unittest.main()
