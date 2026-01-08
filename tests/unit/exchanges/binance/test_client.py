"""Tests for BinanceClient with mocked HTTP responses."""

from datetime import datetime
from decimal import Decimal

import pytest
from pytest_httpx import HTTPXMock

from crypto_mcp.exchanges.binance import BinanceClient, BinanceAPIError, BinanceRateLimitError
from crypto_mcp.exchanges.binance.endpoints import BASE_URL


@pytest.fixture
async def client():
    """Create a BinanceClient for testing."""
    c = BinanceClient()
    yield c
    await c.close()


class TestGetOpenInterest:
    """Tests for get_open_interest method."""

    @pytest.mark.asyncio
    async def test_success(self, httpx_mock: HTTPXMock, client):
        httpx_mock.add_response(
            url=f"{BASE_URL}/fapi/v1/openInterest?symbol=BTCUSDT",
            json={
                "symbol": "BTCUSDT",
                "openInterest": "12345.678",
                "time": 1700000000000,
            },
        )
        result = await client.get_open_interest("BTCUSDT")
        assert result.symbol == "BTCUSDT"
        assert result.open_interest == Decimal("12345.678")
        assert result.exchange == "binance"

    @pytest.mark.asyncio
    async def test_invalid_symbol(self, httpx_mock: HTTPXMock, client):
        httpx_mock.add_response(
            url=f"{BASE_URL}/fapi/v1/openInterest?symbol=INVALID",
            status_code=400,
            json={"code": -1121, "msg": "Invalid symbol."},
        )
        with pytest.raises(BinanceAPIError) as exc_info:
            await client.get_open_interest("INVALID")
        assert exc_info.value.code == -1121


class TestGetOpenInterestHistory:
    """Tests for get_open_interest_history method."""

    @pytest.mark.asyncio
    async def test_success(self, httpx_mock: HTTPXMock, client):
        httpx_mock.add_response(
            url=f"{BASE_URL}/futures/data/openInterestHist?symbol=BTCUSDT&period=5m&limit=30",
            json=[
                {
                    "symbol": "BTCUSDT",
                    "sumOpenInterest": "12345.0",
                    "sumOpenInterestValue": "555555555.0",
                    "timestamp": 1700000000000,
                },
                {
                    "symbol": "BTCUSDT",
                    "sumOpenInterest": "12346.0",
                    "sumOpenInterestValue": "555600000.0",
                    "timestamp": 1700000300000,
                },
            ],
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
            url=f"{BASE_URL}/futures/data/openInterestHist?symbol=BTCUSDT&period=1h&limit=10&startTime={start_ms}&endTime={end_ms}",
            json=[],
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
            url=f"{BASE_URL}/fapi/v1/fundingRate?limit=100&symbol=BTCUSDT",
            json=[
                {
                    "symbol": "BTCUSDT",
                    "fundingRate": "0.00010000",
                    "fundingTime": 1700000000000,
                    "markPrice": "45000.00",
                },
            ],
        )
        result = await client.get_funding_rate(symbol="BTCUSDT")
        assert len(result) == 1
        assert result[0].funding_rate == Decimal("0.00010000")

    @pytest.mark.asyncio
    async def test_success_without_symbol(self, httpx_mock: HTTPXMock, client):
        httpx_mock.add_response(
            url=f"{BASE_URL}/fapi/v1/fundingRate?limit=100",
            json=[
                {"symbol": "BTCUSDT", "fundingRate": "0.0001", "fundingTime": 1700000000000},
                {"symbol": "ETHUSDT", "fundingRate": "0.0002", "fundingTime": 1700000000000},
            ],
        )
        result = await client.get_funding_rate()
        assert len(result) == 2


class TestGetTicker24h:
    """Tests for get_ticker_24h method."""

    @pytest.mark.asyncio
    async def test_single_symbol(self, httpx_mock: HTTPXMock, client):
        httpx_mock.add_response(
            url=f"{BASE_URL}/fapi/v1/ticker/24hr?symbol=BTCUSDT",
            json={
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
            },
        )
        result = await client.get_ticker_24h(symbol="BTCUSDT")
        assert result.symbol == "BTCUSDT"
        assert result.price_change == Decimal("1000.50")

    @pytest.mark.asyncio
    async def test_all_symbols(self, httpx_mock: HTTPXMock, client):
        httpx_mock.add_response(
            url=f"{BASE_URL}/fapi/v1/ticker/24hr",
            json=[
                {
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
                },
            ],
        )
        result = await client.get_ticker_24h()
        assert isinstance(result, list)
        assert len(result) == 1


class TestGetKlines:
    """Tests for get_klines method."""

    @pytest.mark.asyncio
    async def test_success(self, httpx_mock: HTTPXMock, client):
        httpx_mock.add_response(
            url=f"{BASE_URL}/fapi/v1/klines?symbol=BTCUSDT&interval=1h&limit=500",
            json=[
                [
                    1700000000000,
                    "45000.00",
                    "45500.00",
                    "44800.00",
                    "45200.00",
                    "1234.567",
                    1700003600000,
                    "55555555.00",
                    5000,
                    "600.123",
                    "27000000.00",
                ],
            ],
        )
        result = await client.get_klines("BTCUSDT", "1h")
        assert result.symbol == "BTCUSDT"
        assert result.interval == "1h"
        assert len(result.candles) == 1
        assert result.candles[0].high == Decimal("45500.00")


class TestGetMarkPrice:
    """Tests for get_mark_price method."""

    @pytest.mark.asyncio
    async def test_single_symbol(self, httpx_mock: HTTPXMock, client):
        httpx_mock.add_response(
            url=f"{BASE_URL}/fapi/v1/premiumIndex?symbol=BTCUSDT",
            json={
                "symbol": "BTCUSDT",
                "markPrice": "45000.00",
                "indexPrice": "44999.50",
                "lastFundingRate": "0.00010000",
                "nextFundingTime": 1700000000000,
            },
        )
        result = await client.get_mark_price(symbol="BTCUSDT")
        assert result.symbol == "BTCUSDT"
        assert result.mark_price == Decimal("45000.00")

    @pytest.mark.asyncio
    async def test_all_symbols(self, httpx_mock: HTTPXMock, client):
        httpx_mock.add_response(
            url=f"{BASE_URL}/fapi/v1/premiumIndex",
            json=[
                {
                    "symbol": "BTCUSDT",
                    "markPrice": "45000.00",
                    "indexPrice": "44999.50",
                    "lastFundingRate": "0.00010000",
                    "nextFundingTime": 1700000000000,
                },
            ],
        )
        result = await client.get_mark_price()
        assert isinstance(result, list)


class TestGetLongShortRatio:
    """Tests for get_long_short_ratio method."""

    @pytest.mark.asyncio
    async def test_success(self, httpx_mock: HTTPXMock, client):
        httpx_mock.add_response(
            url=f"{BASE_URL}/futures/data/topLongShortPositionRatio?symbol=BTCUSDT&period=5m&limit=30",
            json=[
                {
                    "symbol": "BTCUSDT",
                    "longShortRatio": "1.2500",
                    "longAccount": "0.5556",
                    "shortAccount": "0.4444",
                    "timestamp": 1700000000000,
                },
            ],
        )
        result = await client.get_long_short_ratio("BTCUSDT", "5m")
        assert len(result) == 1
        assert result[0].long_short_ratio == Decimal("1.2500")


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_rate_limit_error(self, httpx_mock: HTTPXMock, client):
        httpx_mock.add_response(
            url=f"{BASE_URL}/fapi/v1/openInterest?symbol=BTCUSDT",
            status_code=429,
            json={"code": -1003, "msg": "Too many requests."},
        )
        with pytest.raises(BinanceRateLimitError):
            await client.get_open_interest("BTCUSDT")

    @pytest.mark.asyncio
    async def test_api_error_in_response_body(self, httpx_mock: HTTPXMock, client):
        # some Binance errors return 200 with error in JSON body
        httpx_mock.add_response(
            url=f"{BASE_URL}/fapi/v1/openInterest?symbol=BTCUSDT",
            json={"code": -1000, "msg": "Unknown error."},
        )
        with pytest.raises(BinanceAPIError) as exc_info:
            await client.get_open_interest("BTCUSDT")
        assert exc_info.value.code == -1000

    @pytest.mark.asyncio
    async def test_http_error_non_json(self, httpx_mock: HTTPXMock, client):
        httpx_mock.add_response(
            url=f"{BASE_URL}/fapi/v1/openInterest?symbol=BTCUSDT",
            status_code=500,
            text="Internal Server Error",
        )
        with pytest.raises(BinanceAPIError) as exc_info:
            await client.get_open_interest("BTCUSDT")
        assert exc_info.value.code == 500
