"""Regression coverage for native auto-association configuration migration."""

import json
import tempfile
import unittest
from pathlib import Path

from wifi_ac_guardian_win.config import SETTINGS_SCHEMA_VERSION, load_config, save_config


class TestConfigMigration(unittest.TestCase):
    def test_migrates_unmarked_legacy_30_second_default_to_3_5_seconds_once(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps({"reconnect_delay": 30.0}), encoding="utf-8")

            migrated = load_config(str(path))

            self.assertEqual(migrated.reconnect_delay, 3.5)
            save_config(migrated, str(path), sync_startup_shortcut=False)
            persisted = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(persisted["settings_schema_version"], SETTINGS_SCHEMA_VERSION)

            migrated.reconnect_delay = 30.0
            save_config(migrated, str(path), sync_startup_shortcut=False)
            reloaded = load_config(str(path))
            self.assertEqual(reloaded.reconnect_delay, 30.0)

    def test_preserves_explicit_30_second_choice_from_prior_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps({"settings_schema_version": 3, "reconnect_delay": 30.0}), encoding="utf-8")

            loaded = load_config(str(path))

            self.assertEqual(loaded.reconnect_delay, 30.0)


if __name__ == "__main__":
    unittest.main()
