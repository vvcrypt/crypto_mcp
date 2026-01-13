"""MCP tool for 24h ticker data."""

from mcp.server.fastmcp import FastMCP

from crypto_mcp.exchanges.base import BaseExchangeClient
from crypto_mcp.tools._utils import get_client
from crypto_mcp.utils.cache import TTLCache


def register_ticker_tools(
    mcp: FastMCP,
    clients: dict[str, BaseExchangeClient],
    cache: TTLCache | None = None,
) -> None:
    """Register ticker tools with the MCP server."""

    @mcp.tool()
    async def get_ticker_24h(
        symbol: str | None = None,
        exchange: str = "binance",
    ) -> dict | list[dict]:
        """Get 24-hour price and volume statistics for futures symbols.

        Returns rolling 24h window statistics including price change,
        volume, high/low prices, and trade count.

        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT). If None, returns all symbols.
            exchange: Exchange to query ("binance" or "bybit", default: binance)

        Returns:
            24h ticker statistics. Returns a list if no symbol specified.
        """
        normalized_symbol = symbol.upper() if symbol else None
        cache_key = f"ticker_24h:{exchange}:{normalized_symbol}"

        # check cache first
        if cache:
            hit, cached_value = await cache.get(cache_key)
            if hit:
                return cached_value

        # cache miss - fetch from API
        client = get_client(clients, exchange)
        result = await client.get_ticker_24h(normalized_symbol)

        response: dict | list[dict]
        if isinstance(result, list):
            response = [r.model_dump(mode="json") for r in result]
        else:
            response = result.model_dump(mode="json")

        # store in cache
        if cache:
            await cache.set(cache_key, response)

        return response
