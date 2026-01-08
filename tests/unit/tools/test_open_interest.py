"""Tests for open interest MCP tools."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp.server.fastmcp import FastMCP

from crypto_mcp.models import OpenInterestResponse
from crypto_mcp.tools.open_interest import register_open_interest_tools


@pytest.fixture
def mock_client():
    """Create a mock BinanceClient."""
    client = MagicMock()
    client.get_open_interest = AsyncMock()
    return client


@pytest.fixture
def mcp_with_tools(mock_client):
    """Create FastMCP instance with open interest tools registered."""
    mcp = FastMCP("test-crypto")
    register_open_interest_tools(mcp, mock_client)
    return mcp


class TestGetOpenInterest:
    """Tests for get_open_interest tool."""

    @pytest.mark.asyncio
    async def test_calls_client_with_uppercase_symbol(self, mock_client, mcp_with_tools):
        mock_client.get_open_interest.return_value = OpenInterestResponse(
            symbol="BTCUSDT",
            open_interest=Decimal("12345.678"),
            timestamp=1700000000000,
            exchange="binance",
        )

        # access the registered tool function
        tool_fn = mcp_with_tools._tool_manager._tools["get_open_interest"].fn
        result = await tool_fn(symbol="btcusdt")

        # verify client called with uppercase symbol
        mock_client.get_open_interest.assert_called_once_with("BTCUSDT")

        # verify result is serialized dict
        assert isinstance(result, dict)
        assert result["symbol"] == "BTCUSDT"
        assert result["open_interest"] == "12345.678"
        assert result["exchange"] == "binance"

    @pytest.mark.asyncio
    async def test_returns_correct_structure(self, mock_client, mcp_with_tools):
        mock_client.get_open_interest.return_value = OpenInterestResponse(
            symbol="ETHUSDT",
            open_interest=Decimal("500000.0"),
            timestamp=1700001000000,
            exchange="binance",
        )

        tool_fn = mcp_with_tools._tool_manager._tools["get_open_interest"].fn
        result = await tool_fn(symbol="ETHUSDT")

        assert "symbol" in result
        assert "open_interest" in result
        assert "timestamp" in result
        assert "exchange" in result

    @pytest.mark.asyncio
    async def test_tool_is_registered(self, mcp_with_tools):
        """Verify the tool is properly registered with FastMCP."""
        assert "get_open_interest" in mcp_with_tools._tool_manager._tools

    @pytest.mark.asyncio
    async def test_propagates_client_errors(self, mock_client, mcp_with_tools):
        """Verify errors from client are propagated."""
        from crypto_mcp.exchanges.binance import BinanceAPIError

        mock_client.get_open_interest.side_effect = BinanceAPIError(
            "Invalid symbol", code=-1121
        )

        tool_fn = mcp_with_tools._tool_manager._tools["get_open_interest"].fn

        with pytest.raises(BinanceAPIError):
            await tool_fn(symbol="INVALID")
