"""MCP tool for 24h ticker data."""

from mcp.server.fastmcp import FastMCP

from crypto_mcp.exchanges.binance import BinanceClient
from crypto_mcp.models import TickerResponse


def register_ticker_tools(mcp: FastMCP, client: BinanceClient) -> None:
    """Register ticker tools with the MCP server."""

    @mcp.tool()
    async def get_ticker_24h(symbol: str | None = None) -> dict | list[dict]:
        """Get 24-hour price and volume statistics for futures symbols.

        Returns rolling 24h window statistics including price change,
        volume, high/low prices, and trade count.

        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT). If None, returns all symbols.

        Returns:
            24h ticker statistics. Returns a list if no symbol specified.
        """
        result = await client.get_ticker_24h(symbol.upper() if symbol else None)

        if isinstance(result, list):
            return [r.model_dump(mode="json") for r in result]
        return result.model_dump(mode="json")
