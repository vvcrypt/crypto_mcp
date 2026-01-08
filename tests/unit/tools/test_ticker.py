"""Tests for 24h ticker MCP tools."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp.server.fastmcp import FastMCP

from crypto_mcp.models import TickerResponse
from crypto_mcp.tools.ticker import register_ticker_tools


@pytest.fixture
def mock_client():
    """Create a mock BinanceClient."""
    client = MagicMock()
    client.get_ticker_24h = AsyncMock()
    return client


@pytest.fixture
def mcp_with_tools(mock_client):
    """Create FastMCP instance with ticker tools registered."""
    mcp = FastMCP("test-crypto")
    register_ticker_tools(mcp, mock_client)
    return mcp


def make_ticker_response(symbol: str = "BTCUSDT") -> TickerResponse:
    """Create a sample TickerResponse."""
    return TickerResponse(
        symbol=symbol,
        price_change=Decimal("1000.50"),
        price_change_percent=Decimal("2.35"),
        last_price=Decimal("43500.00"),
        volume=Decimal("50000.00"),
        quote_volume=Decimal("2175000000.00"),
        high_price=Decimal("44000.00"),
        low_price=Decimal("42000.00"),
        open_price=Decimal("42500.00"),
        open_time=1700000000000,
        close_time=1700086400000,
        trade_count=1500000,
        exchange="binance",
    )


class TestGetTicker24h:
    """Tests for get_ticker_24h tool."""

    @pytest.mark.asyncio
    async def test_single_symbol(self, mock_client, mcp_with_tools):
        mock_client.get_ticker_24h.return_value = make_ticker_response("BTCUSDT")

        tool_fn = mcp_with_tools._tool_manager._tools["get_ticker_24h"].fn
        result = await tool_fn(symbol="btcusdt")

        mock_client.get_ticker_24h.assert_called_once_with("BTCUSDT")

        assert isinstance(result, dict)
        assert result["symbol"] == "BTCUSDT"
        assert result["price_change"] == "1000.50"
        assert result["volume"] == "50000.00"

    @pytest.mark.asyncio
    async def test_all_symbols(self, mock_client, mcp_with_tools):
        mock_client.get_ticker_24h.return_value = [
            make_ticker_response("BTCUSDT"),
            make_ticker_response("ETHUSDT"),
        ]

        tool_fn = mcp_with_tools._tool_manager._tools["get_ticker_24h"].fn
        result = await tool_fn(symbol=None)

        mock_client.get_ticker_24h.assert_called_once_with(None)

        assert isinstance(result, list)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_tool_is_registered(self, mcp_with_tools):
        assert "get_ticker_24h" in mcp_with_tools._tool_manager._tools
