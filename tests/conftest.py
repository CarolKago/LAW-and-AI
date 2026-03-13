"""
pytest configuration and shared fixtures.

Downloads required NLTK corpora once per test session so individual test
modules do not need to hit the network repeatedly.
"""

import pytest
import unittest.mock as mock


def pytest_configure(config):
    """Download NLTK data needed by Legal_text_summariser before any test runs."""
    try:
        import nltk
        nltk.download("punkt", quiet=True)
        nltk.download("punkt_tab", quiet=True)
        nltk.download("stopwords", quiet=True)
    except Exception:
        # If NLTK is not installed, individual tests will fail with clear errors.
        pass
