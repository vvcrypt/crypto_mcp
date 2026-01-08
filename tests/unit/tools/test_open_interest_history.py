"""Tests for open interest history MCP tools."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp.server.fastmcp import FastMCP

from crypto_mcp.exceptions import ValidationError
from crypto_mcp.models import OpenInterestResponse
from crypto_mcp.tools.open_interest_history import register_open_interest_history_tools


@pytest.fixture
def mock_client():
    """Create a mock BinanceClient."""
    client = MagicMock()
    client.get_open_interest_history = AsyncMock()
    return client


@pytest.fixture
def mcp_with_tools(mock_client):
    """Create FastMCP instance with open interest history tools registered."""
    mcp = FastMCP("test-crypto")
    register_open_interest_history_tools(mcp, mock_client)
    return mcp


class TestGetOpenInterestHistory:
    """Tests for get_open_interest_history tool."""

    @pytest.mark.asyncio
    async def test_basic_call(self, mock_client, mcp_with_tools):
        mock_client.get_open_interest_history.return_value = [
            OpenInterestResponse(
                symbol="BTCUSDT",
                open_interest=Decimal("12345.0"),
                timestamp=1700000000000,
                exchange="binance",
            ),
            OpenInterestResponse(
                symbol="BTCUSDT",
                open_interest=Decimal("12346.0"),
                timestamp=1700000300000,
                exchange="binance",
            ),
        ]

        tool_fn = mcp_with_tools._tool_manager._tools["get_open_interest_history"].fn
        result = await tool_fn(symbol="btcusdt", period="5m")

        mock_client.get_open_interest_history.assert_called_once_with(
            symbol="BTCUSDT",
            period="5m",
            limit=30,
            start_time=None,
            end_time=None,
        )

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["open_interest"] == "12345.0"

    @pytest.mark.asyncio
    async def test_with_time_params(self, mock_client, mcp_with_tools):
        mock_client.get_open_interest_history.return_value = []

        tool_fn = mcp_with_tools._tool_manager._tools["get_open_interest_history"].fn
        await tool_fn(
            symbol="BTCUSDT",
            period="1h",
            limit=100,
            start_time="2024-01-01T00:00:00",
            end_time="2024-01-02T00:00:00",
        )

        call_args = mock_client.get_open_interest_history.call_args
        assert call_args.kwargs["limit"] == 100
        assert call_args.kwargs["start_time"] == datetime(2024, 1, 1, 0, 0, 0)
        assert call_args.kwargs["end_time"] == datetime(2024, 1, 2, 0, 0, 0)

    @pytest.mark.asyncio
    async def test_invalid_period(self, mock_client, mcp_with_tools):
        tool_fn = mcp_with_tools._tool_manager._tools["get_open_interest_history"].fn

        with pytest.raises(ValidationError) as exc_info:
            await tool_fn(symbol="BTCUSDT", period="invalid")

        assert "Invalid period" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_tool_is_registered(self, mcp_with_tools):
        assert "get_open_interest_history" in mcp_with_tools._tool_manager._tools
