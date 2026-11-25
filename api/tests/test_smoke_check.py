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
    def test_wait_for_seeded_document(self):
        empty = b'{"status":"ok","documents":0}'
        ready = b'{"status":"ok","documents":2}'
        with patch.object(smoke, "fetch", side_effect=[(200, empty), (200, ready)]), patch.object(smoke.time, "sleep"):
            self.assertEqual(smoke.wait_health("http://test")["documents"], 2)

    def test_retry_invalid_json(self):
        ready = b'{"status":"ok","documents":1}'
        with patch.object(smoke, "fetch", side_effect=[(200, b"not-json"), (200, ready)]), patch.object(smoke.time, "sleep"):
            self.assertEqual(smoke.wait_health("http://test")["status"], "ok")

    def test_health_failure_reports_last_error(self):
        with patch.object(smoke, "fetch", side_effect=RuntimeError("unreachable")), patch.object(smoke.time, "sleep"), self.assertRaisesRegex(SystemExit, "unreachable"):
            smoke.wait_health("http://test")

    def test_retry_temporary_error(self):
        ready = json.dumps({"status": "ok", "documents": 2}).encode()
        with patch.object(smoke, "fetch", side_effect=[RuntimeError("503"), (200, ready)]), patch.object(smoke.time, "sleep"):
            self.assertEqual(smoke.wait_health("http://test")["documents"], 2)
