"""Pydantic models for parsing Binance API responses."""

from decimal import Decimal

from pydantic import BaseModel, Field

from crypto_mcp.models import (
    Candle,
    FundingRateResponse,
    KlinesResponse,
    LongShortRatioResponse,
    MarkPriceResponse,
    OpenInterestResponse,
    TickerResponse,
)

EXCHANGE = "binance"


class BinanceOpenInterest(BaseModel):
    """Binance open interest response."""

    symbol: str
    openInterest: Decimal
    time: int

    def to_response(self) -> OpenInterestResponse:
        return OpenInterestResponse(
            symbol=self.symbol,
            open_interest=self.openInterest,
            timestamp=self.time,
            exchange=EXCHANGE,
        )


class BinanceOpenInterestHistory(BaseModel):
    """Binance historical open interest response."""

    symbol: str
    sumOpenInterest: Decimal
    sumOpenInterestValue: Decimal
    timestamp: int

    def to_response(self) -> OpenInterestResponse:
        return OpenInterestResponse(
            symbol=self.symbol,
            open_interest=self.sumOpenInterest,
            timestamp=self.timestamp,
            exchange=EXCHANGE,
        )


class BinanceFundingRate(BaseModel):
    """Binance funding rate response."""

    symbol: str
    fundingRate: Decimal
    fundingTime: int
    markPrice: Decimal | None = None

    def to_response(self) -> FundingRateResponse:
        return FundingRateResponse(
            symbol=self.symbol,
            funding_rate=self.fundingRate,
            funding_time=self.fundingTime,
            mark_price=self.markPrice,
            exchange=EXCHANGE,
        )


class BinanceTicker24h(BaseModel):
    """Binance 24h ticker statistics response."""

    symbol: str
    priceChange: Decimal
    priceChangePercent: Decimal
    lastPrice: Decimal
    volume: Decimal
    quoteVolume: Decimal
    highPrice: Decimal
    lowPrice: Decimal
    openPrice: Decimal
    openTime: int
    closeTime: int
    count: int

    def to_response(self) -> TickerResponse:
        return TickerResponse(
            symbol=self.symbol,
            price_change=self.priceChange,
            price_change_percent=self.priceChangePercent,
            last_price=self.lastPrice,
            volume=self.volume,
            quote_volume=self.quoteVolume,
            high_price=self.highPrice,
            low_price=self.lowPrice,
            open_price=self.openPrice,
            open_time=self.openTime,
            close_time=self.closeTime,
            trade_count=self.count,
            exchange=EXCHANGE,
        )


class BinanceMarkPrice(BaseModel):
    """Binance mark price (premium index) response."""

    symbol: str
    markPrice: Decimal
    indexPrice: Decimal
    lastFundingRate: Decimal
    nextFundingTime: int

    # additional fields we don't use but may be in response
    estimatedSettlePrice: Decimal | None = None
    interestRate: Decimal | None = None
    time: int | None = None

    def to_response(self) -> MarkPriceResponse:
        return MarkPriceResponse(
            symbol=self.symbol,
            mark_price=self.markPrice,
            index_price=self.indexPrice,
            last_funding_rate=self.lastFundingRate,
            next_funding_time=self.nextFundingTime,
            exchange=EXCHANGE,
        )


class BinanceLongShortRatio(BaseModel):
    """Binance top trader long/short ratio response."""

    symbol: str
    longShortRatio: Decimal
    longAccount: Decimal
    shortAccount: Decimal
    timestamp: int

    def to_response(self) -> LongShortRatioResponse:
        return LongShortRatioResponse(
            symbol=self.symbol,
            long_short_ratio=self.longShortRatio,
            long_account=self.longAccount,
            short_account=self.shortAccount,
            timestamp=self.timestamp,
            exchange=EXCHANGE,
        )


def parse_kline(data: list, symbol: str, interval: str) -> KlinesResponse:
    """Parse Binance kline array response into KlinesResponse.

    Binance kline format:
    [
        open_time,      # 0
        open,           # 1
        high,           # 2
        low,            # 3
        close,          # 4
        volume,         # 5
        close_time,     # 6
        quote_volume,   # 7
        trade_count,    # 8
        taker_buy_base, # 9  (not used)
        taker_buy_quote # 10 (not used)
    ]
    """
    candles = []
    for k in data:
        candles.append(
            Candle(
                open_time=k[0],
                open=Decimal(k[1]),
                high=Decimal(k[2]),
                low=Decimal(k[3]),
                close=Decimal(k[4]),
                volume=Decimal(k[5]),
                close_time=k[6],
                quote_volume=Decimal(k[7]),
                trade_count=k[8],
            )
        )
    return KlinesResponse(
        symbol=symbol,
        interval=interval,
        candles=candles,
        exchange=EXCHANGE,
    )


class BinanceErrorResponse(BaseModel):
    """Binance API error response."""

    code: int
    msg: str
