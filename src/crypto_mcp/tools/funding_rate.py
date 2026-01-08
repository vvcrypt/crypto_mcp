"""MCP tool for funding rate data."""

from datetime import datetime

from mcp.server.fastmcp import FastMCP

from crypto_mcp.exchanges.binance import BinanceClient


def register_funding_rate_tools(mcp: FastMCP, client: BinanceClient) -> None:
    """Register funding rate tools with the MCP server."""

    @mcp.tool()
    async def get_funding_rate(
        symbol: str | None = None,
        limit: int = 100,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> list[dict]:
        """Get funding rate history for futures symbols.

        Funding rate is the periodic payment between longs and shorts to keep
        futures price close to spot. Positive rate means longs pay shorts.
        Funding occurs every 8 hours on Binance.

        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT). If None, returns multiple symbols.
            limit: Number of records to return (1-1000, default 100)
            start_time: Start time in ISO format (e.g., 2024-01-01T00:00:00)
            end_time: End time in ISO format (e.g., 2024-01-02T00:00:00)

        Returns:
            List of funding rate records with symbol, rate, funding time, and mark price
        """
        # parse datetime strings if provided
        start_dt = datetime.fromisoformat(start_time) if start_time else None
        end_dt = datetime.fromisoformat(end_time) if end_time else None

        result = await client.get_funding_rate(
            symbol=symbol.upper() if symbol else None,
            limit=limit,
            start_time=start_dt,
            end_time=end_dt,
        )
        return [r.model_dump(mode="json") for r in result]
