"""Exception classes for crypto MCP server."""

from crypto_mcp.exceptions.base import (
    CryptoMCPError,
    ExchangeError,
    RateLimitError,
    SymbolNotFoundError,
    ValidationError,
)

__all__ = [
    "CryptoMCPError",
    "ExchangeError",
    "RateLimitError",
    "SymbolNotFoundError",
    "ValidationError",
]
