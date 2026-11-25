"""Network-free regression checks for the smoke checker."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("smoke_check", Path(__file__).resolve().parents[2] / "scripts" / "smoke_check.py")
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)


class SmokeTests(unittest.TestCase):
    def test_health_failure_reports_last_error(self):
        with patch.object(smoke, "fetch", side_effect=RuntimeError("unreachable")), patch.object(smoke.time, "sleep"), self.assertRaisesRegex(SystemExit, "unreachable"):
            smoke.wait_health("http://test")

    def test_retry_temporary_error(self):
        ready = json.dumps({"status": "ok", "documents": 2}).encode()
        with patch.object(smoke, "fetch", side_effect=[RuntimeError("503"), (200, ready)]), patch.object(smoke.time, "sleep"):
            self.assertEqual(smoke.wait_health("http://test")["documents"], 2)
