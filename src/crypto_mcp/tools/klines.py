"""MCP tool for klines (candlestick) data."""

import asyncio
from datetime import datetime

from mcp.server.fastmcp import FastMCP

from crypto_mcp.exchanges.base import BaseExchangeClient
from crypto_mcp.models.common import ValidInterval
from crypto_mcp.tools._utils import get_client


def register_klines_tools(
    mcp: FastMCP,
    clients: dict[str, BaseExchangeClient],
) -> None:
    """Register klines tools with the MCP server."""

    @mcp.tool()
    async def get_klines(
        symbol: str,
        interval: str,
        limit: int = 500,
        start_time: str | None = None,
        end_time: str | None = None,
        exchange: str = "binance",
    ) -> dict:
        """Get OHLCV candlestick data for a futures symbol.

        Returns Open, High, Low, Close, Volume (OHLCV) data at the specified
        time interval.

        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT)
            interval: Candlestick interval. Valid values: 1m, 3m, 5m, 15m, 30m,
                      1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
            limit: Number of candles to return (1-1500, default 500)
            start_time: Start time in ISO format (e.g., 2024-01-01T00:00:00)
            end_time: End time in ISO format (e.g., 2024-01-02T00:00:00)
            exchange: Exchange to query ("binance" or "bybit", default: binance)

        Returns:
            Klines data including symbol, interval, and list of candles
        """
        client = get_client(clients, exchange)

        # validate and normalize interval (accepts both Binance and Bybit formats)
        normalized_interval = ValidInterval.validate(interval)

        # parse datetime strings if provided
        start_dt = datetime.fromisoformat(start_time) if start_time else None
        end_dt = datetime.fromisoformat(end_time) if end_time else None

        result = await client.get_klines(
            symbol=symbol.upper(),
            interval=normalized_interval,
            limit=limit,
            start_time=start_dt,
            end_time=end_dt,
        )
        return result.model_dump(mode="json")

    @mcp.tool()
    async def get_klines_batch(
        symbols: list[str],
        interval: str,
        limit: int = 500,
        start_time: str | None = None,
        end_time: str | None = None,
        exchange: str = "binance",
    ) -> dict[str, dict]:
        """Get OHLCV candlestick data for MULTIPLE symbols in parallel.

        Use this tool instead of calling get_klines multiple times.
        Much faster for querying price data of many symbols at once.

        Args:
            symbols: List of trading pair symbols (e.g., ["BTCUSDT", "ETHUSDT"])
            interval: Candlestick interval. Valid values: 1m, 3m, 5m, 15m, 30m,
                      1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
            limit: Number of candles per symbol (1-1500, default 500)
            start_time: Start time in ISO format (e.g., 2024-01-01T00:00:00)
            end_time: End time in ISO format (e.g., 2024-01-02T00:00:00)
            exchange: Exchange to query ("binance" or "bybit", default: binance)

        Returns:
            Dict mapping each symbol to its klines data
        """
        client = get_client(clients, exchange)
        normalized_interval = ValidInterval.validate(interval)

        start_dt = datetime.fromisoformat(start_time) if start_time else None
        end_dt = datetime.fromisoformat(end_time) if end_time else None

        async def fetch_one(sym: str) -> tuple[str, dict]:
            result = await client.get_klines(
                symbol=sym.upper(),
                interval=normalized_interval,
                limit=limit,
                start_time=start_dt,
                end_time=end_dt,
            )
            return sym.upper(), result.model_dump(mode="json")

        results = await asyncio.gather(*[fetch_one(s) for s in symbols])
        return dict(results)
