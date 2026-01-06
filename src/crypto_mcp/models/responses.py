"""Unified response models returned by MCP tools."""

from decimal import Decimal

from pydantic import BaseModel


class OpenInterestResponse(BaseModel):
    """Open interest for a futures symbol."""

    symbol: str
    open_interest: Decimal
    timestamp: int
    exchange: str


class FundingRateResponse(BaseModel):
    """Funding rate for a futures symbol."""

    symbol: str
    funding_rate: Decimal
    funding_time: int
    mark_price: Decimal | None = None
    exchange: str


class TickerResponse(BaseModel):
    """24h ticker statistics."""

    symbol: str
    price_change: Decimal
    price_change_percent: Decimal
    last_price: Decimal
    volume: Decimal
    quote_volume: Decimal
    high_price: Decimal
    low_price: Decimal
    open_price: Decimal
    open_time: int
    close_time: int
    trade_count: int
    exchange: str


class Candle(BaseModel):
    """Single OHLCV candle."""

    open_time: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    close_time: int
    quote_volume: Decimal
    trade_count: int


class KlinesResponse(BaseModel):
    """Kline/candlestick data response."""

    symbol: str
    interval: str
    candles: list[Candle]
    exchange: str


class MarkPriceResponse(BaseModel):
    """Mark price and funding info."""

    symbol: str
    mark_price: Decimal
    index_price: Decimal
    last_funding_rate: Decimal
    next_funding_time: int
    exchange: str


class LongShortRatioResponse(BaseModel):
    """Top trader long/short ratio."""

    symbol: str
    long_short_ratio: Decimal
    long_account: Decimal
    short_account: Decimal
    timestamp: int
    exchange: str
