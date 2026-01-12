"""Tests for Bybit response model parsing."""

from decimal import Decimal

import pytest

from crypto_mcp.exchanges.bybit.models import (
    BybitFundingRateResponse,
    BybitKlineResponse,
    BybitLongShortRatioResponse,
    BybitOpenInterestResponse,
    BybitTickerResponse,
)


class TestBybitOpenInterestResponse:
    """Tests for open interest response parsing."""

    def test_parse_and_convert(self):
        data = {
            "retCode": 0,
            "retMsg": "OK",
            "result": {
                "symbol": "BTCUSDT",
                "category": "linear",
                "list": [
                    {"openInterest": "12345.678", "timestamp": "1700000000000"},
                    {"openInterest": "12346.000", "timestamp": "1700000300000"},
                ],
                "nextPageCursor": "",
            },
            "time": 1700000300000,
        }
        response = BybitOpenInterestResponse.model_validate(data)
        results = response.to_responses()

        assert len(results) == 2
        assert results[0].symbol == "BTCUSDT"
        assert results[0].open_interest == Decimal("12345.678")
        assert results[0].timestamp == 1700000000000
        assert results[0].exchange == "bybit"


class TestBybitTickerResponse:
    """Tests for ticker response parsing."""

    def test_to_ticker_responses(self):
        data = {
            "retCode": 0,
            "retMsg": "OK",
            "result": {
                "category": "linear",
                "list": [
                    {
                        "symbol": "BTCUSDT",
                        "lastPrice": "45000.00",
                        "indexPrice": "44999.50",
                        "markPrice": "45000.10",
                        "prevPrice24h": "44000.00",
                        "price24hPcnt": "0.0227",
                        "highPrice24h": "45500.00",
                        "lowPrice24h": "43500.00",
                        "volume24h": "50000.00",
                        "turnover24h": "2250000000.00",
                        "openInterest": "12345.678",
                        "openInterestValue": "555555555.00",
                        "fundingRate": "0.0001",
                        "nextFundingTime": "1700000000000",
                    }
                ],
            },
            "time": 1700000000000,
        }
        response = BybitTickerResponse.model_validate(data)
        results = response.to_ticker_responses()

        assert len(results) == 1
        assert results[0].symbol == "BTCUSDT"
        assert results[0].last_price == Decimal("45000.00")
        assert results[0].high_price == Decimal("45500.00")
        assert results[0].exchange == "bybit"

    def test_to_mark_price_responses(self):
        data = {
            "retCode": 0,
            "retMsg": "OK",
            "result": {
                "category": "linear",
                "list": [
                    {
                        "symbol": "BTCUSDT",
                        "lastPrice": "45000.00",
                        "indexPrice": "44999.50",
                        "markPrice": "45000.10",
                        "prevPrice24h": "44000.00",
                        "price24hPcnt": "0.0227",
                        "highPrice24h": "45500.00",
                        "lowPrice24h": "43500.00",
                        "volume24h": "50000.00",
                        "turnover24h": "2250000000.00",
                        "openInterest": "12345.678",
                        "openInterestValue": "555555555.00",
                        "fundingRate": "0.0001",
                        "nextFundingTime": "1700000000000",
                    }
                ],
            },
            "time": 1700000000000,
        }
        response = BybitTickerResponse.model_validate(data)
        results = response.to_mark_price_responses()

        assert len(results) == 1
        assert results[0].symbol == "BTCUSDT"
        assert results[0].mark_price == Decimal("45000.10")
        assert results[0].index_price == Decimal("44999.50")
        assert results[0].last_funding_rate == Decimal("0.0001")

    def test_to_open_interest_responses(self):
        data = {
            "retCode": 0,
            "retMsg": "OK",
            "result": {
                "category": "linear",
                "list": [
                    {
                        "symbol": "BTCUSDT",
                        "lastPrice": "45000.00",
                        "indexPrice": "44999.50",
                        "markPrice": "45000.10",
                        "prevPrice24h": "44000.00",
                        "price24hPcnt": "0.0227",
                        "highPrice24h": "45500.00",
                        "lowPrice24h": "43500.00",
                        "volume24h": "50000.00",
                        "turnover24h": "2250000000.00",
                        "openInterest": "12345.678",
                        "openInterestValue": "555555555.00",
                        "fundingRate": "0.0001",
                        "nextFundingTime": "1700000000000",
                    }
                ],
            },
            "time": 1700000000000,
        }
        response = BybitTickerResponse.model_validate(data)
        results = response.to_open_interest_responses()

        assert len(results) == 1
        assert results[0].symbol == "BTCUSDT"
        assert results[0].open_interest == Decimal("12345.678")


class TestBybitFundingRateResponse:
    """Tests for funding rate response parsing."""

    def test_parse_and_convert(self):
        data = {
            "retCode": 0,
            "retMsg": "OK",
            "result": {
                "category": "linear",
                "list": [
                    {
                        "symbol": "BTCUSDT",
                        "fundingRate": "0.00010000",
                        "fundingRateTimestamp": "1700000000000",
                    },
                    {
                        "symbol": "BTCUSDT",
                        "fundingRate": "0.00015000",
                        "fundingRateTimestamp": "1700028800000",
                    },
                ],
            },
            "time": 1700028800000,
        }
        response = BybitFundingRateResponse.model_validate(data)
        results = response.to_responses()

        assert len(results) == 2
        assert results[0].symbol == "BTCUSDT"
        assert results[0].funding_rate == Decimal("0.00010000")
        assert results[0].funding_time == 1700000000000
        assert results[0].mark_price is None  # bybit doesn't include this
        assert results[0].exchange == "bybit"


class TestBybitKlineResponse:
    """Tests for kline response parsing."""

    def test_parse_and_convert(self):
        data = {
            "retCode": 0,
            "retMsg": "OK",
            "result": {
                "symbol": "BTCUSDT",
                "category": "linear",
                "list": [
                    # bybit returns reverse chronological
                    ["1700003600000", "45200.00", "45500.00", "45100.00", "45300.00", "500.00", "22500000.00"],
                    ["1700000000000", "45000.00", "45200.00", "44800.00", "45200.00", "1234.567", "55555555.00"],
                ],
            },
            "time": 1700003600000,
        }
        response = BybitKlineResponse.model_validate(data)
        result = response.to_response("1h")

        assert result.symbol == "BTCUSDT"
        assert result.interval == "1h"
        assert len(result.candles) == 2
        # should be reversed to chronological order
        assert result.candles[0].open_time == 1700000000000
        assert result.candles[0].open == Decimal("45000.00")
        assert result.candles[0].high == Decimal("45200.00")
        assert result.candles[0].low == Decimal("44800.00")
        assert result.candles[0].close == Decimal("45200.00")
        assert result.candles[0].volume == Decimal("1234.567")
        assert result.candles[0].quote_volume == Decimal("55555555.00")
        assert result.candles[0].trade_count == 0  # bybit doesn't provide this
        assert result.exchange == "bybit"


class TestBybitLongShortRatioResponse:
    """Tests for long/short ratio response parsing."""

    def test_parse_and_convert(self):
        data = {
            "retCode": 0,
            "retMsg": "OK",
            "result": {
                "list": [
                    {
                        "symbol": "BTCUSDT",
                        "buyRatio": "0.5556",
                        "sellRatio": "0.4444",
                        "timestamp": "1700000000000",
                    },
                ],
            },
            "time": 1700000000000,
        }
        response = BybitLongShortRatioResponse.model_validate(data)
        results = response.to_responses()

        assert len(results) == 1
        assert results[0].symbol == "BTCUSDT"
        assert results[0].long_account == Decimal("0.5556")
        assert results[0].short_account == Decimal("0.4444")
        # ratio = buy/sell = 0.5556/0.4444 = 1.25
        assert float(results[0].long_short_ratio) == pytest.approx(1.25, rel=0.01)
        assert results[0].exchange == "bybit"

    def test_zero_sell_ratio(self):
        """Test handling of zero sell ratio to avoid division by zero."""
        data = {
            "retCode": 0,
            "retMsg": "OK",
            "result": {
                "list": [
                    {
                        "symbol": "BTCUSDT",
                        "buyRatio": "1.0",
                        "sellRatio": "0",
                        "timestamp": "1700000000000",
                    },
                ],
            },
            "time": 1700000000000,
        }
        response = BybitLongShortRatioResponse.model_validate(data)
        results = response.to_responses()

        assert len(results) == 1
        assert results[0].long_short_ratio == Decimal("999")
