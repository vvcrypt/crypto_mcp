"""Tests for configuration module."""

from crypto_mcp.config import Settings


class TestSettings:
    """Tests for Settings class."""

    def test_default_values(self):
        """Settings have sensible defaults."""
        settings = Settings()

        assert settings.binance_futures_base_url == "https://fapi.binance.com"
        assert settings.binance_api_key is None
        assert settings.http_timeout == 30.0
        assert settings.server_name == "Crypto Data MCP"

    def test_custom_values(self):
        """Settings accept custom values."""
        settings = Settings(
            binance_futures_base_url="https://test.com",
            binance_api_key="test_key",
            http_timeout=10.0,
        )

        assert settings.binance_futures_base_url == "https://test.com"
        assert settings.binance_api_key == "test_key"
        assert settings.http_timeout == 10.0

    def test_fixture_provides_settings(self, settings: Settings):
        """Fixture provides working settings instance."""
        assert settings.http_timeout == 5.0  # test override
        assert settings.binance_futures_base_url == "https://fapi.binance.com"
