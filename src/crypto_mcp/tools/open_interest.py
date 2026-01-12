"""MCP tool for open interest data."""

import asyncio

from mcp.server.fastmcp import FastMCP

from crypto_mcp.exchanges.base import BaseExchangeClient
from crypto_mcp.models import OpenInterestResponse
from crypto_mcp.tools._utils import get_client


def register_open_interest_tools(
    mcp: FastMCP,
    clients: dict[str, BaseExchangeClient],
) -> None:
    """Register open interest tools with the MCP server."""

    @mcp.tool()
    async def get_open_interest(
        symbol: str,
        exchange: str = "binance",
    ) -> dict:
        """Get current open interest for a futures symbol.

        Open interest is the total number of outstanding futures contracts.
        Rising OI indicates new money entering the market.

        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT, ETHUSDT)
            exchange: Exchange to query ("binance" or "bybit", default: binance)

        Returns:
            Open interest data including symbol, amount, timestamp, and exchange
        """
        client = get_client(clients, exchange)
        result: OpenInterestResponse = await client.get_open_interest(symbol.upper())
        return result.model_dump(mode="json")

    @mcp.tool()
    async def get_open_interest_batch(
        symbols: list[str],
        exchange: str = "binance",
    ) -> dict[str, dict]:
        """Get current open interest for MULTIPLE symbols in parallel.

        Use this tool instead of calling get_open_interest multiple times.
        Much faster for querying many symbols at once.

        Args:
            symbols: List of trading pair symbols (e.g., ["BTCUSDT", "ETHUSDT", "SOLUSDT"])
            exchange: Exchange to query ("binance" or "bybit", default: binance)

        Returns:
            Dict mapping each symbol to its open interest data
        """
        client = get_client(clients, exchange)

        async def fetch_one(sym: str) -> tuple[str, dict]:
            result = await client.get_open_interest(symbol=sym.upper())
            return sym.upper(), result.model_dump(mode="json")

        results = await asyncio.gather(*[fetch_one(s) for s in symbols])
        return dict(results)
