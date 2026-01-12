"""MCP tools for crypto data.

This module provides functions to register all MCP tools with a FastMCP server.
"""

from mcp.server.fastmcp import FastMCP

from crypto_mcp.exchanges.base import BaseExchangeClient

from ._utils import SUPPORTED_EXCHANGES, get_client
from .funding_rate import register_funding_rate_tools
from .klines import register_klines_tools
from .long_short_ratio import register_long_short_ratio_tools
from .mark_price import register_mark_price_tools
from .open_interest import register_open_interest_tools
from .open_interest_history import register_open_interest_history_tools
from .ticker import register_ticker_tools


def register_all_tools(
    mcp: FastMCP,
    clients: dict[str, BaseExchangeClient],
) -> None:
    """Register all MCP tools with the server.

    Args:
        mcp: FastMCP server instance
        clients: Dict mapping exchange names to client instances
    """
    register_open_interest_tools(mcp, clients)
    register_mark_price_tools(mcp, clients)
    register_ticker_tools(mcp, clients)
    register_klines_tools(mcp, clients)
    register_funding_rate_tools(mcp, clients)
    register_open_interest_history_tools(mcp, clients)
    register_long_short_ratio_tools(mcp, clients)


__all__ = ["register_all_tools", "get_client", "SUPPORTED_EXCHANGES"]
