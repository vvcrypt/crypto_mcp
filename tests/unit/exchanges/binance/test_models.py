"""Tests for Binance response model parsing."""

from decimal import Decimal

import pytest

from crypto_mcp.exchanges.binance.models import (
    BinanceFundingRate,
    BinanceLongShortRatio,
    BinanceMarkPrice,
    BinanceOpenInterest,
    BinanceOpenInterestHistory,
    BinanceTicker24h,
    parse_kline,
)


class TestBinanceOpenInterest:
    """Tests for BinanceOpenInterest model."""

    def test_parse_valid_response(self):
        data = {
            "symbol": "BTCUSDT",
            "openInterest": "12345.678",
            "time": 1700000000000,
        }
        model = BinanceOpenInterest.model_validate(data)
        assert model.symbol == "BTCUSDT"
        assert model.openInterest == Decimal("12345.678")
        assert model.time == 1700000000000

    def test_to_response(self):
        data = {
            "symbol": "ETHUSDT",
            "openInterest": "98765.432",
            "time": 1700001000000,
        }
        model = BinanceOpenInterest.model_validate(data)
        response = model.to_response()
        assert response.symbol == "ETHUSDT"
        assert response.open_interest == Decimal("98765.432")
        assert response.timestamp == 1700001000000
        assert response.exchange == "binance"


class TestBinanceOpenInterestHistory:
    """Tests for BinanceOpenInterestHistory model."""

    def test_parse_valid_response(self):
        data = {
            "symbol": "BTCUSDT",
            "sumOpenInterest": "12345.0",
            "sumOpenInterestValue": "555555555.0",
            "timestamp": 1700000000000,
        }
        model = BinanceOpenInterestHistory.model_validate(data)
        assert model.symbol == "BTCUSDT"
        assert model.sumOpenInterest == Decimal("12345.0")
        assert model.timestamp == 1700000000000

    def test_to_response(self):
        data = {
            "symbol": "BTCUSDT",
            "sumOpenInterest": "12345.0",
            "sumOpenInterestValue": "555555555.0",
            "timestamp": 1700000000000,
        }
        response = BinanceOpenInterestHistory.model_validate(data).to_response()
        assert response.open_interest == Decimal("12345.0")
        assert response.exchange == "binance"


class TestBinanceFundingRate:
    """Tests for BinanceFundingRate model."""

    def test_parse_with_mark_price(self):
        data = {
            "symbol": "BTCUSDT",
            "fundingRate": "0.00010000",
            "fundingTime": 1700000000000,
            "markPrice": "45000.00",
        }
        model = BinanceFundingRate.model_validate(data)
        assert model.fundingRate == Decimal("0.00010000")
        assert model.markPrice == Decimal("45000.00")

    def test_parse_without_mark_price(self):
        data = {
            "symbol": "BTCUSDT",
            "fundingRate": "0.00010000",
            "fundingTime": 1700000000000,
        }
        model = BinanceFundingRate.model_validate(data)
        assert model.markPrice is None

    def test_to_response(self):
        data = {
            "symbol": "BTCUSDT",
            "fundingRate": "-0.00005000",
            "fundingTime": 1700000000000,
            "markPrice": "42000.00",
        }
        response = BinanceFundingRate.model_validate(data).to_response()
        assert response.funding_rate == Decimal("-0.00005000")
        assert response.mark_price == Decimal("42000.00")
        assert response.exchange == "binance"


class TestBinanceTicker24h:
    """Tests for BinanceTicker24h model."""

    def test_parse_valid_response(self):
        data = {
            "symbol": "BTCUSDT",
            "priceChange": "1000.50",
            "priceChangePercent": "2.35",
            "lastPrice": "43500.00",
            "volume": "50000.00",
            "quoteVolume": "2175000000.00",
            "highPrice": "44000.00",
            "lowPrice": "42000.00",
            "openPrice": "42500.00",
            "openTime": 1700000000000,
            "closeTime": 1700086400000,
            "count": 1500000,
        }
        model = BinanceTicker24h.model_validate(data)
        assert model.priceChangePercent == Decimal("2.35")
        assert model.count == 1500000

    def test_to_response(self):
        data = {
            "symbol": "BTCUSDT",
            "priceChange": "1000.50",
            "priceChangePercent": "2.35",
            "lastPrice": "43500.00",
            "volume": "50000.00",
            "quoteVolume": "2175000000.00",
            "highPrice": "44000.00",
            "lowPrice": "42000.00",
            "openPrice": "42500.00",
            "openTime": 1700000000000,
            "closeTime": 1700086400000,
            "count": 1500000,
        }
        response = BinanceTicker24h.model_validate(data).to_response()
        assert response.price_change_percent == Decimal("2.35")
        assert response.trade_count == 1500000
        assert response.exchange == "binance"


class TestBinanceMarkPrice:
    """Tests for BinanceMarkPrice model."""

    def test_parse_valid_response(self):
        data = {
            "symbol": "BTCUSDT",
            "markPrice": "45000.00",
            "indexPrice": "44999.50",
            "lastFundingRate": "0.00010000",
            "nextFundingTime": 1700000000000,
        }
        model = BinanceMarkPrice.model_validate(data)
        assert model.markPrice == Decimal("45000.00")

    def test_parse_with_optional_fields(self):
        data = {
            "symbol": "BTCUSDT",
            "markPrice": "45000.00",
            "indexPrice": "44999.50",
            "lastFundingRate": "0.00010000",
            "nextFundingTime": 1700000000000,
            "estimatedSettlePrice": "45001.00",
            "interestRate": "0.0001",
            "time": 1699999999999,
        }
        model = BinanceMarkPrice.model_validate(data)
        assert model.estimatedSettlePrice == Decimal("45001.00")

    def test_to_response(self):
        data = {
            "symbol": "ETHUSDT",
            "markPrice": "2500.00",
            "indexPrice": "2499.50",
            "lastFundingRate": "0.00005000",
            "nextFundingTime": 1700000000000,
        }
        response = BinanceMarkPrice.model_validate(data).to_response()
        assert response.mark_price == Decimal("2500.00")
        assert response.index_price == Decimal("2499.50")
        assert response.exchange == "binance"


class TestBinanceLongShortRatio:
    """Tests for BinanceLongShortRatio model."""

    def test_parse_valid_response(self):
        data = {
            "symbol": "BTCUSDT",
            "longShortRatio": "1.2500",
            "longAccount": "0.5556",
            "shortAccount": "0.4444",
            "timestamp": 1700000000000,
        }
        model = BinanceLongShortRatio.model_validate(data)
        assert model.longShortRatio == Decimal("1.2500")
        assert model.longAccount == Decimal("0.5556")

    def test_to_response(self):
        data = {
            "symbol": "BTCUSDT",
            "longShortRatio": "1.2500",
            "longAccount": "0.5556",
            "shortAccount": "0.4444",
            "timestamp": 1700000000000,
        }
        response = BinanceLongShortRatio.model_validate(data).to_response()
        assert response.long_short_ratio == Decimal("1.2500")
        assert response.long_account == Decimal("0.5556")
        assert response.short_account == Decimal("0.4444")
        assert response.exchange == "binance"


class TestParseKline:
    """Tests for parse_kline function."""

    def test_parse_single_kline(self):
        data = [
            [
                1700000000000,  # open time
                "45000.00",  # open
                "45500.00",  # high
                "44800.00",  # low
                "45200.00",  # close
                "1234.567",  # volume
                1700003600000,  # close time
                "55555555.00",  # quote volume
                5000,  # trade count
                "600.123",  # taker buy base (unused)
                "27000000.00",  # taker buy quote (unused)
            ]
        ]
        result = parse_kline(data, "BTCUSDT", "1h")
        assert result.symbol == "BTCUSDT"
        assert result.interval == "1h"
        assert result.exchange == "binance"
        assert len(result.candles) == 1

        candle = result.candles[0]
        assert candle.open == Decimal("45000.00")
        assert candle.high == Decimal("45500.00")
        assert candle.low == Decimal("44800.00")
        assert candle.close == Decimal("45200.00")
        assert candle.volume == Decimal("1234.567")
        assert candle.trade_count == 5000

    def test_parse_multiple_klines(self):
        data = [
            [1700000000000, "45000", "45100", "44900", "45050", "100", 1700003600000, "4505000", 1000, "50", "2252500"],
            [1700003600000, "45050", "45200", "45000", "45150", "150", 1700007200000, "6772500", 1500, "75", "3386250"],
        ]
        result = parse_kline(data, "BTCUSDT", "1h")
        assert len(result.candles) == 2
        assert result.candles[0].open == Decimal("45000")
        assert result.candles[1].open == Decimal("45050")

    def test_parse_empty_klines(self):
        result = parse_kline([], "BTCUSDT", "1h")
        assert len(result.candles) == 0
        assert result.symbol == "BTCUSDT"
