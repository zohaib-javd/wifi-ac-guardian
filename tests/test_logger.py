"""Tests for the dedicated log directory, midnight rotation, and orphan cleanup."""

import logging
import tempfile
import unittest
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from unittest.mock import patch

import wifi_ac_guardian_win.logger as logger_module
from wifi_ac_guardian_win.logger import (
    cleanup_orphan_home_logs,
    default_log_directory,
    setup_logger,
)


class TestGuardianLogger(unittest.TestCase):
    def _reset_guardian_logger(self):
        logger = logging.getLogger("wifi_ac_guardian_win")
        previous_handlers = list(logger.handlers)
        for handler in logger.handlers:
            handler.close()
        logger.handlers.clear()
        return logger, previous_handlers

    def _restore_guardian_logger(self, logger, previous_handlers):
        for handler in logger.handlers:
            handler.close()
        logger.handlers.clear()
        logger.handlers.extend(previous_handlers)

    def test_default_log_directory_uses_localappdata_when_available(self):
        with patch.dict("os.environ", {"LOCALAPPDATA": r"C:\Fake\LocalAppData"}):
            directory = default_log_directory()
        self.assertEqual(directory, r"C:\Fake\LocalAppData\WiFi AC Guardian\logs")

    def test_default_log_directory_falls_back_to_home_when_localappdata_missing(self):
        with patch.dict("os.environ", {}, clear=False):
            import os
            os.environ.pop("LOCALAPPDATA", None)
            directory = default_log_directory()
        self.assertTrue(directory.endswith(".wifi-ac-guardian" + "/logs" if "/" in directory else ".wifi-ac-guardian\\logs"))

    def test_uses_midnight_rotation_with_one_backup(self):
        logger, previous_handlers = self._reset_guardian_logger()
        with tempfile.TemporaryDirectory() as directory:
            try:
                configured = setup_logger(str(Path(directory) / "guardian.log"))
                handlers = [handler for handler in configured.handlers if isinstance(handler, TimedRotatingFileHandler)]
                self.assertEqual(len(handlers), 1)
                self.assertEqual(handlers[0].when, "MIDNIGHT")
                self.assertEqual(handlers[0].backupCount, 1)
            finally:
                self._restore_guardian_logger(logger, previous_handlers)

    def test_log_directory_is_created_if_missing(self):
        logger, previous_handlers = self._reset_guardian_logger()
        with tempfile.TemporaryDirectory() as directory:
            try:
                nested = Path(directory) / "nested" / "logs" / "guardian.log"
                self.assertFalse(nested.parent.exists())
                setup_logger(str(nested))
                self.assertTrue(nested.parent.exists())
            finally:
                self._restore_guardian_logger(logger, previous_handlers)

    def test_moves_orphan_home_logs_into_target_directory(self):
        logger_module._ORPHAN_CLEANUP_DONE = False
        with tempfile.TemporaryDirectory() as home_dir, tempfile.TemporaryDirectory() as target_dir:
            home = Path(home_dir)
            orphan = home / "wifi_ac_guardian_win.log.2026-08-20"
            orphan.write_text("stale\n", encoding="utf-8")

            with patch.object(logger_module.Path, "home", return_value=home):
                cleanup_orphan_home_logs(target_dir)

            self.assertFalse(orphan.exists())
            self.assertTrue((Path(target_dir) / orphan.name).exists())
        logger_module._ORPHAN_CLEANUP_DONE = False

    def test_orphan_cleanup_runs_only_once_per_process(self):
        logger_module._ORPHAN_CLEANUP_DONE = False
        with tempfile.TemporaryDirectory() as home_dir, tempfile.TemporaryDirectory() as target_dir:
            home = Path(home_dir)
            first_orphan = home / "wifi_ac_guardian_win.log"
            first_orphan.write_text("first\n", encoding="utf-8")

            with patch.object(logger_module.Path, "home", return_value=home):
                cleanup_orphan_home_logs(target_dir)

                second_orphan = home / "wifi_ac_guardian_win.log.stale"
                second_orphan.write_text("second\n", encoding="utf-8")
                cleanup_orphan_home_logs(target_dir)

            # The second orphan was created after the one-time scan already
            # ran, so it must remain untouched in the home directory.
            self.assertTrue(second_orphan.exists())
        logger_module._ORPHAN_CLEANUP_DONE = False


if __name__ == "__main__":
    unittest.main()
