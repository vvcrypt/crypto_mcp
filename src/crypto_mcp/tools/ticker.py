"""MCP tool for 24h ticker data."""

from mcp.server.fastmcp import FastMCP

from crypto_mcp.exchanges.base import BaseExchangeClient
from crypto_mcp.tools._utils import get_client


def register_ticker_tools(
    mcp: FastMCP,
    clients: dict[str, BaseExchangeClient],
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
        client = get_client(clients, exchange)
        result = await client.get_ticker_24h(symbol.upper() if symbol else None)

        if isinstance(result, list):
            return [r.model_dump(mode="json") for r in result]
        return result.model_dump(mode="json")
