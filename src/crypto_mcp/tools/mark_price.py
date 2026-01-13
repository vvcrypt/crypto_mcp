"""MCP tool for mark price data."""

from mcp.server.fastmcp import FastMCP

from crypto_mcp.exchanges.base import BaseExchangeClient
from crypto_mcp.tools._utils import get_client
from crypto_mcp.utils.cache import TTLCache


def register_mark_price_tools(
    mcp: FastMCP,
    clients: dict[str, BaseExchangeClient],
    cache: TTLCache | None = None,
) -> None:
    """Register mark price tools with the MCP server."""

    @mcp.tool()
    async def get_mark_price(
        symbol: str | None = None,
        exchange: str = "binance",
    ) -> dict | list[dict]:
        """Get current mark price and funding info for futures symbols.

        Mark price is the fair price used for liquidations, calculated from
        the index price plus a decaying funding basis.

        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT). If None, returns all symbols.
            exchange: Exchange to query ("binance" or "bybit", default: binance)

        Returns:
            Mark price data including mark price, index price, funding rate,
            and next funding time. Returns a list if no symbol specified.
        """
        normalized_symbol = symbol.upper() if symbol else None
        cache_key = f"mark_price:{exchange}:{normalized_symbol}"

        # check cache first
        if cache:
            hit, cached_value = await cache.get(cache_key)
            if hit:
                return cached_value

        # cache miss - fetch from API
        client = get_client(clients, exchange)
        result = await client.get_mark_price(normalized_symbol)

        if isinstance(result, list):
            response = [r.model_dump(mode="json") for r in result]
        else:
            response = result.model_dump(mode="json")

        # store in cache
        if cache:
            await cache.set(cache_key, response)

        return response
