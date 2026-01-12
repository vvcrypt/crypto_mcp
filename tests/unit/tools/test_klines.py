"""Tests for klines MCP tools."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp.server.fastmcp import FastMCP

from crypto_mcp.exceptions import ValidationError
from crypto_mcp.models import Candle, KlinesResponse
from crypto_mcp.tools.klines import register_klines_tools


@pytest.fixture
def mock_client():
    """Create a mock exchange client."""
    client = MagicMock()
    client.get_klines = AsyncMock()
    return client


@pytest.fixture
def mock_clients(mock_client):
    """Create clients dict with mock client."""
    return {"binance": mock_client, "bybit": mock_client}


@pytest.fixture
def mcp_with_tools(mock_clients):
    """Create FastMCP instance with klines tools registered."""
    mcp = FastMCP("test-crypto")
    register_klines_tools(mcp, mock_clients)
    return mcp


def make_klines_response() -> KlinesResponse:
    """Create a sample KlinesResponse."""
    return KlinesResponse(
        symbol="BTCUSDT",
        interval="1h",
        candles=[
            Candle(
                open_time=1700000000000,
                open=Decimal("45000.00"),
                high=Decimal("45500.00"),
                low=Decimal("44800.00"),
                close=Decimal("45200.00"),
                volume=Decimal("1234.567"),
                close_time=1700003600000,
                quote_volume=Decimal("55555555.00"),
                trade_count=5000,
            ),
        ],
        exchange="binance",
    )


class TestGetKlines:
    """Tests for get_klines tool."""

    @pytest.mark.asyncio
    async def test_basic_call(self, mock_client, mcp_with_tools):
        mock_client.get_klines.return_value = make_klines_response()

        tool_fn = mcp_with_tools._tool_manager._tools["get_klines"].fn
        result = await tool_fn(symbol="btcusdt", interval="1h")

        mock_client.get_klines.assert_called_once_with(
            symbol="BTCUSDT",
            interval="1h",
            limit=500,
            start_time=None,
            end_time=None,
        )

        assert isinstance(result, dict)
        assert result["symbol"] == "BTCUSDT"
        assert result["interval"] == "1h"
        assert len(result["candles"]) == 1

    @pytest.mark.asyncio
    async def test_with_time_params(self, mock_client, mcp_with_tools):
        mock_client.get_klines.return_value = make_klines_response()

        tool_fn = mcp_with_tools._tool_manager._tools["get_klines"].fn
        result = await tool_fn(
            symbol="BTCUSDT",
            interval="4h",
            limit=100,
            start_time="2024-01-01T00:00:00",
            end_time="2024-01-02T00:00:00",
        )

        call_args = mock_client.get_klines.call_args
        assert call_args.kwargs["symbol"] == "BTCUSDT"
        assert call_args.kwargs["limit"] == 100
        assert call_args.kwargs["start_time"] == datetime(2024, 1, 1, 0, 0, 0)
        assert call_args.kwargs["end_time"] == datetime(2024, 1, 2, 0, 0, 0)

    @pytest.mark.asyncio
    async def test_invalid_interval(self, mock_client, mcp_with_tools):
        tool_fn = mcp_with_tools._tool_manager._tools["get_klines"].fn

        with pytest.raises(ValidationError) as exc_info:
            await tool_fn(symbol="BTCUSDT", interval="invalid")

        assert "Invalid interval" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_tool_is_registered(self, mcp_with_tools):
        assert "get_klines" in mcp_with_tools._tool_manager._tools
