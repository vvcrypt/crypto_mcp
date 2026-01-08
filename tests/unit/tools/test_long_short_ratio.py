"""Tests for long/short ratio MCP tools."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp.server.fastmcp import FastMCP

from crypto_mcp.exceptions import ValidationError
from crypto_mcp.models import LongShortRatioResponse
from crypto_mcp.tools.long_short_ratio import register_long_short_ratio_tools


@pytest.fixture
def mock_client():
    """Create a mock BinanceClient."""
    client = MagicMock()
    client.get_long_short_ratio = AsyncMock()
    return client


@pytest.fixture
def mcp_with_tools(mock_client):
    """Create FastMCP instance with long/short ratio tools registered."""
    mcp = FastMCP("test-crypto")
    register_long_short_ratio_tools(mcp, mock_client)
    return mcp


class TestGetLongShortRatio:
    """Tests for get_long_short_ratio tool."""

    @pytest.mark.asyncio
    async def test_basic_call(self, mock_client, mcp_with_tools):
        mock_client.get_long_short_ratio.return_value = [
            LongShortRatioResponse(
                symbol="BTCUSDT",
                long_short_ratio=Decimal("1.2500"),
                long_account=Decimal("0.5556"),
                short_account=Decimal("0.4444"),
                timestamp=1700000000000,
                exchange="binance",
            ),
        ]

        tool_fn = mcp_with_tools._tool_manager._tools["get_long_short_ratio"].fn
        result = await tool_fn(symbol="btcusdt", period="5m")

        mock_client.get_long_short_ratio.assert_called_once_with(
            symbol="BTCUSDT",
            period="5m",
            limit=30,
            start_time=None,
            end_time=None,
        )

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["long_short_ratio"] == "1.2500"
        assert result[0]["long_account"] == "0.5556"
        assert result[0]["short_account"] == "0.4444"

    @pytest.mark.asyncio
    async def test_with_time_params(self, mock_client, mcp_with_tools):
        mock_client.get_long_short_ratio.return_value = []

        tool_fn = mcp_with_tools._tool_manager._tools["get_long_short_ratio"].fn
        await tool_fn(
            symbol="BTCUSDT",
            period="1h",
            limit=100,
            start_time="2024-01-01T00:00:00",
            end_time="2024-01-02T00:00:00",
        )

        call_args = mock_client.get_long_short_ratio.call_args
        assert call_args.kwargs["limit"] == 100
        assert call_args.kwargs["start_time"] == datetime(2024, 1, 1, 0, 0, 0)
        assert call_args.kwargs["end_time"] == datetime(2024, 1, 2, 0, 0, 0)

    @pytest.mark.asyncio
    async def test_invalid_period(self, mock_client, mcp_with_tools):
        tool_fn = mcp_with_tools._tool_manager._tools["get_long_short_ratio"].fn

        with pytest.raises(ValidationError) as exc_info:
            await tool_fn(symbol="BTCUSDT", period="invalid")

        assert "Invalid period" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_tool_is_registered(self, mcp_with_tools):
        assert "get_long_short_ratio" in mcp_with_tools._tool_manager._tools
