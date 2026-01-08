"""Integration tests for the MCP server."""

from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
import httpx

from mcp.server.fastmcp import FastMCP

from crypto_mcp.config import Settings
from crypto_mcp.exchanges.binance import BinanceClient
from crypto_mcp.tools import register_all_tools


# expected tool names
EXPECTED_TOOLS = [
    "get_open_interest",
    "get_mark_price",
    "get_ticker_24h",
    "get_klines",
    "get_klines_batch",
    "get_funding_rate",
    "get_open_interest_history",
    "get_open_interest_history_batch",
    "get_long_short_ratio",
]


class TestServerToolRegistration:
    """Tests for tool registration on server startup."""

    @pytest.fixture
    def mcp_server(self):
        """Create an MCP server with all tools registered."""
        mcp = FastMCP("test-crypto-server")
        mock_client = AsyncMock(spec=BinanceClient)
        register_all_tools(mcp, mock_client)
        return mcp, mock_client

    def test_all_tools_registered(self, mcp_server):
        """Verify all expected tools are registered."""
        mcp, _ = mcp_server
        registered_tools = set(mcp._tool_manager._tools.keys())

        for tool_name in EXPECTED_TOOLS:
            assert tool_name in registered_tools, f"Tool {tool_name} not registered"

    def test_correct_number_of_tools(self, mcp_server):
        """Verify exactly 9 tools are registered."""
        mcp, _ = mcp_server
        assert len(mcp._tool_manager._tools) == 9


class TestServerImport:
    """Tests for server module imports."""

    def test_server_module_imports(self):
        """Verify server module can be imported without errors."""
        from crypto_mcp import server
        assert hasattr(server, "mcp")
        assert hasattr(server, "lifespan")
        assert hasattr(server, "settings")

    def test_main_module_imports(self):
        """Verify __main__ module can be imported."""
        from crypto_mcp import __main__
        assert hasattr(__main__, "mcp")


class TestToolExecution:
    """Tests for executing tools through the server."""

    @pytest.fixture
    def mcp_with_mock_client(self):
        """Create MCP server with mock client that returns test data."""
        mcp = FastMCP("test-execution")
        mock_client = AsyncMock(spec=BinanceClient)
        register_all_tools(mcp, mock_client)
        return mcp, mock_client

    @pytest.mark.asyncio
    async def test_open_interest_tool_execution(self, mcp_with_mock_client):
        """Test executing get_open_interest tool."""
        from crypto_mcp.models import OpenInterestResponse

        mcp, mock_client = mcp_with_mock_client
        mock_client.get_open_interest.return_value = OpenInterestResponse(
            symbol="BTCUSDT",
            open_interest=Decimal("50000.0"),
            timestamp=1700000000000,
            exchange="binance",
        )

        tool_fn = mcp._tool_manager._tools["get_open_interest"].fn
        result = await tool_fn(symbol="BTCUSDT")

        assert result["symbol"] == "BTCUSDT"
        assert result["exchange"] == "binance"

    @pytest.mark.asyncio
    async def test_mark_price_tool_execution(self, mcp_with_mock_client):
        """Test executing get_mark_price tool."""
        from crypto_mcp.models import MarkPriceResponse

        mcp, mock_client = mcp_with_mock_client
        mock_client.get_mark_price.return_value = [
            MarkPriceResponse(
                symbol="BTCUSDT",
                mark_price=Decimal("45000.00"),
                index_price=Decimal("44999.50"),
                estimated_settle_price=Decimal("45000.00"),
                last_funding_rate=Decimal("0.0001"),
                next_funding_time=1700003600000,
                interest_rate=Decimal("0.0003"),
                timestamp=1700000000000,
                exchange="binance",
            )
        ]

        tool_fn = mcp._tool_manager._tools["get_mark_price"].fn
        result = await tool_fn(symbol="BTCUSDT")

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["symbol"] == "BTCUSDT"

    @pytest.mark.asyncio
    async def test_klines_tool_execution(self, mcp_with_mock_client):
        """Test executing get_klines tool."""
        from crypto_mcp.models import KlinesResponse, Candle

        mcp, mock_client = mcp_with_mock_client
        mock_client.get_klines.return_value = KlinesResponse(
            symbol="BTCUSDT",
            interval="1h",
            candles=[
                Candle(
                    open_time=1700000000000,
                    open=Decimal("45000.00"),
                    high=Decimal("45500.00"),
                    low=Decimal("44800.00"),
                    close=Decimal("45200.00"),
                    volume=Decimal("1000.0"),
                    close_time=1700003599999,
                    quote_volume=Decimal("45000000.00"),
                    trade_count=5000,
                    taker_buy_volume=Decimal("500.0"),
                    taker_buy_quote_volume=Decimal("22500000.00"),
                )
            ],
            exchange="binance",
        )

        tool_fn = mcp._tool_manager._tools["get_klines"].fn
        result = await tool_fn(symbol="BTCUSDT", interval="1h")

        assert result["symbol"] == "BTCUSDT"
        assert result["interval"] == "1h"
        assert len(result["candles"]) == 1
