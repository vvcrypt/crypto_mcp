"""Tests for BybitClient with mocked HTTP responses."""

from datetime import datetime
from decimal import Decimal

import pytest
from pytest_httpx import HTTPXMock

from crypto_mcp.exchanges.bybit import BybitClient, BybitAPIError, BybitRateLimitError
from crypto_mcp.exchanges.bybit.endpoints import BASE_URL


@pytest.fixture
async def client():
    """Create a BybitClient for testing."""
    c = BybitClient()
    yield c
    await c.close()


class TestGetOpenInterest:
    """Tests for get_open_interest method (uses ticker endpoint)."""

    @pytest.mark.asyncio
    async def test_success(self, httpx_mock: HTTPXMock, client):
        httpx_mock.add_response(
            url=f"{BASE_URL}/v5/market/tickers?category=linear&symbol=BTCUSDT",
            json={
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
            },
        )
        result = await client.get_open_interest("BTCUSDT")
        assert result.symbol == "BTCUSDT"
        assert result.open_interest == Decimal("12345.678")
        assert result.exchange == "bybit"

    @pytest.mark.asyncio
    async def test_invalid_symbol(self, httpx_mock: HTTPXMock, client):
        httpx_mock.add_response(
            url=f"{BASE_URL}/v5/market/tickers?category=linear&symbol=INVALID",
            json={
                "retCode": 10001,
                "retMsg": "Invalid symbol",
                "result": {"category": "linear", "list": []},
                "time": 1700000000000,
            },
        )
        with pytest.raises(BybitAPIError) as exc_info:
            await client.get_open_interest("INVALID")
        assert exc_info.value.code == 10001


class TestGetOpenInterestHistory:
    """Tests for get_open_interest_history method."""

    @pytest.mark.asyncio
    async def test_success(self, httpx_mock: HTTPXMock, client):
        httpx_mock.add_response(
            url=f"{BASE_URL}/v5/market/open-interest?category=linear&symbol=BTCUSDT&intervalTime=5min&limit=30",
            json={
                "retCode": 0,
                "retMsg": "OK",
                "result": {
                    "symbol": "BTCUSDT",
                    "category": "linear",
                    "list": [
                        {"openInterest": "12345.0", "timestamp": "1700000300000"},
                        {"openInterest": "12346.0", "timestamp": "1700000000000"},
                    ],
                    "nextPageCursor": "",
                },
                "time": 1700000300000,
            },
        )
        result = await client.get_open_interest_history("BTCUSDT", "5m")
        assert len(result) == 2
        assert result[0].open_interest == Decimal("12345.0")

    @pytest.mark.asyncio
    async def test_with_time_params(self, httpx_mock: HTTPXMock, client):
        start = datetime(2024, 1, 1, 0, 0, 0)
        end = datetime(2024, 1, 2, 0, 0, 0)
        start_ms = int(start.timestamp() * 1000)
        end_ms = int(end.timestamp() * 1000)

        httpx_mock.add_response(
            url=f"{BASE_URL}/v5/market/open-interest?category=linear&symbol=BTCUSDT&intervalTime=1h&limit=10&startTime={start_ms}&endTime={end_ms}",
            json={
                "retCode": 0,
                "retMsg": "OK",
                "result": {
                    "symbol": "BTCUSDT",
                    "category": "linear",
                    "list": [],
                    "nextPageCursor": "",
                },
                "time": 1700000000000,
            },
        )
        result = await client.get_open_interest_history(
            "BTCUSDT", "1h", limit=10, start_time=start, end_time=end
        )
        assert result == []


class TestGetFundingRate:
    """Tests for get_funding_rate method."""

    @pytest.mark.asyncio
    async def test_success_with_symbol(self, httpx_mock: HTTPXMock, client):
        httpx_mock.add_response(
            url=f"{BASE_URL}/v5/market/funding/history?category=linear&symbol=BTCUSDT&limit=100",
            json={
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
                    ],
                },
                "time": 1700000000000,
            },
        )
        result = await client.get_funding_rate(symbol="BTCUSDT")
        assert len(result) == 1
        assert result[0].funding_rate == Decimal("0.00010000")

    @pytest.mark.asyncio
    async def test_without_symbol_returns_empty(self, client):
        # bybit requires symbol for funding rate, returns empty if none
        result = await client.get_funding_rate()
        assert result == []


class TestGetTicker24h:
    """Tests for get_ticker_24h method."""

    @pytest.mark.asyncio
    async def test_single_symbol(self, httpx_mock: HTTPXMock, client):
        httpx_mock.add_response(
            url=f"{BASE_URL}/v5/market/tickers?category=linear&symbol=BTCUSDT",
            json={
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
            },
        )
        result = await client.get_ticker_24h(symbol="BTCUSDT")
        assert result.symbol == "BTCUSDT"
        assert result.last_price == Decimal("45000.00")

    @pytest.mark.asyncio
    async def test_all_symbols(self, httpx_mock: HTTPXMock, client):
        httpx_mock.add_response(
            url=f"{BASE_URL}/v5/market/tickers?category=linear",
            json={
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
            },
        )
        result = await client.get_ticker_24h()
        assert isinstance(result, list)
        assert len(result) == 1


class TestGetKlines:
    """Tests for get_klines method."""

    @pytest.mark.asyncio
    async def test_success(self, httpx_mock: HTTPXMock, client):
        httpx_mock.add_response(
            url=f"{BASE_URL}/v5/market/kline?category=linear&symbol=BTCUSDT&interval=60&limit=500",
            json={
                "retCode": 0,
                "retMsg": "OK",
                "result": {
                    "symbol": "BTCUSDT",
                    "category": "linear",
                    "list": [
                        # bybit returns in reverse chronological order
                        ["1700003600000", "45200.00", "45500.00", "45100.00", "45300.00", "500.00", "22500000.00"],
                        ["1700000000000", "45000.00", "45200.00", "44800.00", "45200.00", "1234.567", "55555555.00"],
                    ],
                },
                "time": 1700003600000,
            },
        )
        result = await client.get_klines("BTCUSDT", "1h")
        assert result.symbol == "BTCUSDT"
        assert result.interval == "1h"
        assert len(result.candles) == 2
        # should be reversed to chronological order
        assert result.candles[0].open_time == 1700000000000
        assert result.candles[0].high == Decimal("45200.00")
        assert result.exchange == "bybit"


class TestGetMarkPrice:
    """Tests for get_mark_price method."""

    @pytest.mark.asyncio
    async def test_single_symbol(self, httpx_mock: HTTPXMock, client):
        httpx_mock.add_response(
            url=f"{BASE_URL}/v5/market/tickers?category=linear&symbol=BTCUSDT",
            json={
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
            },
        )
        result = await client.get_mark_price(symbol="BTCUSDT")
        assert result.symbol == "BTCUSDT"
        assert result.mark_price == Decimal("45000.10")
        assert result.index_price == Decimal("44999.50")

    @pytest.mark.asyncio
    async def test_all_symbols(self, httpx_mock: HTTPXMock, client):
        httpx_mock.add_response(
            url=f"{BASE_URL}/v5/market/tickers?category=linear",
            json={
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
            },
        )
        result = await client.get_mark_price()
        assert isinstance(result, list)


class TestGetLongShortRatio:
    """Tests for get_long_short_ratio method."""

    @pytest.mark.asyncio
    async def test_success(self, httpx_mock: HTTPXMock, client):
        httpx_mock.add_response(
            url=f"{BASE_URL}/v5/market/account-ratio?category=linear&symbol=BTCUSDT&period=5min&limit=30",
            json={
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
            },
        )
        result = await client.get_long_short_ratio("BTCUSDT", "5m")
        assert len(result) == 1
        assert result[0].long_account == Decimal("0.5556")
        assert result[0].short_account == Decimal("0.4444")


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_rate_limit_error(self, httpx_mock: HTTPXMock, client):
        httpx_mock.add_response(
            url=f"{BASE_URL}/v5/market/tickers?category=linear&symbol=BTCUSDT",
            json={"retCode": 10006, "retMsg": "Too many requests."},
        )
        with pytest.raises(BybitRateLimitError):
            await client.get_open_interest("BTCUSDT")

    @pytest.mark.asyncio
    async def test_api_error_in_response_body(self, httpx_mock: HTTPXMock, client):
        httpx_mock.add_response(
            url=f"{BASE_URL}/v5/market/tickers?category=linear&symbol=BTCUSDT",
            json={"retCode": 10001, "retMsg": "Invalid parameter."},
        )
        with pytest.raises(BybitAPIError) as exc_info:
            await client.get_open_interest("BTCUSDT")
        assert exc_info.value.code == 10001

    @pytest.mark.asyncio
    async def test_http_error_non_json(self, httpx_mock: HTTPXMock, client):
        httpx_mock.add_response(
            url=f"{BASE_URL}/v5/market/tickers?category=linear&symbol=BTCUSDT",
            status_code=500,
            text="Internal Server Error",
        )
        with pytest.raises(BybitAPIError) as exc_info:
            await client.get_open_interest("BTCUSDT")
        assert exc_info.value.code == 500
