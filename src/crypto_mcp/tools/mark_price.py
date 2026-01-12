"""MCP tool for mark price data."""

from mcp.server.fastmcp import FastMCP

from crypto_mcp.exchanges.base import BaseExchangeClient
from crypto_mcp.tools._utils import get_client


def register_mark_price_tools(
    mcp: FastMCP,
    clients: dict[str, BaseExchangeClient],
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
        client = get_client(clients, exchange)
        result = await client.get_mark_price(symbol.upper() if symbol else None)

        if isinstance(result, list):
            return [r.model_dump(mode="json") for r in result]
        return result.model_dump(mode="json")
