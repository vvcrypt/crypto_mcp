"""Shared fixtures for performance tests."""

import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from mcp.server.fastmcp import FastMCP

from crypto_mcp.config import Settings
from crypto_mcp.exchanges.binance import BinanceClient
from crypto_mcp.tools import register_all_tools
from crypto_mcp.models import (
    OpenInterestResponse,
    FundingRateResponse,
    MarkPriceResponse,
    TickerResponse,
    LongShortRatioResponse,
    KlinesResponse,
    Candle,
)


@pytest.fixture
def mock_binance_client():
    """Create a mock BinanceClient with reasonable test data."""
    client = AsyncMock(spec=BinanceClient)

    # setup default return values for common methods
    client.get_open_interest.return_value = OpenInterestResponse(
        symbol="BTCUSDT",
        open_interest=Decimal("100000.0"),
        timestamp=1700000000000,
        exchange="binance",
    )

    client.get_funding_rate.return_value = [
        FundingRateResponse(
            symbol="BTCUSDT",
            funding_rate=Decimal("0.0001"),
            funding_time=1700000000000,
            mark_price=Decimal("45000.00"),
            exchange="binance",
        )
    ]

    client.get_long_short_ratio.return_value = [
        LongShortRatioResponse(
            symbol="BTCUSDT",
            long_short_ratio=Decimal("1.5"),
            long_account=Decimal("60.0"),
            short_account=Decimal("40.0"),
            timestamp=1700000000000,
            exchange="binance",
        )
    ]

    client.get_mark_price.return_value = MarkPriceResponse(
        symbol="BTCUSDT",
        mark_price=Decimal("45000.00"),
        index_price=Decimal("44999.50"),
        last_funding_rate=Decimal("0.0001"),
        next_funding_time=1700003600000,
        exchange="binance",
    )

    client.get_ticker_24h.return_value = TickerResponse(
        symbol="BTCUSDT",
        price_change=Decimal("500.00"),
        price_change_percent=Decimal("1.12"),
        last_price=Decimal("45000.00"),
        volume=Decimal("50000.0"),
        quote_volume=Decimal("2250000000.00"),
        high_price=Decimal("45500.00"),
        low_price=Decimal("44000.00"),
        open_price=Decimal("44500.00"),
        open_time=1699913600000,
        close_time=1700000000000,
        trade_count=1000000,
        exchange="binance",
    )

    return client


@pytest.fixture
def mcp_server_with_mock(mock_binance_client):
    """Create an MCP server with mock client for testing tools."""
    mcp = FastMCP("test-performance")
    mock_clients = {"binance": mock_binance_client, "bybit": mock_binance_client}
    register_all_tools(mcp, mock_clients)
    return mcp, mock_binance_client


@pytest.fixture
def sample_symbols():
    """Common test symbols."""
    return ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]


@pytest.fixture
def many_symbols():
    """Large list of symbols for batch testing."""
    return [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
        "DOGEUSDT", "SOLUSDT", "DOTUSDT", "MATICUSDT", "LTCUSDT",
        "SHIBUSDT", "TRXUSDT", "AVAXUSDT", "LINKUSDT", "ATOMUSDT",
    ]


class TimingHelper:
    """Helper class for measuring execution time."""

    def __init__(self):
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = asyncio.get_event_loop().time()
        return self

    def __exit__(self, *args):
        self.end_time = asyncio.get_event_loop().time()

    @property
    def elapsed_ms(self):
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time) * 1000
        return None


@pytest.fixture
def timing():
    """Fixture for timing measurements."""
    return TimingHelper
