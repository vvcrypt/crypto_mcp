"""Abstract base class for exchange clients."""

from abc import ABC, abstractmethod
from datetime import datetime

from crypto_mcp.models import (
    FundingRateResponse,
    KlinesResponse,
    LongShortRatioResponse,
    MarkPriceResponse,
    OpenInterestResponse,
    TickerResponse,
)


class BaseExchangeClient(ABC):
    """Abstract interface for exchange API clients."""

    @abstractmethod
    async def get_open_interest(self, symbol: str) -> OpenInterestResponse:
        """Get current open interest for a symbol."""
        pass

    @abstractmethod
    async def get_open_interest_history(
        self,
        symbol: str,
        period: str,
        limit: int = 30,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[OpenInterestResponse]:
        """Get historical open interest."""
        pass

    @abstractmethod
    async def get_funding_rate(
        self,
        symbol: str | None = None,
        limit: int = 100,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[FundingRateResponse]:
        """Get funding rate history."""
        pass

    @abstractmethod
    async def get_ticker_24h(
        self,
        symbol: str | None = None,
    ) -> TickerResponse | list[TickerResponse]:
        """Get 24h ticker statistics."""
        pass

    @abstractmethod
    async def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 500,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> KlinesResponse:
        """Get OHLCV candlestick data."""
        pass

    @abstractmethod
    async def get_mark_price(
        self,
        symbol: str | None = None,
    ) -> MarkPriceResponse | list[MarkPriceResponse]:
        """Get current mark price and funding info."""
        pass

    @abstractmethod
    async def get_long_short_ratio(
        self,
        symbol: str,
        period: str,
        limit: int = 30,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[LongShortRatioResponse]:
        """Get top trader long/short ratio."""
        pass
