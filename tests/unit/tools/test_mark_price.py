"""Tests for mark price MCP tools."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp.server.fastmcp import FastMCP

from crypto_mcp.models import MarkPriceResponse
from crypto_mcp.tools.mark_price import register_mark_price_tools


@pytest.fixture
def mock_client():
    """Create a mock exchange client."""
    client = MagicMock()
    client.get_mark_price = AsyncMock()
    return client


@pytest.fixture
def mock_clients(mock_client):
    """Create clients dict with mock client."""
    return {"binance": mock_client, "bybit": mock_client}


@pytest.fixture
def mcp_with_tools(mock_clients):
    """Create FastMCP instance with mark price tools registered."""
    mcp = FastMCP("test-crypto")
    register_mark_price_tools(mcp, mock_clients)
    return mcp


class TestGetMarkPrice:
    """Tests for get_mark_price tool."""

    @pytest.mark.asyncio
    async def test_single_symbol(self, mock_client, mcp_with_tools):
        mock_client.get_mark_price.return_value = MarkPriceResponse(
            symbol="BTCUSDT",
            mark_price=Decimal("45000.00"),
            index_price=Decimal("44999.50"),
            last_funding_rate=Decimal("0.00010000"),
            next_funding_time=1700000000000,
            exchange="binance",
        )

        tool_fn = mcp_with_tools._tool_manager._tools["get_mark_price"].fn
        result = await tool_fn(symbol="btcusdt")

        mock_client.get_mark_price.assert_called_once_with("BTCUSDT")

        assert isinstance(result, dict)
        assert result["symbol"] == "BTCUSDT"
        assert result["mark_price"] == "45000.00"
        assert result["index_price"] == "44999.50"
        assert result["last_funding_rate"] == "0.00010000"

    @pytest.mark.asyncio
    async def test_all_symbols(self, mock_client, mcp_with_tools):
        mock_client.get_mark_price.return_value = [
            MarkPriceResponse(
                symbol="BTCUSDT",
                mark_price=Decimal("45000.00"),
                index_price=Decimal("44999.50"),
                last_funding_rate=Decimal("0.00010000"),
                next_funding_time=1700000000000,
                exchange="binance",
            ),
            MarkPriceResponse(
                symbol="ETHUSDT",
                mark_price=Decimal("2500.00"),
                index_price=Decimal("2499.50"),
                last_funding_rate=Decimal("0.00005000"),
                next_funding_time=1700000000000,
                exchange="binance",
            ),
        ]

        tool_fn = mcp_with_tools._tool_manager._tools["get_mark_price"].fn
        result = await tool_fn(symbol=None)

        mock_client.get_mark_price.assert_called_once_with(None)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["symbol"] == "BTCUSDT"
        assert result[1]["symbol"] == "ETHUSDT"

    @pytest.mark.asyncio
    async def test_tool_is_registered(self, mcp_with_tools):
        assert "get_mark_price" in mcp_with_tools._tool_manager._tools
