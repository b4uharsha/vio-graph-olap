"""Tests for configuration validation."""

import pytest
from pydantic import ValidationError

from wrapper.config import (
    WrapperConfig,
    FalkorDBConfig,
    MetricsConfig,
    LoggingConfig,
    InternalAuthConfig,
)


class TestWrapperConfig:
    def test_defaults(self, monkeypatch):
        monkeypatch.delenv("WRAPPER_INSTANCE_ID", raising=False)
        monkeypatch.delenv("WRAPPER_SNAPSHOT_ID", raising=False)
        monkeypatch.delenv("WRAPPER_MAPPING_ID", raising=False)
        monkeypatch.delenv("WRAPPER_GCS_BASE_PATH", raising=False)
        config = WrapperConfig(control_plane_url="http://localhost:8080")
        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert config.instance_id == ""
        assert config.gcs_base_path == ""

    def test_gcs_path_validation_valid(self):
        config = WrapperConfig(
            control_plane_url="http://localhost:8080",
            gcs_base_path="gs://my-bucket/path/",
        )
        assert config.gcs_base_path == "gs://my-bucket/path"  # trailing slash stripped

    def test_gcs_path_validation_invalid(self):
        with pytest.raises(ValidationError, match="gs://"):
            WrapperConfig(
                control_plane_url="http://localhost:8080",
                gcs_base_path="s3://wrong-prefix",
            )

    def test_gcs_path_empty_is_valid(self):
        config = WrapperConfig(control_plane_url="http://localhost:8080", gcs_base_path="")
        assert config.gcs_base_path == ""

    def test_port_range(self):
        with pytest.raises(ValidationError):
            WrapperConfig(control_plane_url="http://localhost:8080", port=0)
        with pytest.raises(ValidationError):
            WrapperConfig(control_plane_url="http://localhost:8080", port=99999)


class TestFalkorDBConfig:
    def test_defaults(self):
        config = FalkorDBConfig()
        assert config.query_timeout_ms == 60_000
        assert config.algorithm_timeout_ms == 1_800_000

    def test_timeout_minimum(self):
        with pytest.raises(ValidationError):
            FalkorDBConfig(query_timeout_ms=100)


class TestMetricsConfig:
    def test_defaults(self):
        config = MetricsConfig()
        assert config.report_interval_seconds == 60
        assert config.enabled is True

    def test_interval_minimum(self):
        with pytest.raises(ValidationError):
            MetricsConfig(report_interval_seconds=5)


class TestLoggingConfig:
    def test_defaults(self, monkeypatch):
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        monkeypatch.delenv("LOG_FORMAT", raising=False)
        config = LoggingConfig()
        assert config.level == "INFO"
        assert config.format == "json"

    def test_valid_levels(self):
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            config = LoggingConfig(level=level)
            assert config.level == level


class TestInternalAuthConfig:
    def test_defaults(self):
        config = InternalAuthConfig()
        assert config.internal_api_key is None

    def test_with_key(self):
        config = InternalAuthConfig(internal_api_key="test-key-123")
        assert config.internal_api_key == "test-key-123"
