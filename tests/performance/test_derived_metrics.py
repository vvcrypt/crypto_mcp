"""TDD tests for derived metrics tool (Improvement #5).

These tests define the expected behavior for:
- get_derived_metrics tool
- VWAP calculation
- Funding rate trend analysis
- OI change rate calculation

Tests are expected to fail until implementation is complete.
"""

from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from crypto_mcp.models import (
    KlinesResponse,
    Candle,
    FundingRateResponse,
    OpenInterestResponse,
)


class TestDerivedMetricsTool:
    """Tests for the get_derived_metrics tool."""

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="get_derived_metrics tool not yet implemented")
    async def test_tool_exists(self, mcp_server_with_mock):
        """get_derived_metrics tool should be registered."""
        mcp, _ = mcp_server_with_mock
        assert "get_derived_metrics" in mcp._tool_manager._tools

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="get_derived_metrics tool not yet implemented")
    async def test_returns_requested_metrics(self, mcp_server_with_mock):
        """Tool should return only the requested metrics."""
        mcp, mock_client = mcp_server_with_mock

        # setup mock data
        mock_client.get_klines.return_value = _create_sample_klines()
        mock_client.get_funding_rate.return_value = _create_sample_funding_rates()

        tool_fn = mcp._tool_manager._tools["get_derived_metrics"].fn
        result = await tool_fn(symbol="BTCUSDT", metrics=["vwap", "funding_trend"])

        assert "vwap" in result
        assert "funding_trend" in result
        assert "oi_change_rate" not in result  # not requested


class TestVWAPCalculation:
    """Tests for VWAP (Volume Weighted Average Price) calculation."""

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="VWAP calculation not yet implemented")
    async def test_vwap_calculation_is_correct(self, mcp_server_with_mock):
        """VWAP should be sum(price*volume) / sum(volume)."""
        mcp, mock_client = mcp_server_with_mock

        # create known test data
        mock_client.get_klines.return_value = KlinesResponse(
            symbol="BTCUSDT",
            interval="1h",
            candles=[
                Candle(
                    open_time=1700000000000,
                    open=Decimal("100"),
                    high=Decimal("110"),
                    low=Decimal("90"),
                    close=Decimal("105"),
                    volume=Decimal("10"),  # typical price ~100, vol 10
                    close_time=1700003599999,
                    quote_volume=Decimal("1000"),  # price*vol
                    trade_count=100,
                ),
                Candle(
                    open_time=1700003600000,
                    open=Decimal("105"),
                    high=Decimal("115"),
                    low=Decimal("100"),
                    close=Decimal("110"),
                    volume=Decimal("20"),  # typical price ~107, vol 20
                    close_time=1700007199999,
                    quote_volume=Decimal("2140"),  # price*vol
                    trade_count=200,
                ),
            ],
            exchange="binance",
        )

        tool_fn = mcp._tool_manager._tools["get_derived_metrics"].fn
        result = await tool_fn(symbol="BTCUSDT", metrics=["vwap"])

        # VWAP = (1000 + 2140) / (10 + 20) = 3140 / 30 = 104.67
        expected_vwap = Decimal("104.67")
        assert abs(result["vwap"] - expected_vwap) < Decimal("0.01")

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="VWAP calculation not yet implemented")
    async def test_vwap_uses_configurable_period(self, mcp_server_with_mock):
        """VWAP should accept period parameter."""
        mcp, mock_client = mcp_server_with_mock

        mock_client.get_klines.return_value = _create_sample_klines()

        tool_fn = mcp._tool_manager._tools["get_derived_metrics"].fn
        await tool_fn(symbol="BTCUSDT", metrics=["vwap"], vwap_period="4h")

        # verify klines were fetched with correct interval
        mock_client.get_klines.assert_called_once()
        call_kwargs = mock_client.get_klines.call_args.kwargs
        assert call_kwargs.get("interval") == "4h" or call_kwargs.get("interval") == "1h"


class TestFundingTrendAnalysis:
    """Tests for funding rate trend analysis."""

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="Funding trend analysis not yet implemented")
    async def test_funding_trend_returns_direction(self, mcp_server_with_mock):
        """Funding trend should return direction (bullish/bearish/neutral)."""
        mcp, mock_client = mcp_server_with_mock

        # increasing funding rates = bullish
        mock_client.get_funding_rate.return_value = [
            FundingRateResponse(
                symbol="BTCUSDT",
                funding_rate=Decimal("0.0001"),
                funding_time=1700000000000,
                exchange="binance",
            ),
            FundingRateResponse(
                symbol="BTCUSDT",
                funding_rate=Decimal("0.0002"),
                funding_time=1700028800000,
                exchange="binance",
            ),
            FundingRateResponse(
                symbol="BTCUSDT",
                funding_rate=Decimal("0.0003"),
                funding_time=1700057600000,
                exchange="binance",
            ),
        ]

        tool_fn = mcp._tool_manager._tools["get_derived_metrics"].fn
        result = await tool_fn(symbol="BTCUSDT", metrics=["funding_trend"])

        assert result["funding_trend"]["direction"] in ["bullish", "bearish", "neutral"]
        assert result["funding_trend"]["direction"] == "bullish"

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="Funding trend analysis not yet implemented")
    async def test_funding_trend_returns_strength(self, mcp_server_with_mock):
        """Funding trend should return strength indicator."""
        mcp, mock_client = mcp_server_with_mock

        mock_client.get_funding_rate.return_value = _create_sample_funding_rates()

        tool_fn = mcp._tool_manager._tools["get_derived_metrics"].fn
        result = await tool_fn(symbol="BTCUSDT", metrics=["funding_trend"])

        assert "strength" in result["funding_trend"]
        assert isinstance(result["funding_trend"]["strength"], (int, float, Decimal))


class TestOIChangeRate:
    """Tests for open interest change rate calculation."""

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="OI change rate not yet implemented")
    async def test_oi_change_rate_calculation(self, mcp_server_with_mock):
        """OI change rate should be percentage change over period."""
        mcp, mock_client = mcp_server_with_mock

        # OI went from 100000 to 110000 = 10% increase
        mock_client.get_open_interest_history.return_value = [
            OpenInterestResponse(
                symbol="BTCUSDT",
                open_interest=Decimal("100000"),
                timestamp=1700000000000,
                exchange="binance",
            ),
            OpenInterestResponse(
                symbol="BTCUSDT",
                open_interest=Decimal("110000"),
                timestamp=1700086400000,
                exchange="binance",
            ),
        ]

        tool_fn = mcp._tool_manager._tools["get_derived_metrics"].fn
        result = await tool_fn(symbol="BTCUSDT", metrics=["oi_change_rate"])

        assert result["oi_change_rate"] == Decimal("10.0")  # 10%

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="OI change rate not yet implemented")
    async def test_oi_change_handles_decrease(self, mcp_server_with_mock):
        """OI change rate should handle decreases (negative values)."""
        mcp, mock_client = mcp_server_with_mock

        # OI went from 100000 to 90000 = -10%
        mock_client.get_open_interest_history.return_value = [
            OpenInterestResponse(
                symbol="BTCUSDT",
                open_interest=Decimal("100000"),
                timestamp=1700000000000,
                exchange="binance",
            ),
            OpenInterestResponse(
                symbol="BTCUSDT",
                open_interest=Decimal("90000"),
                timestamp=1700086400000,
                exchange="binance",
            ),
        ]

        tool_fn = mcp._tool_manager._tools["get_derived_metrics"].fn
        result = await tool_fn(symbol="BTCUSDT", metrics=["oi_change_rate"])

        assert result["oi_change_rate"] == Decimal("-10.0")


class TestPriceOIDivergence:
    """Tests for price-OI divergence detection."""

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="Price-OI divergence not yet implemented")
    async def test_divergence_detected_when_price_up_oi_down(self, mcp_server_with_mock):
        """Should detect bearish divergence when price up but OI down."""
        mcp, mock_client = mcp_server_with_mock

        # price went up 10% but OI went down 5%
        mock_client.get_klines.return_value = _create_klines_with_price_change(10)
        mock_client.get_open_interest_history.return_value = _create_oi_with_change(-5)

        tool_fn = mcp._tool_manager._tools["get_derived_metrics"].fn
        result = await tool_fn(symbol="BTCUSDT", metrics=["price_oi_divergence"])

        assert result["price_oi_divergence"]["detected"] is True
        assert result["price_oi_divergence"]["type"] == "bearish"


# helper functions for creating test data

def _create_sample_klines() -> KlinesResponse:
    """Create sample klines data for testing."""
    return KlinesResponse(
        symbol="BTCUSDT",
        interval="1h",
        candles=[
            Candle(
                open_time=1700000000000 + i * 3600000,
                open=Decimal("45000") + i * 100,
                high=Decimal("45500") + i * 100,
                low=Decimal("44800") + i * 100,
                close=Decimal("45200") + i * 100,
                volume=Decimal("1000"),
                close_time=1700003599999 + i * 3600000,
                quote_volume=Decimal("45000000"),
                trade_count=5000,
            )
            for i in range(24)
        ],
        exchange="binance",
    )


def _create_sample_funding_rates() -> list[FundingRateResponse]:
    """Create sample funding rate data for testing."""
    return [
        FundingRateResponse(
            symbol="BTCUSDT",
            funding_rate=Decimal("0.0001") + Decimal("0.00001") * i,
            funding_time=1700000000000 + i * 28800000,  # 8 hours apart
            exchange="binance",
        )
        for i in range(10)
    ]


def _create_klines_with_price_change(percent_change: float) -> KlinesResponse:
    """Create klines showing a specific price change."""
    start_price = Decimal("45000")
    end_price = start_price * (1 + Decimal(str(percent_change)) / 100)

    return KlinesResponse(
        symbol="BTCUSDT",
        interval="1h",
        candles=[
            Candle(
                open_time=1700000000000,
                open=start_price,
                high=start_price + 500,
                low=start_price - 200,
                close=start_price + 100,
                volume=Decimal("1000"),
                close_time=1700003599999,
                quote_volume=Decimal("45000000"),
                trade_count=5000,
            ),
            Candle(
                open_time=1700086400000,
                open=end_price - 100,
                high=end_price + 200,
                low=end_price - 300,
                close=end_price,
                volume=Decimal("1000"),
                close_time=1700089999999,
                quote_volume=Decimal("45000000"),
                trade_count=5000,
            ),
        ],
        exchange="binance",
    )


def _create_oi_with_change(percent_change: float) -> list[OpenInterestResponse]:
    """Create OI history showing a specific change."""
    start_oi = Decimal("100000")
    end_oi = start_oi * (1 + Decimal(str(percent_change)) / 100)

    return [
        OpenInterestResponse(
            symbol="BTCUSDT",
            open_interest=start_oi,
            timestamp=1700000000000,
            exchange="binance",
        ),
        OpenInterestResponse(
            symbol="BTCUSDT",
            open_interest=end_oi,
            timestamp=1700086400000,
            exchange="binance",
        ),
    ]
