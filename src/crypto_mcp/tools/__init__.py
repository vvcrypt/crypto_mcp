"""MCP tools for crypto data.

This module provides functions to register all MCP tools with a FastMCP server.
"""

from mcp.server.fastmcp import FastMCP

from crypto_mcp.exchanges.binance import BinanceClient

from .funding_rate import register_funding_rate_tools
from .klines import register_klines_tools
from .long_short_ratio import register_long_short_ratio_tools
from .mark_price import register_mark_price_tools
from .open_interest import register_open_interest_tools
from .open_interest_history import register_open_interest_history_tools
from .ticker import register_ticker_tools


def register_all_tools(mcp: FastMCP, client: BinanceClient) -> None:
    """Register all MCP tools with the server.

    Args:
        mcp: FastMCP server instance
        client: Exchange client to use for API calls
    """
    register_open_interest_tools(mcp, client)
    register_mark_price_tools(mcp, client)
    register_ticker_tools(mcp, client)
    register_klines_tools(mcp, client)
    register_funding_rate_tools(mcp, client)
    register_open_interest_history_tools(mcp, client)
    register_long_short_ratio_tools(mcp, client)


__all__ = ["register_all_tools"]
