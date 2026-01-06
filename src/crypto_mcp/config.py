"""Configuration management for the MCP server."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # binance
    binance_futures_base_url: str = "https://fapi.binance.com"
    binance_api_key: str | None = None
    binance_api_secret: str | None = None

    # http client
    http_timeout: float = 30.0

    # server
    server_name: str = "Crypto Data MCP"
    log_level: str = "INFO"

    model_config = {
        "env_prefix": "CRYPTO_MCP_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }
