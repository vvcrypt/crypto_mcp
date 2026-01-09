"""TDD tests for batch tools (Improvement #1).

These tests define the expected behavior for:
- get_funding_rate_batch
- get_long_short_ratio_batch
- get_open_interest_batch

Tests are expected to fail until implementations are complete.
"""

import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from crypto_mcp.models import (
    FundingRateResponse,
    LongShortRatioResponse,
    OpenInterestResponse,
)


class TestFundingRateBatch:
    """Tests for get_funding_rate_batch tool."""

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="get_funding_rate_batch not yet implemented")
    async def test_batch_returns_dict_keyed_by_symbol(
        self, mcp_server_with_mock, sample_symbols
    ):
        """Batch tool should return {symbol: [funding_rates]}."""
        mcp, mock_client = mcp_server_with_mock

        # setup mock to return data for each symbol
        async def mock_funding_rate(symbol, limit=100, **kwargs):
            return [
                FundingRateResponse(
                    symbol=symbol,
                    funding_rate=Decimal("0.0001"),
                    funding_time=1700000000000,
                    mark_price=Decimal("45000.00"),
                    exchange="binance",
                )
            ]

        mock_client.get_funding_rate.side_effect = mock_funding_rate

        # this tool doesn't exist yet - test will fail
        tool_fn = mcp._tool_manager._tools["get_funding_rate_batch"].fn
        result = await tool_fn(symbols=sample_symbols, limit=10)

        assert isinstance(result, dict)
        assert set(result.keys()) == set(s.upper() for s in sample_symbols)
        for symbol, rates in result.items():
            assert isinstance(rates, list)
            assert len(rates) > 0
            assert rates[0]["symbol"] == symbol

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="get_funding_rate_batch not yet implemented")
    async def test_batch_makes_parallel_requests(
        self, mcp_server_with_mock, sample_symbols
    ):
        """Batch should use asyncio.gather for parallel execution."""
        mcp, mock_client = mcp_server_with_mock

        call_times = []

        async def mock_funding_rate(symbol, limit=100, **kwargs):
            call_times.append(asyncio.get_event_loop().time())
            await asyncio.sleep(0.1)  # simulate network delay
            return [
                FundingRateResponse(
                    symbol=symbol,
                    funding_rate=Decimal("0.0001"),
                    funding_time=1700000000000,
                    mark_price=Decimal("45000.00"),
                    exchange="binance",
                )
            ]

        mock_client.get_funding_rate.side_effect = mock_funding_rate

        tool_fn = mcp._tool_manager._tools["get_funding_rate_batch"].fn

        start = asyncio.get_event_loop().time()
        await tool_fn(symbols=sample_symbols, limit=10)
        elapsed = asyncio.get_event_loop().time() - start

        # if parallel: ~0.1s total; if sequential: ~0.5s (5 * 0.1s)
        # allow some overhead but should be way less than sequential
        assert elapsed < 0.3, f"Batch took {elapsed}s, expected <0.3s (parallel)"

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="get_funding_rate_batch not yet implemented")
    async def test_batch_handles_empty_list(self, mcp_server_with_mock):
        """Batch should return empty dict for empty input."""
        mcp, _ = mcp_server_with_mock

        tool_fn = mcp._tool_manager._tools["get_funding_rate_batch"].fn
        result = await tool_fn(symbols=[], limit=10)

        assert result == {}

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="get_funding_rate_batch not yet implemented")
    async def test_batch_uppercases_symbols(self, mcp_server_with_mock):
        """Batch should uppercase symbol names."""
        mcp, mock_client = mcp_server_with_mock

        mock_client.get_funding_rate.return_value = [
            FundingRateResponse(
                symbol="BTCUSDT",
                funding_rate=Decimal("0.0001"),
                funding_time=1700000000000,
                mark_price=Decimal("45000.00"),
                exchange="binance",
            )
        ]

        tool_fn = mcp._tool_manager._tools["get_funding_rate_batch"].fn
        result = await tool_fn(symbols=["btcusdt"], limit=10)

        assert "BTCUSDT" in result


class TestLongShortRatioBatch:
    """Tests for get_long_short_ratio_batch tool."""

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="get_long_short_ratio_batch not yet implemented")
    async def test_batch_returns_dict_keyed_by_symbol(
        self, mcp_server_with_mock, sample_symbols
    ):
        """Batch tool should return {symbol: [ratios]}."""
        mcp, mock_client = mcp_server_with_mock

        async def mock_ls_ratio(symbol, period, limit=30, **kwargs):
            return [
                LongShortRatioResponse(
                    symbol=symbol,
                    long_short_ratio=Decimal("1.5"),
                    long_account=Decimal("60.0"),
                    short_account=Decimal("40.0"),
                    timestamp=1700000000000,
                    exchange="binance",
                )
            ]

        mock_client.get_long_short_ratio.side_effect = mock_ls_ratio

        tool_fn = mcp._tool_manager._tools["get_long_short_ratio_batch"].fn
        result = await tool_fn(symbols=sample_symbols, period="1h", limit=10)

        assert isinstance(result, dict)
        assert set(result.keys()) == set(s.upper() for s in sample_symbols)

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="get_long_short_ratio_batch not yet implemented")
    async def test_batch_requires_period_parameter(self, mcp_server_with_mock):
        """Period is required for long/short ratio queries."""
        mcp, _ = mcp_server_with_mock

        tool_fn = mcp._tool_manager._tools["get_long_short_ratio_batch"].fn

        # should raise TypeError or similar for missing period
        with pytest.raises(TypeError):
            await tool_fn(symbols=["BTCUSDT"])


class TestOpenInterestBatch:
    """Tests for get_open_interest_batch tool (current OI, not history)."""

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="get_open_interest_batch not yet implemented")
    async def test_batch_returns_dict_keyed_by_symbol(
        self, mcp_server_with_mock, sample_symbols
    ):
        """Batch tool should return {symbol: oi_data}."""
        mcp, mock_client = mcp_server_with_mock

        async def mock_oi(symbol):
            return OpenInterestResponse(
                symbol=symbol,
                open_interest=Decimal("100000.0"),
                timestamp=1700000000000,
                exchange="binance",
            )

        mock_client.get_open_interest.side_effect = mock_oi

        tool_fn = mcp._tool_manager._tools["get_open_interest_batch"].fn
        result = await tool_fn(symbols=sample_symbols)

        assert isinstance(result, dict)
        assert set(result.keys()) == set(s.upper() for s in sample_symbols)
        for symbol, data in result.items():
            assert data["symbol"] == symbol
            assert "open_interest" in data

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="get_open_interest_batch not yet implemented")
    async def test_batch_faster_than_sequential(
        self, mcp_server_with_mock, many_symbols
    ):
        """Batch should be significantly faster than sequential calls."""
        mcp, mock_client = mcp_server_with_mock

        async def mock_oi(symbol):
            await asyncio.sleep(0.05)  # 50ms per request
            return OpenInterestResponse(
                symbol=symbol,
                open_interest=Decimal("100000.0"),
                timestamp=1700000000000,
                exchange="binance",
            )

        mock_client.get_open_interest.side_effect = mock_oi

        tool_fn = mcp._tool_manager._tools["get_open_interest_batch"].fn

        start = asyncio.get_event_loop().time()
        await tool_fn(symbols=many_symbols)
        elapsed = asyncio.get_event_loop().time() - start

        # 15 symbols * 50ms = 750ms sequential
        # parallel should be ~50-100ms
        assert elapsed < 0.3, f"Batch took {elapsed}s, expected <0.3s"


class TestExistingBatchTools:
    """Verify existing batch tools work correctly (regression tests)."""

    @pytest.mark.asyncio
    async def test_klines_batch_exists(self, mcp_server_with_mock):
        """Verify get_klines_batch tool is registered."""
        mcp, _ = mcp_server_with_mock
        assert "get_klines_batch" in mcp._tool_manager._tools

    @pytest.mark.asyncio
    async def test_open_interest_history_batch_exists(self, mcp_server_with_mock):
        """Verify get_open_interest_history_batch tool is registered."""
        mcp, _ = mcp_server_with_mock
        assert "get_open_interest_history_batch" in mcp._tool_manager._tools
