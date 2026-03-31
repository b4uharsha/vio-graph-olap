"""Tests for structured logging configuration."""

from unittest.mock import patch
from types import SimpleNamespace

from wrapper.logging import configure_logging


class TestConfigureLogging:
    def test_configure_json_format(self):
        config = SimpleNamespace(format="json", level="INFO")
        configure_logging(config)

    def test_configure_console_format(self):
        config = SimpleNamespace(format="console", level="DEBUG")
        configure_logging(config)

    def test_configure_with_warning_level(self):
        config = SimpleNamespace(format="json", level="WARNING")
        configure_logging(config)
