"""TDD tests for extended data fields (Improvement #4).

These tests define the expected behavior for additional response fields:
- MarkPriceResponse: estimated_settle_price, interest_rate, timestamp
- OpenInterestResponse: open_interest_value (USD notional)
- Candle: taker_buy_volume, taker_buy_quote_volume

Tests are expected to fail until implementations are complete.
"""

from decimal import Decimal

import pytest

from crypto_mcp.models import (
    MarkPriceResponse,
    OpenInterestResponse,
    Candle,
    KlinesResponse,
)


class TestMarkPriceExtendedFields:
    """Tests for extended MarkPriceResponse fields."""

    @pytest.mark.xfail(reason="Extended fields not yet added to MarkPriceResponse")
    def test_mark_price_has_estimated_settle_price(self):
        """MarkPriceResponse should include estimated_settle_price."""
        response = MarkPriceResponse(
            symbol="BTCUSDT",
            mark_price=Decimal("45000.00"),
            index_price=Decimal("44999.50"),
            last_funding_rate=Decimal("0.0001"),
            next_funding_time=1700003600000,
            estimated_settle_price=Decimal("45001.00"),
            exchange="binance",
        )

        assert response.estimated_settle_price == Decimal("45001.00")

    @pytest.mark.xfail(reason="Extended fields not yet added to MarkPriceResponse")
    def test_mark_price_has_interest_rate(self):
        """MarkPriceResponse should include interest_rate."""
        response = MarkPriceResponse(
            symbol="BTCUSDT",
            mark_price=Decimal("45000.00"),
            index_price=Decimal("44999.50"),
            last_funding_rate=Decimal("0.0001"),
            next_funding_time=1700003600000,
            interest_rate=Decimal("0.0003"),
            exchange="binance",
        )

        assert response.interest_rate == Decimal("0.0003")

    @pytest.mark.xfail(reason="Extended fields not yet added to MarkPriceResponse")
    def test_mark_price_has_timestamp(self):
        """MarkPriceResponse should include timestamp."""
        response = MarkPriceResponse(
            symbol="BTCUSDT",
            mark_price=Decimal("45000.00"),
            index_price=Decimal("44999.50"),
            last_funding_rate=Decimal("0.0001"),
            next_funding_time=1700003600000,
            timestamp=1700000000000,
            exchange="binance",
        )

        assert response.timestamp == 1700000000000

    @pytest.mark.xfail(reason="Extended fields not yet added to MarkPriceResponse")
    def test_extended_fields_are_optional(self):
        """Extended fields should be optional (None by default)."""
        response = MarkPriceResponse(
            symbol="BTCUSDT",
            mark_price=Decimal("45000.00"),
            index_price=Decimal("44999.50"),
            last_funding_rate=Decimal("0.0001"),
            next_funding_time=1700003600000,
            exchange="binance",
        )

        assert response.estimated_settle_price is None
        assert response.interest_rate is None
        assert response.timestamp is None


class TestOpenInterestExtendedFields:
    """Tests for extended OpenInterestResponse fields."""

    @pytest.mark.xfail(reason="open_interest_value not yet added to OpenInterestResponse")
    def test_open_interest_has_value_field(self):
        """OpenInterestResponse should include open_interest_value (USD)."""
        response = OpenInterestResponse(
            symbol="BTCUSDT",
            open_interest=Decimal("100000.0"),
            open_interest_value=Decimal("4500000000.00"),  # USD notional
            timestamp=1700000000000,
            exchange="binance",
        )

        assert response.open_interest_value == Decimal("4500000000.00")

    @pytest.mark.xfail(reason="open_interest_value not yet added to OpenInterestResponse")
    def test_open_interest_value_is_optional(self):
        """open_interest_value should be optional."""
        response = OpenInterestResponse(
            symbol="BTCUSDT",
            open_interest=Decimal("100000.0"),
            timestamp=1700000000000,
            exchange="binance",
        )

        assert response.open_interest_value is None


class TestCandleExtendedFields:
    """Tests for extended Candle fields."""

    @pytest.mark.xfail(reason="Taker fields not yet added to Candle")
    def test_candle_has_taker_buy_volume(self):
        """Candle should include taker_buy_volume."""
        candle = Candle(
            open_time=1700000000000,
            open=Decimal("45000.00"),
            high=Decimal("45500.00"),
            low=Decimal("44800.00"),
            close=Decimal("45200.00"),
            volume=Decimal("1000.0"),
            close_time=1700003599999,
            quote_volume=Decimal("45000000.00"),
            trade_count=5000,
            taker_buy_volume=Decimal("600.0"),
        )

        assert candle.taker_buy_volume == Decimal("600.0")

    @pytest.mark.xfail(reason="Taker fields not yet added to Candle")
    def test_candle_has_taker_buy_quote_volume(self):
        """Candle should include taker_buy_quote_volume."""
        candle = Candle(
            open_time=1700000000000,
            open=Decimal("45000.00"),
            high=Decimal("45500.00"),
            low=Decimal("44800.00"),
            close=Decimal("45200.00"),
            volume=Decimal("1000.0"),
            close_time=1700003599999,
            quote_volume=Decimal("45000000.00"),
            trade_count=5000,
            taker_buy_quote_volume=Decimal("27000000.00"),
        )

        assert candle.taker_buy_quote_volume == Decimal("27000000.00")

    @pytest.mark.xfail(reason="Taker fields not yet added to Candle")
    def test_taker_fields_are_optional(self):
        """Taker fields should be optional."""
        candle = Candle(
            open_time=1700000000000,
            open=Decimal("45000.00"),
            high=Decimal("45500.00"),
            low=Decimal("44800.00"),
            close=Decimal("45200.00"),
            volume=Decimal("1000.0"),
            close_time=1700003599999,
            quote_volume=Decimal("45000000.00"),
            trade_count=5000,
        )

        assert candle.taker_buy_volume is None
        assert candle.taker_buy_quote_volume is None


class TestExtendedFieldsInToolResponses:
    """Test that extended fields appear in tool responses."""

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="Extended fields not yet implemented")
    async def test_mark_price_tool_returns_extended_fields(self, mcp_server_with_mock):
        """get_mark_price tool should return extended fields when available."""
        mcp, mock_client = mcp_server_with_mock

        mock_client.get_mark_price.return_value = MarkPriceResponse(
            symbol="BTCUSDT",
            mark_price=Decimal("45000.00"),
            index_price=Decimal("44999.50"),
            last_funding_rate=Decimal("0.0001"),
            next_funding_time=1700003600000,
            estimated_settle_price=Decimal("45001.00"),
            interest_rate=Decimal("0.0003"),
            timestamp=1700000000000,
            exchange="binance",
        )

        tool_fn = mcp._tool_manager._tools["get_mark_price"].fn
        result = await tool_fn(symbol="BTCUSDT")

        assert "estimated_settle_price" in result
        assert "interest_rate" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="Extended fields not yet implemented")
    async def test_klines_tool_returns_taker_volumes(self, mcp_server_with_mock):
        """get_klines tool should return taker volume fields in candles."""
        mcp, mock_client = mcp_server_with_mock

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
                    taker_buy_volume=Decimal("600.0"),
                    taker_buy_quote_volume=Decimal("27000000.00"),
                )
            ],
            exchange="binance",
        )

        tool_fn = mcp._tool_manager._tools["get_klines"].fn
        result = await tool_fn(symbol="BTCUSDT", interval="1h")

        candle = result["candles"][0]
        assert "taker_buy_volume" in candle
        assert "taker_buy_quote_volume" in candle
