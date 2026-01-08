"""MCP tool for long/short ratio data."""

from datetime import datetime

from mcp.server.fastmcp import FastMCP

from crypto_mcp.exchanges.binance import BinanceClient
from crypto_mcp.models.common import ValidPeriod


def register_long_short_ratio_tools(mcp: FastMCP, client: BinanceClient) -> None:
    """Register long/short ratio tools with the MCP server."""

    @mcp.tool()
    async def get_long_short_ratio(
        symbol: str,
        period: str,
        limit: int = 30,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> list[dict]:
        """Get top trader long/short position ratio for a futures symbol.

        Shows the ratio of long vs short positions among top traders.
        A ratio > 1 means more longs than shorts. Useful for sentiment analysis.

        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT)
            period: Time interval between data points. Valid values:
                    5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d
            limit: Number of records to return (1-500, default 30)
            start_time: Start time in ISO format (e.g., 2024-01-01T00:00:00)
            end_time: End time in ISO format (e.g., 2024-01-02T00:00:00)

        Returns:
            List of long/short ratio records with ratio value, long/short account
            percentages, timestamp, and exchange
        """
        # validate period
        ValidPeriod.validate(period)

        # parse datetime strings if provided
        start_dt = datetime.fromisoformat(start_time) if start_time else None
        end_dt = datetime.fromisoformat(end_time) if end_time else None

        result = await client.get_long_short_ratio(
            symbol=symbol.upper(),
            period=period,
            limit=limit,
            start_time=start_dt,
            end_time=end_dt,
        )
        return [r.model_dump(mode="json") for r in result]
