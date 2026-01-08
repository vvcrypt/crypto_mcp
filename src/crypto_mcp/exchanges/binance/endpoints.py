"""Binance USDT-M Futures API endpoint constants."""

# base URL for USDT-margined futures
BASE_URL = "https://fapi.binance.com"

# current open interest for a symbol
OPEN_INTEREST = "/fapi/v1/openInterest"

# historical open interest (data API)
OPEN_INTEREST_HISTORY = "/futures/data/openInterestHist"

# funding rate history
FUNDING_RATE = "/fapi/v1/fundingRate"

# 24h ticker statistics
TICKER_24H = "/fapi/v1/ticker/24hr"

# OHLCV candlestick data
KLINES = "/fapi/v1/klines"

# mark price and funding info (premium index)
MARK_PRICE = "/fapi/v1/premiumIndex"

# top trader long/short position ratio
LONG_SHORT_RATIO = "/futures/data/topLongShortPositionRatio"


def build_url(endpoint: str) -> str:
    """Build full URL from endpoint path."""
    return f"{BASE_URL}{endpoint}"
