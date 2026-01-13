"""Binance USDT-M Futures API client."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import TYPE_CHECKING

import httpx
from pydantic import ValidationError as PydanticValidationError

from crypto_mcp.exchanges.base import BaseExchangeClient

if TYPE_CHECKING:
    from crypto_mcp.utils.rate_limiter import SlidingWindowRateLimiter
from crypto_mcp.models import (
    FundingRateResponse,
    KlinesResponse,
    LongShortRatioResponse,
    MarkPriceResponse,
    OpenInterestResponse,
    TickerResponse,
)

from .endpoints import (
    BASE_URL,
    FUNDING_RATE,
    KLINES,
    LONG_SHORT_RATIO,
    MARK_PRICE,
    OPEN_INTEREST,
    OPEN_INTEREST_HISTORY,
    TICKER_24H,
)
from .exceptions import BinanceAPIError, BinanceRateLimitError, raise_for_binance_error
from .models import (
    BinanceErrorResponse,
    BinanceFundingRate,
    BinanceLongShortRatio,
    BinanceMarkPrice,
    BinanceOpenInterest,
    BinanceOpenInterestHistory,
    BinanceTicker24h,
    parse_kline,
)


class BinanceClient(BaseExchangeClient):
    """Binance USDT-M Futures API client."""

    def __init__(
        self,
        http_client: httpx.AsyncClient | None = None,
        rate_limiter: SlidingWindowRateLimiter | None = None,
        max_retries: int = 3,
    ):
        self._client = http_client
        self._owns_client = http_client is None
        self._rate_limiter = rate_limiter
        self._max_retries = max_retries

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)
        return self._client

    async def close(self) -> None:
        """Close HTTP client if we own it."""
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _request(self, endpoint: str, params: dict | None = None) -> dict | list:
        """Make GET request to Binance API with rate limiting and retry."""
        # acquire rate limit slot before making request
        if self._rate_limiter:
            await self._rate_limiter.acquire()

        last_error: Exception | None = None

        for attempt in range(self._max_retries):
            try:
                return await self._do_request(endpoint, params)
            except BinanceRateLimitError as e:
                last_error = e
                if attempt < self._max_retries - 1:
                    # exponential backoff: 1s, 2s, 4s
                    wait_time = 2**attempt
                    await asyncio.sleep(wait_time)
                    # also re-acquire rate limit slot
                    if self._rate_limiter:
                        await self._rate_limiter.acquire()

        # all retries exhausted
        raise last_error  # type: ignore[misc]

    async def _do_request(self, endpoint: str, params: dict | None = None) -> dict | list:
        """Execute the actual HTTP request."""
        client = await self._get_client()
        response = await client.get(endpoint, params=params)

        # check HTTP status
        if response.status_code != 200:
            try:
                error = BinanceErrorResponse.model_validate(response.json())
                raise_for_binance_error(error.code, error.msg)
            except (PydanticValidationError, json.JSONDecodeError):
                raise BinanceAPIError(
                    f"HTTP {response.status_code}: {response.text}",
                    code=response.status_code,
                )

        data = response.json()

        # check for error response in JSON
        if isinstance(data, dict) and "code" in data and data["code"] < 0:
            raise_for_binance_error(data["code"], data.get("msg", "Unknown error"))

        return data

    def _datetime_to_ms(self, dt: datetime | None) -> int | None:
        """Convert datetime to milliseconds timestamp."""
        if dt is None:
            return None
        return int(dt.timestamp() * 1000)

    async def get_open_interest(self, symbol: str) -> OpenInterestResponse:
        """Get current open interest for a symbol."""
        data = await self._request(OPEN_INTEREST, {"symbol": symbol})
        return BinanceOpenInterest.model_validate(data).to_response()

    async def get_open_interest_history(
        self,
        symbol: str,
        period: str,
        limit: int = 30,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[OpenInterestResponse]:
        """Get historical open interest."""
        params: dict = {
            "symbol": symbol,
            "period": period,
            "limit": limit,
        }
        if start_time:
            params["startTime"] = self._datetime_to_ms(start_time)
        if end_time:
            params["endTime"] = self._datetime_to_ms(end_time)

        data = await self._request(OPEN_INTEREST_HISTORY, params)
        return [
            BinanceOpenInterestHistory.model_validate(item).to_response()
            for item in data
        ]

    async def get_funding_rate(
        self,
        symbol: str | None = None,
        limit: int = 100,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[FundingRateResponse]:
        """Get funding rate history."""
        params: dict = {"limit": limit}
        if symbol:
            params["symbol"] = symbol
        if start_time:
            params["startTime"] = self._datetime_to_ms(start_time)
        if end_time:
            params["endTime"] = self._datetime_to_ms(end_time)

        data = await self._request(FUNDING_RATE, params)
        return [
            BinanceFundingRate.model_validate(item).to_response() for item in data
        ]

    async def get_ticker_24h(
        self,
        symbol: str | None = None,
    ) -> TickerResponse | list[TickerResponse]:
        """Get 24h ticker statistics."""
        params = {"symbol": symbol} if symbol else None
        data = await self._request(TICKER_24H, params)

        if isinstance(data, list):
            return [BinanceTicker24h.model_validate(item).to_response() for item in data]
        return BinanceTicker24h.model_validate(data).to_response()

    async def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 500,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> KlinesResponse:
        """Get OHLCV candlestick data."""
        params: dict = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit,
        }
        if start_time:
            params["startTime"] = self._datetime_to_ms(start_time)
        if end_time:
            params["endTime"] = self._datetime_to_ms(end_time)

        data = await self._request(KLINES, params)
        assert isinstance(data, list)
        return parse_kline(data, symbol, interval)

    async def get_mark_price(
        self,
        symbol: str | None = None,
    ) -> MarkPriceResponse | list[MarkPriceResponse]:
        """Get current mark price and funding info."""
        params = {"symbol": symbol} if symbol else None
        data = await self._request(MARK_PRICE, params)

        if isinstance(data, list):
            return [BinanceMarkPrice.model_validate(item).to_response() for item in data]
        return BinanceMarkPrice.model_validate(data).to_response()

    async def get_long_short_ratio(
        self,
        symbol: str,
        period: str,
        limit: int = 30,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[LongShortRatioResponse]:
        """Get top trader long/short ratio."""
        params: dict = {
            "symbol": symbol,
            "period": period,
            "limit": limit,
        }
        if start_time:
            params["startTime"] = self._datetime_to_ms(start_time)
        if end_time:
            params["endTime"] = self._datetime_to_ms(end_time)

        data = await self._request(LONG_SHORT_RATIO, params)
        return [
            BinanceLongShortRatio.model_validate(item).to_response() for item in data
        ]
