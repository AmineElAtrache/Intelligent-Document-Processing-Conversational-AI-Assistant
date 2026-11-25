"""Environment defaults without OCR or model dependencies."""
import os
import unittest
from unittest.mock import patch

from app.config import default_provider, ollama_base_url, openai_api_key


class ConfigTests(unittest.TestCase):
    def test_ollama_trailing_slash(self):
        with patch.dict(os.environ, {"OLLAMA_BASE_URL": " http://localhost:11434/ "}):
            self.assertEqual(ollama_base_url(), "http://localhost:11434")

    def test_provider_case_and_spaces(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": " OPENAI "}):
            self.assertEqual(default_provider(), "openai")

    def test_blank_ollama_url_uses_local_default(self):
        with patch.dict(os.environ, {"OLLAMA_BASE_URL": "  "}):
            self.assertEqual(ollama_base_url(), "http://127.0.0.1:11434")

    def test_unknown_provider_uses_mock(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "unknown"}):
            self.assertEqual(default_provider(), "mock")

    def test_api_key_is_trimmed(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "  synthetic  "}):
            self.assertEqual(openai_api_key(), "synthetic")
