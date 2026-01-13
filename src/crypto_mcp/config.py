"""Configuration management for the MCP server."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # binance
    binance_futures_base_url: str = "https://fapi.binance.com"
    binance_api_key: str | None = None
    binance_api_secret: str | None = None

    # bybit
    bybit_futures_base_url: str = "https://api.bybit.com"
    bybit_api_key: str | None = None
    bybit_api_secret: str | None = None

    # http client
    http_timeout: float = 30.0

    # rate limiting
    rate_limit_enabled: bool = True
    binance_rate_limit: int = 1200  # requests per minute (conservative)
    bybit_rate_limit: int = 100  # requests per minute (conservative)
    rate_limit_retry_enabled: bool = True
    rate_limit_max_retries: int = 3

    # caching
    cache_enabled: bool = True
    cache_ttl: float = 3.0  # seconds

    # server
    server_name: str = "Crypto Data MCP"
    log_level: str = "INFO"

    model_config = {
        "env_prefix": "CRYPTO_MCP_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }
