"""TDD tests for exchange info tool (Improvement #9).

These tests define the expected behavior for:
- get_exchange_info tool
- Symbol information retrieval
- Trading rules and constraints

Tests are expected to fail until implementation is complete.
"""

from decimal import Decimal
from unittest.mock import AsyncMock

import pytest


class TestExchangeInfoTool:
    """Tests for get_exchange_info tool."""

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="get_exchange_info tool not yet implemented")
    async def test_tool_exists(self, mcp_server_with_mock):
        """get_exchange_info tool should be registered."""
        mcp, _ = mcp_server_with_mock
        assert "get_exchange_info" in mcp._tool_manager._tools

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="get_exchange_info tool not yet implemented")
    async def test_returns_symbol_info(self, mcp_server_with_mock):
        """Tool should return symbol information."""
        mcp, mock_client = mcp_server_with_mock

        mock_client.get_exchange_info = AsyncMock(
            return_value={
                "symbol": "BTCUSDT",
                "price_precision": 2,
                "quantity_precision": 3,
                "base_asset": "BTC",
                "quote_asset": "USDT",
            }
        )

        tool_fn = mcp._tool_manager._tools["get_exchange_info"].fn
        result = await tool_fn(symbol="BTCUSDT")

        assert result["symbol"] == "BTCUSDT"

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="get_exchange_info tool not yet implemented")
    async def test_returns_all_symbols_when_no_symbol_specified(
        self, mcp_server_with_mock
    ):
        """Tool should return all symbols when no symbol specified."""
        mcp, mock_client = mcp_server_with_mock

        mock_client.get_exchange_info = AsyncMock(
            return_value=[
                {"symbol": "BTCUSDT", "price_precision": 2},
                {"symbol": "ETHUSDT", "price_precision": 2},
            ]
        )

        tool_fn = mcp._tool_manager._tools["get_exchange_info"].fn
        result = await tool_fn()

        assert isinstance(result, list)
        assert len(result) >= 2


class TestExchangeInfoFields:
    """Tests for exchange info response fields."""

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="get_exchange_info tool not yet implemented")
    async def test_price_precision(self, mcp_server_with_mock):
        """Response should include price_precision."""
        mcp, mock_client = mcp_server_with_mock

        mock_client.get_exchange_info = AsyncMock(
            return_value={"symbol": "BTCUSDT", "price_precision": 2}
        )

        tool_fn = mcp._tool_manager._tools["get_exchange_info"].fn
        result = await tool_fn(symbol="BTCUSDT")

        assert "price_precision" in result
        assert isinstance(result["price_precision"], int)

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="get_exchange_info tool not yet implemented")
    async def test_quantity_precision(self, mcp_server_with_mock):
        """Response should include quantity_precision."""
        mcp, mock_client = mcp_server_with_mock

        mock_client.get_exchange_info = AsyncMock(
            return_value={"symbol": "BTCUSDT", "quantity_precision": 3}
        )

        tool_fn = mcp._tool_manager._tools["get_exchange_info"].fn
        result = await tool_fn(symbol="BTCUSDT")

        assert "quantity_precision" in result
        assert isinstance(result["quantity_precision"], int)

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="get_exchange_info tool not yet implemented")
    async def test_tick_size(self, mcp_server_with_mock):
        """Response should include tick_size (minimum price increment)."""
        mcp, mock_client = mcp_server_with_mock

        mock_client.get_exchange_info = AsyncMock(
            return_value={"symbol": "BTCUSDT", "tick_size": Decimal("0.01")}
        )

        tool_fn = mcp._tool_manager._tools["get_exchange_info"].fn
        result = await tool_fn(symbol="BTCUSDT")

        assert "tick_size" in result

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="get_exchange_info tool not yet implemented")
    async def test_step_size(self, mcp_server_with_mock):
        """Response should include step_size (minimum quantity increment)."""
        mcp, mock_client = mcp_server_with_mock

        mock_client.get_exchange_info = AsyncMock(
            return_value={"symbol": "BTCUSDT", "step_size": Decimal("0.001")}
        )

        tool_fn = mcp._tool_manager._tools["get_exchange_info"].fn
        result = await tool_fn(symbol="BTCUSDT")

        assert "step_size" in result

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="get_exchange_info tool not yet implemented")
    async def test_min_notional(self, mcp_server_with_mock):
        """Response should include min_notional (minimum order value)."""
        mcp, mock_client = mcp_server_with_mock

        mock_client.get_exchange_info = AsyncMock(
            return_value={"symbol": "BTCUSDT", "min_notional": Decimal("5.0")}
        )

        tool_fn = mcp._tool_manager._tools["get_exchange_info"].fn
        result = await tool_fn(symbol="BTCUSDT")

        assert "min_notional" in result


class TestExchangeInfoClient:
    """Tests for BinanceClient.get_exchange_info method."""

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="get_exchange_info not yet implemented in client")
    async def test_client_method_exists(self):
        """BinanceClient should have get_exchange_info method."""
        from crypto_mcp.exchanges.binance import BinanceClient

        assert hasattr(BinanceClient, "get_exchange_info")

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="get_exchange_info not yet implemented in client")
    async def test_client_calls_correct_endpoint(self):
        """Client should call /fapi/v1/exchangeInfo endpoint."""
        from crypto_mcp.exchanges.binance.endpoints import EXCHANGE_INFO

        assert EXCHANGE_INFO == "/fapi/v1/exchangeInfo"


class TestExchangeInfoResponseModel:
    """Tests for ExchangeInfoResponse model."""

    @pytest.mark.xfail(reason="ExchangeInfoResponse model not yet implemented")
    def test_model_exists(self):
        """ExchangeInfoResponse model should exist."""
        from crypto_mcp.models import ExchangeInfoResponse

        assert ExchangeInfoResponse is not None

    @pytest.mark.xfail(reason="ExchangeInfoResponse model not yet implemented")
    def test_model_has_expected_fields(self):
        """ExchangeInfoResponse should have expected fields."""
        from crypto_mcp.models import ExchangeInfoResponse

        response = ExchangeInfoResponse(
            symbol="BTCUSDT",
            price_precision=2,
            quantity_precision=3,
            base_asset="BTC",
            quote_asset="USDT",
            tick_size=Decimal("0.01"),
            step_size=Decimal("0.001"),
            min_notional=Decimal("5.0"),
            exchange="binance",
        )

        assert response.symbol == "BTCUSDT"
        assert response.price_precision == 2
        assert response.quantity_precision == 3


class TestExchangeInfoCaching:
    """Tests for exchange info caching (should be cached longer than market data)."""

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="Exchange info caching not yet implemented")
    async def test_exchange_info_is_cached(self, mcp_server_with_mock):
        """Exchange info should be cached (doesn't change frequently)."""
        mcp, mock_client = mcp_server_with_mock

        mock_client.get_exchange_info = AsyncMock(
            return_value={"symbol": "BTCUSDT", "price_precision": 2}
        )

        tool_fn = mcp._tool_manager._tools["get_exchange_info"].fn

        await tool_fn(symbol="BTCUSDT")
        await tool_fn(symbol="BTCUSDT")

        # should only call once due to caching
        assert mock_client.get_exchange_info.call_count == 1

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="Exchange info caching not yet implemented")
    async def test_exchange_info_cache_has_longer_ttl(self):
        """Exchange info cache should have longer TTL than market data."""
        from crypto_mcp.config import Settings

        settings = Settings()

        # exchange info TTL should be much longer (e.g., 1 hour vs 3 seconds)
        assert settings.exchange_info_cache_ttl >= 3600  # 1 hour
