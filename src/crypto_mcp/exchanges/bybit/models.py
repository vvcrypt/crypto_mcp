"""Pydantic models for parsing Bybit V5 API responses."""

from decimal import Decimal

from pydantic import BaseModel

from crypto_mcp.models import (
    Candle,
    FundingRateResponse,
    KlinesResponse,
    LongShortRatioResponse,
    MarkPriceResponse,
    OpenInterestResponse,
    TickerResponse,
)

EXCHANGE = "bybit"


class BybitBaseResponse(BaseModel):
    """Base response wrapper for all Bybit V5 API responses."""

    retCode: int
    retMsg: str
    time: int | None = None


# open interest models


class BybitOpenInterestItem(BaseModel):
    """Single open interest data point."""

    openInterest: str
    timestamp: str


class BybitOpenInterestResult(BaseModel):
    """Open interest result wrapper."""

    symbol: str
    category: str
    list: list[BybitOpenInterestItem]
    nextPageCursor: str = ""


class BybitOpenInterestResponse(BybitBaseResponse):
    """Open interest API response."""

    result: BybitOpenInterestResult

    def to_responses(self) -> list[OpenInterestResponse]:
        """Convert to unified response format."""
        responses = []
        for item in self.result.list:
            responses.append(
                OpenInterestResponse(
                    symbol=self.result.symbol,
                    open_interest=Decimal(item.openInterest),
                    timestamp=int(item.timestamp),
                    exchange=EXCHANGE,
                )
            )
        return responses


# ticker models (includes mark price, funding rate, open interest)


class BybitLinearTickerItem(BaseModel):
    """Single linear ticker data."""

    symbol: str
    lastPrice: str
    indexPrice: str
    markPrice: str
    prevPrice24h: str
    price24hPcnt: str
    highPrice24h: str
    lowPrice24h: str
    volume24h: str
    turnover24h: str
    openInterest: str
    openInterestValue: str
    fundingRate: str
    nextFundingTime: str
    # optional fields
    bid1Price: str = "0"
    bid1Size: str = "0"
    ask1Price: str = "0"
    ask1Size: str = "0"


class BybitTickerResult(BaseModel):
    """Ticker result wrapper."""

    category: str
    list: list[BybitLinearTickerItem]


class BybitTickerResponse(BybitBaseResponse):
    """Ticker API response."""

    result: BybitTickerResult

    def to_ticker_responses(self) -> list[TickerResponse]:
        """Convert to unified ticker response format."""
        responses = []
        for item in self.result.list:
            # calculate open/close time (24h window ending now)
            # bybit doesn't provide these directly, so we approximate
            close_time = self.time or 0
            open_time = close_time - 86400000 if close_time else 0

            responses.append(
                TickerResponse(
                    symbol=item.symbol,
                    price_change=Decimal(item.lastPrice) - Decimal(item.prevPrice24h),
                    price_change_percent=Decimal(item.price24hPcnt) * 100,
                    last_price=Decimal(item.lastPrice),
                    volume=Decimal(item.volume24h),
                    quote_volume=Decimal(item.turnover24h),
                    high_price=Decimal(item.highPrice24h),
                    low_price=Decimal(item.lowPrice24h),
                    open_price=Decimal(item.prevPrice24h),
                    open_time=open_time,
                    close_time=close_time,
                    trade_count=0,  # bybit doesn't provide this
                    exchange=EXCHANGE,
                )
            )
        return responses

    def to_mark_price_responses(self) -> list[MarkPriceResponse]:
        """Convert to unified mark price response format."""
        responses = []
        for item in self.result.list:
            responses.append(
                MarkPriceResponse(
                    symbol=item.symbol,
                    mark_price=Decimal(item.markPrice),
                    index_price=Decimal(item.indexPrice),
                    last_funding_rate=Decimal(item.fundingRate),
                    next_funding_time=int(item.nextFundingTime),
                    exchange=EXCHANGE,
                )
            )
        return responses

    def to_open_interest_responses(self) -> list[OpenInterestResponse]:
        """Convert to unified open interest response format."""
        responses = []
        for item in self.result.list:
            responses.append(
                OpenInterestResponse(
                    symbol=item.symbol,
                    open_interest=Decimal(item.openInterest),
                    timestamp=self.time or 0,
                    exchange=EXCHANGE,
                )
            )
        return responses


# funding rate history models


class BybitFundingRateItem(BaseModel):
    """Single funding rate data point."""

    symbol: str
    fundingRate: str
    fundingRateTimestamp: str


class BybitFundingRateResult(BaseModel):
    """Funding rate result wrapper."""

    category: str
    list: list[BybitFundingRateItem]


class BybitFundingRateResponse(BybitBaseResponse):
    """Funding rate history API response."""

    result: BybitFundingRateResult

    def to_responses(self) -> list[FundingRateResponse]:
        """Convert to unified response format."""
        responses = []
        for item in self.result.list:
            responses.append(
                FundingRateResponse(
                    symbol=item.symbol,
                    funding_rate=Decimal(item.fundingRate),
                    funding_time=int(item.fundingRateTimestamp),
                    mark_price=None,  # bybit doesn't include mark price in funding history
                    exchange=EXCHANGE,
                )
            )
        return responses


# long/short ratio models


class BybitLongShortRatioItem(BaseModel):
    """Single long/short ratio data point."""

    symbol: str
    buyRatio: str
    sellRatio: str
    timestamp: str


class BybitLongShortRatioResult(BaseModel):
    """Long/short ratio result wrapper."""

    list: list[BybitLongShortRatioItem]


class BybitLongShortRatioResponse(BybitBaseResponse):
    """Long/short ratio API response."""

    result: BybitLongShortRatioResult

    def to_responses(self) -> list[LongShortRatioResponse]:
        """Convert to unified response format."""
        responses = []
        for item in self.result.list:
            buy_ratio = Decimal(item.buyRatio)
            sell_ratio = Decimal(item.sellRatio)
            # calculate long/short ratio from buy/sell ratios
            # if sell_ratio is 0, use a large number to avoid division by zero
            if sell_ratio == 0:
                long_short_ratio = Decimal("999")
            else:
                long_short_ratio = buy_ratio / sell_ratio

            responses.append(
                LongShortRatioResponse(
                    symbol=item.symbol,
                    long_short_ratio=long_short_ratio,
                    long_account=buy_ratio,
                    short_account=sell_ratio,
                    timestamp=int(item.timestamp),
                    exchange=EXCHANGE,
                )
            )
        return responses


# klines models


class BybitKlineResult(BaseModel):
    """Kline result wrapper."""

    symbol: str
    category: str
    list: list[list[str]]


class BybitKlineResponse(BybitBaseResponse):
    """Kline API response."""

    result: BybitKlineResult

    def to_response(self, interval: str) -> KlinesResponse:
        """Convert to unified klines response format.

        Bybit kline format (in reverse chronological order):
        [
            start_time,   # 0
            open,         # 1
            high,         # 2
            low,          # 3
            close,        # 4
            volume,       # 5
            turnover      # 6 (quote volume)
        ]

        Note: Bybit doesn't provide trade_count or close_time.
        """
        candles = []
        # bybit returns in reverse chronological order, so reverse
        for k in reversed(self.result.list):
            open_time = int(k[0])
            candles.append(
                Candle(
                    open_time=open_time,
                    open=Decimal(k[1]),
                    high=Decimal(k[2]),
                    low=Decimal(k[3]),
                    close=Decimal(k[4]),
                    volume=Decimal(k[5]),
                    close_time=open_time,  # bybit doesn't provide close_time
                    quote_volume=Decimal(k[6]),
                    trade_count=0,  # bybit doesn't provide this
                )
            )
        return KlinesResponse(
            symbol=self.result.symbol,
            interval=interval,
            candles=candles,
            exchange=EXCHANGE,
        )


class BybitErrorResponse(BaseModel):
    """Bybit API error response."""

    retCode: int
    retMsg: str
