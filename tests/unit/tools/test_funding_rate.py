"""Tests for funding rate MCP tools."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp.server.fastmcp import FastMCP

from crypto_mcp.models import FundingRateResponse
from crypto_mcp.tools.funding_rate import register_funding_rate_tools


@pytest.fixture
def mock_client():
    """Create a mock exchange client."""
    client = MagicMock()
    client.get_funding_rate = AsyncMock()
    return client


@pytest.fixture
def mock_clients(mock_client):
    """Create clients dict with mock client."""
    return {"binance": mock_client, "bybit": mock_client}


@pytest.fixture
def mcp_with_tools(mock_clients):
    """Create FastMCP instance with funding rate tools registered."""
    mcp = FastMCP("test-crypto")
    register_funding_rate_tools(mcp, mock_clients)
    return mcp


class TestGetFundingRate:
    """Tests for get_funding_rate tool."""

    @pytest.mark.asyncio
    async def test_with_symbol(self, mock_client, mcp_with_tools):
        mock_client.get_funding_rate.return_value = [
            FundingRateResponse(
                symbol="BTCUSDT",
                funding_rate=Decimal("0.00010000"),
                funding_time=1700000000000,
                mark_price=Decimal("45000.00"),
                exchange="binance",
            ),
        ]

        tool_fn = mcp_with_tools._tool_manager._tools["get_funding_rate"].fn
        result = await tool_fn(symbol="btcusdt")

        mock_client.get_funding_rate.assert_called_once_with(
            symbol="BTCUSDT",
            limit=100,
            start_time=None,
            end_time=None,
        )

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["funding_rate"] == "0.00010000"

    @pytest.mark.asyncio
    async def test_without_symbol(self, mock_client, mcp_with_tools):
        mock_client.get_funding_rate.return_value = [
            FundingRateResponse(
                symbol="BTCUSDT",
                funding_rate=Decimal("0.0001"),
                funding_time=1700000000000,
                exchange="binance",
            ),
            FundingRateResponse(
                symbol="ETHUSDT",
                funding_rate=Decimal("0.0002"),
                funding_time=1700000000000,
                exchange="binance",
            ),
        ]

        tool_fn = mcp_with_tools._tool_manager._tools["get_funding_rate"].fn
        result = await tool_fn(symbol=None)

        mock_client.get_funding_rate.assert_called_once_with(
            symbol=None,
            limit=100,
            start_time=None,
            end_time=None,
        )

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_with_time_params(self, mock_client, mcp_with_tools):
        mock_client.get_funding_rate.return_value = []

        tool_fn = mcp_with_tools._tool_manager._tools["get_funding_rate"].fn
        await tool_fn(
            symbol="BTCUSDT",
            limit=50,
            start_time="2024-01-01T00:00:00",
            end_time="2024-01-02T00:00:00",
        )

        call_args = mock_client.get_funding_rate.call_args
        assert call_args.kwargs["limit"] == 50
        assert call_args.kwargs["start_time"] == datetime(2024, 1, 1, 0, 0, 0)
        assert call_args.kwargs["end_time"] == datetime(2024, 1, 2, 0, 0, 0)

    @pytest.mark.asyncio
    async def test_tool_is_registered(self, mcp_with_tools):
        assert "get_funding_rate" in mcp_with_tools._tool_manager._tools
