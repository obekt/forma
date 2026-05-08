"""Tests for configuration."""

import pytest

from forma.config import Settings


def test_default_settings():
    """Test default settings values."""
    settings = Settings(_env_file=None)
    assert settings.host == "0.0.0.0"
    assert settings.port == 8000
    assert settings.debug is False
    # Extraction settings
    assert settings.extractor_base_url == ""
    assert settings.extractor_api_key == ""
    assert settings.extractor_model_name == ""
    assert settings.extractor_timeout == 120.0
    # GrafitoDB settings
    assert settings.grafitodb_path == "./grafito_data/forma.db"
    assert settings.grafitodb_embedding_model == "all-MiniLM-L6-v2"
    assert settings.grafitodb_vector_dim == 384
    # Tool settings
    assert settings.tools_enabled is False
    assert settings.tools_max_iterations == 5
    assert settings.tools_timeout == 30.0


def test_extraction_settings():
    """Test extraction LLM settings."""
    settings = Settings(
        extractor_base_url="http://localhost:1234/v1",
        extractor_model_name="gemma-4-e4b-it",
        _env_file=None,
    )
    assert settings.extractor_base_url == "http://localhost:1234/v1"
    assert settings.extractor_model_name == "gemma-4-e4b-it"


def test_tool_settings():
    """Test tool execution settings."""
    settings = Settings(
        tools_enabled=True,
        tools_max_iterations=3,
        tools_timeout=60.0,
        _env_file=None,
    )
    assert settings.tools_enabled is True
    assert settings.tools_max_iterations == 3
    assert settings.tools_timeout == 60.0


def test_grafitodb_settings():
    """Test GrafitoDB settings."""
    settings = Settings(
        grafitodb_path="./custom/path/db.db",
        grafitodb_vector_dim=768,
        _env_file=None,
    )
    assert settings.grafitodb_path == "./custom/path/db.db"
    assert settings.grafitodb_vector_dim == 768


def test_history_settings():
    """Test request history settings."""
    settings = Settings(
        history_enabled=False,
        history_max_records=50,
        _env_file=None,
    )
    assert settings.history_enabled is False
    assert settings.history_max_records == 50
