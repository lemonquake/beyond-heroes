"""Regression checks for desktop Start reporting an unusable server as ready."""
import contextlib
import io
import unittest
from unittest.mock import patch

from server import control


class DesktopStartTests(unittest.TestCase):
    def start_existing(self, service=None, error=None):
        with patch.object(control.os, "name", "nt"), patch.object(control, "running", return_value=True), \
                patch.object(control, "health", return_value=service, side_effect=error), \
                patch.object(control.subprocess, "Popen") as launch, contextlib.redirect_stdout(io.StringIO()) as output:
            try:
                control.main(["start"])
            finally:
                launch.assert_not_called()
            return output.getvalue()

    def test_start_refuses_a_stale_running_server(self):
        with self.assertRaises(SystemExit) as result:
            self.start_existing({"protocol": control.PROTOCOL - 1, "game_online": True})
        self.assertIn("Stop Official Server.cmd", str(result.exception))
        self.assertIn("Start Official Server.cmd", str(result.exception))

    def test_start_refuses_an_offline_coordinator(self):
        with self.assertRaisesRegex(SystemExit, "game coordinator is offline"):
            self.start_existing({"protocol": control.PROTOCOL, "game_online": False})

    def test_start_reports_an_unreachable_account_service(self):
        with self.assertRaisesRegex(SystemExit, "account service did not answer"):
            self.start_existing(error=OSError("connection refused"))

    def test_repeated_start_confirms_health_without_launching_duplicates(self):
        output = self.start_existing({"protocol": control.PROTOCOL, "game_online": True})
        self.assertIn("already running and online", output)


if __name__ == "__main__":
    unittest.main()
