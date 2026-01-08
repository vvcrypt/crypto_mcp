"""MCP tool for open interest data."""

from mcp.server.fastmcp import FastMCP

from crypto_mcp.exchanges.binance import BinanceClient
from crypto_mcp.models import OpenInterestResponse


def register_open_interest_tools(mcp: FastMCP, client: BinanceClient) -> None:
    """Register open interest tools with the MCP server."""

    @mcp.tool()
    async def get_open_interest(symbol: str) -> dict:
        """Get current open interest for a futures symbol.

        Open interest is the total number of outstanding futures contracts.
        Rising OI indicates new money entering the market.

        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT, ETHUSDT)

        Returns:
            Open interest data including symbol, amount, timestamp, and exchange
        """
        result: OpenInterestResponse = await client.get_open_interest(symbol.upper())
        return result.model_dump(mode="json")
