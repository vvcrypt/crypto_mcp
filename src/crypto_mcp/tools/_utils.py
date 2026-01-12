"""Utility functions for tools module."""

from crypto_mcp.exchanges.base import BaseExchangeClient
from crypto_mcp.exceptions import ValidationError


SUPPORTED_EXCHANGES = ["binance", "bybit"]


def get_client(
    clients: dict[str, BaseExchangeClient],
    exchange: str,
) -> BaseExchangeClient:
    """Get client for the specified exchange.

    Args:
        clients: Dict mapping exchange names to client instances
        exchange: Exchange name (e.g., "binance", "bybit")

    Returns:
        Exchange client instance

    Raises:
        ValidationError: If exchange is not supported
    """
    exchange_lower = exchange.lower()
    client = clients.get(exchange_lower)
    if client is None:
        raise ValidationError(
            f"Unknown exchange: {exchange}. Supported: {', '.join(SUPPORTED_EXCHANGES)}"
        )
    return client
