"""Bybit V5 Futures API client."""

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
    FUNDING_RATE_HISTORY,
    KLINES,
    LONG_SHORT_RATIO,
    OPEN_INTEREST,
    TICKERS,
    map_interval,
    map_period,
)
from .exceptions import BybitAPIError, BybitRateLimitError, raise_for_bybit_error
from .models import (
    BybitErrorResponse,
    BybitFundingRateResponse,
    BybitKlineResponse,
    BybitLongShortRatioResponse,
    BybitOpenInterestResponse,
    BybitTickerResponse,
)


class BybitClient(BaseExchangeClient):
    """Bybit V5 Perpetual Futures API client."""

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

    async def _request(self, endpoint: str, params: dict | None = None) -> dict:
        """Make GET request to Bybit API with rate limiting and retry."""
        # acquire rate limit slot before making request
        if self._rate_limiter:
            await self._rate_limiter.acquire()

        last_error: Exception | None = None

        for attempt in range(self._max_retries):
            try:
                return await self._do_request(endpoint, params)
            except BybitRateLimitError as e:
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

    async def _do_request(self, endpoint: str, params: dict | None = None) -> dict:
        """Execute the actual HTTP request."""
        client = await self._get_client()
        response = await client.get(endpoint, params=params)

        # check HTTP status
        if response.status_code != 200:
            try:
                error = BybitErrorResponse.model_validate(response.json())
                raise_for_bybit_error(error.retCode, error.retMsg)
            except (PydanticValidationError, json.JSONDecodeError):
                raise BybitAPIError(
                    f"HTTP {response.status_code}: {response.text}",
                    code=response.status_code,
                )

        data = response.json()

        # check for error response in JSON (retCode != 0 means error)
        if isinstance(data, dict) and data.get("retCode", 0) != 0:
            raise_for_bybit_error(data["retCode"], data.get("retMsg", "Unknown error"))

        return data

    def _datetime_to_ms(self, dt: datetime | None) -> int | None:
        """Convert datetime to milliseconds timestamp."""
        if dt is None:
            return None
        return int(dt.timestamp() * 1000)

    async def get_open_interest(self, symbol: str) -> OpenInterestResponse:
        """Get current open interest for a symbol.

        Bybit doesn't have a dedicated current OI endpoint.
        We use the ticker endpoint which includes open interest.
        """
        data = await self._request(
            TICKERS,
            {"category": "linear", "symbol": symbol},
        )
        response = BybitTickerResponse.model_validate(data)
        oi_responses = response.to_open_interest_responses()
        if not oi_responses:
            raise BybitAPIError(f"No open interest data for {symbol}")
        return oi_responses[0]

    async def get_open_interest_history(
        self,
        symbol: str,
        period: str,
        limit: int = 30,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[OpenInterestResponse]:
        """Get historical open interest."""
        bybit_period = map_period(period)
        params: dict = {
            "category": "linear",
            "symbol": symbol,
            "intervalTime": bybit_period,
            "limit": min(limit, 200),  # bybit max is 200
        }
        if start_time:
            params["startTime"] = self._datetime_to_ms(start_time)
        if end_time:
            params["endTime"] = self._datetime_to_ms(end_time)

        data = await self._request(OPEN_INTEREST, params)
        response = BybitOpenInterestResponse.model_validate(data)
        return response.to_responses()

    async def get_funding_rate(
        self,
        symbol: str | None = None,
        limit: int = 100,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[FundingRateResponse]:
        """Get funding rate history.

        Note: Bybit requires symbol for funding rate history.
        If symbol is None, we return an empty list (unlike Binance which returns all).
        """
        if symbol is None:
            return []

        params: dict = {
            "category": "linear",
            "symbol": symbol,
            "limit": min(limit, 200),  # bybit max is 200
        }
        if start_time:
            params["startTime"] = self._datetime_to_ms(start_time)
        if end_time:
            params["endTime"] = self._datetime_to_ms(end_time)

        data = await self._request(FUNDING_RATE_HISTORY, params)
        response = BybitFundingRateResponse.model_validate(data)
        return response.to_responses()

    async def get_ticker_24h(
        self,
        symbol: str | None = None,
    ) -> TickerResponse | list[TickerResponse]:
        """Get 24h ticker statistics."""
        params: dict = {"category": "linear"}
        if symbol:
            params["symbol"] = symbol

        data = await self._request(TICKERS, params)
        response = BybitTickerResponse.model_validate(data)
        ticker_responses = response.to_ticker_responses()

        if symbol and ticker_responses:
            return ticker_responses[0]
        return ticker_responses

    async def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 500,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> KlinesResponse:
        """Get OHLCV candlestick data."""
        bybit_interval = map_interval(interval)
        params: dict = {
            "category": "linear",
            "symbol": symbol,
            "interval": bybit_interval,
            "limit": min(limit, 1000),  # bybit max is 1000
        }
        if start_time:
            params["start"] = self._datetime_to_ms(start_time)
        if end_time:
            params["end"] = self._datetime_to_ms(end_time)

        data = await self._request(KLINES, params)
        response = BybitKlineResponse.model_validate(data)
        return response.to_response(interval)

    async def get_mark_price(
        self,
        symbol: str | None = None,
    ) -> MarkPriceResponse | list[MarkPriceResponse]:
        """Get current mark price and funding info.

        Bybit includes mark price in the ticker endpoint.
        """
        params: dict = {"category": "linear"}
        if symbol:
            params["symbol"] = symbol

        data = await self._request(TICKERS, params)
        response = BybitTickerResponse.model_validate(data)
        mark_responses = response.to_mark_price_responses()

        if symbol and mark_responses:
            return mark_responses[0]
        return mark_responses

    async def get_long_short_ratio(
        self,
        symbol: str,
        period: str,
        limit: int = 30,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[LongShortRatioResponse]:
        """Get top trader long/short ratio."""
        bybit_period = map_period(period)
        params: dict = {
            "category": "linear",
            "symbol": symbol,
            "period": bybit_period,
            "limit": min(limit, 500),  # bybit max is 500
        }
        if start_time:
            params["startTime"] = self._datetime_to_ms(start_time)
        if end_time:
            params["endTime"] = self._datetime_to_ms(end_time)

        data = await self._request(LONG_SHORT_RATIO, params)
        response = BybitLongShortRatioResponse.model_validate(data)
        return response.to_responses()
