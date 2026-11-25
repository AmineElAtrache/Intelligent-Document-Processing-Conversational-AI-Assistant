"""Reject invalid questions before retrieval or provider calls."""
import unittest
from pydantic import ValidationError
from app.main import ChatRequest


class ChatValidationTests(unittest.TestCase):
    def test_blank_question(self):
        with self.assertRaises(ValidationError):
            ChatRequest(message=" \n\t")

    def test_trim_question(self):
        self.assertEqual(ChatRequest(message="  Total?  ").message, "Total?")

    def test_browser_key_rejected(self):
        with self.assertRaises(ValidationError):
            ChatRequest(message="Total?", api_key="synthetic")
