"""Bybit V5 API endpoints and mappings."""

BASE_URL = "https://api.bybit.com"

# market data endpoints (public, no auth required)
KLINES = "/v5/market/kline"
TICKERS = "/v5/market/tickers"
OPEN_INTEREST = "/v5/market/open-interest"
FUNDING_RATE_HISTORY = "/v5/market/funding/history"
LONG_SHORT_RATIO = "/v5/market/account-ratio"

# interval mapping: binance format -> bybit format
INTERVAL_MAP = {
    "1m": "1",
    "3m": "3",
    "5m": "5",
    "15m": "15",
    "30m": "30",
    "1h": "60",
    "2h": "120",
    "4h": "240",
    "6h": "360",
    "8h": "480",
    "12h": "720",
    "1d": "D",
    "3d": "D",  # bybit doesn't have 3d, use daily
    "1w": "W",
    "1M": "M",
}

# period mapping for OI history, long/short ratio
PERIOD_MAP = {
    "5m": "5min",
    "15m": "15min",
    "30m": "30min",
    "1h": "1h",
    "2h": "1h",  # bybit doesn't have 2h, use 1h
    "4h": "4h",
    "6h": "4h",  # bybit doesn't have 6h, use 4h
    "12h": "4h",  # bybit doesn't have 12h, use 4h
    "1d": "1d",
}


def map_interval(binance_interval: str) -> str:
    """Convert Binance interval format to Bybit format."""
    bybit_interval = INTERVAL_MAP.get(binance_interval)
    if bybit_interval is None:
        raise ValueError(f"Unsupported interval: {binance_interval}")
    return bybit_interval


def map_period(binance_period: str) -> str:
    """Convert Binance period format to Bybit format."""
    bybit_period = PERIOD_MAP.get(binance_period)
    if bybit_period is None:
        raise ValueError(f"Unsupported period: {binance_period}")
    return bybit_period


def build_url(endpoint: str) -> str:
    """Build full URL from endpoint path."""
    return f"{BASE_URL}{endpoint}"
