"""Shared pytest fixtures for all tests."""

import pytest

from crypto_mcp.config import Settings


@pytest.fixture
def settings() -> Settings:
    """Test settings with defaults."""
    return Settings(
        binance_futures_base_url="https://fapi.binance.com",
        http_timeout=5.0,  # shorter for tests
    )
