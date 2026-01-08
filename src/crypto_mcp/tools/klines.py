"""MCP tool for klines (candlestick) data."""

from datetime import datetime

from mcp.server.fastmcp import FastMCP

from crypto_mcp.exchanges.binance import BinanceClient
from crypto_mcp.models.common import ValidInterval


def register_klines_tools(mcp: FastMCP, client: BinanceClient) -> None:
    """Register klines tools with the MCP server."""

    @mcp.tool()
    async def get_klines(
        symbol: str,
        interval: str,
        limit: int = 500,
        start_time: str | None = None,
        end_time: str | None = None,
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

        Returns:
            Klines data including symbol, interval, and list of candles
        """
        # validate interval
        ValidInterval.validate(interval)

        # parse datetime strings if provided
        start_dt = datetime.fromisoformat(start_time) if start_time else None
        end_dt = datetime.fromisoformat(end_time) if end_time else None

        result = await client.get_klines(
            symbol=symbol.upper(),
            interval=interval,
            limit=limit,
            start_time=start_dt,
            end_time=end_dt,
        )
        return result.model_dump(mode="json")
