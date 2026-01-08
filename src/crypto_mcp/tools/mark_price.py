"""MCP tool for mark price data."""

from mcp.server.fastmcp import FastMCP

from crypto_mcp.exchanges.binance import BinanceClient
from crypto_mcp.models import MarkPriceResponse


def register_mark_price_tools(mcp: FastMCP, client: BinanceClient) -> None:
    """Register mark price tools with the MCP server."""

    @mcp.tool()
    async def get_mark_price(symbol: str | None = None) -> dict | list[dict]:
        """Get current mark price and funding info for futures symbols.

        Mark price is the fair price used for liquidations, calculated from
        the index price plus a decaying funding basis.

        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT). If None, returns all symbols.

        Returns:
            Mark price data including mark price, index price, funding rate,
            and next funding time. Returns a list if no symbol specified.
        """
        result = await client.get_mark_price(symbol.upper() if symbol else None)

        if isinstance(result, list):
            return [r.model_dump(mode="json") for r in result]
        return result.model_dump(mode="json")
