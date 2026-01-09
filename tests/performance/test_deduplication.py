"""TDD tests for request deduplication (Improvement #7).

These tests define the expected behavior for:
- In-flight request tracking
- Duplicate request handling
- Deduplication cache cleanup

Tests are expected to fail until implementation is complete.
"""

import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from crypto_mcp.models import MarkPriceResponse, OpenInterestResponse


class TestRequestDeduplication:
    """Tests for request deduplication."""

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="Request deduplication not yet implemented")
    async def test_concurrent_same_requests_deduplicated(self, mcp_server_with_mock):
        """Concurrent requests for same symbol should make only one API call."""
        mcp, mock_client = mcp_server_with_mock

        call_count = 0

        async def counting_get_mark_price(symbol=None):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # simulate network delay
            return MarkPriceResponse(
                symbol=symbol or "BTCUSDT",
                mark_price=Decimal("45000.00"),
                index_price=Decimal("44999.50"),
                last_funding_rate=Decimal("0.0001"),
                next_funding_time=1700003600000,
                exchange="binance",
            )

        mock_client.get_mark_price.side_effect = counting_get_mark_price

        tool_fn = mcp._tool_manager._tools["get_mark_price"].fn

        # launch 5 concurrent requests for same symbol
        tasks = [tool_fn(symbol="BTCUSDT") for _ in range(5)]
        results = await asyncio.gather(*tasks)

        # should only have made 1 API call
        assert call_count == 1

        # all results should be the same
        for result in results:
            assert result["symbol"] == "BTCUSDT"

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="Request deduplication not yet implemented")
    async def test_different_symbols_not_deduplicated(self, mcp_server_with_mock):
        """Requests for different symbols should not be deduplicated."""
        mcp, mock_client = mcp_server_with_mock

        call_count = 0
        symbols_called = []

        async def counting_get_mark_price(symbol=None):
            nonlocal call_count
            call_count += 1
            symbols_called.append(symbol)
            return MarkPriceResponse(
                symbol=symbol or "BTCUSDT",
                mark_price=Decimal("45000.00"),
                index_price=Decimal("44999.50"),
                last_funding_rate=Decimal("0.0001"),
                next_funding_time=1700003600000,
                exchange="binance",
            )

        mock_client.get_mark_price.side_effect = counting_get_mark_price

        tool_fn = mcp._tool_manager._tools["get_mark_price"].fn

        # request different symbols
        tasks = [
            tool_fn(symbol="BTCUSDT"),
            tool_fn(symbol="ETHUSDT"),
            tool_fn(symbol="SOLUSDT"),
        ]
        await asyncio.gather(*tasks)

        # should have made 3 API calls
        assert call_count == 3
        assert set(symbols_called) == {"BTCUSDT", "ETHUSDT", "SOLUSDT"}

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="Request deduplication not yet implemented")
    async def test_sequential_requests_not_deduplicated(self, mcp_server_with_mock):
        """Sequential requests (after first completes) should not be deduplicated."""
        mcp, mock_client = mcp_server_with_mock

        call_count = 0

        async def counting_get_mark_price(symbol=None):
            nonlocal call_count
            call_count += 1
            return MarkPriceResponse(
                symbol=symbol or "BTCUSDT",
                mark_price=Decimal("45000.00"),
                index_price=Decimal("44999.50"),
                last_funding_rate=Decimal("0.0001"),
                next_funding_time=1700003600000,
                exchange="binance",
            )

        mock_client.get_mark_price.side_effect = counting_get_mark_price

        tool_fn = mcp._tool_manager._tools["get_mark_price"].fn

        # make sequential requests (waiting for each to complete)
        await tool_fn(symbol="BTCUSDT")
        await tool_fn(symbol="BTCUSDT")

        # should have made 2 API calls (no caching, just deduplication)
        assert call_count == 2


class TestDeduplicationWithCaching:
    """Tests for interaction between deduplication and caching."""

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="Request deduplication not yet implemented")
    async def test_deduplication_works_before_cache_populated(
        self, mcp_server_with_mock
    ):
        """Deduplication should work even before cache is populated."""
        mcp, mock_client = mcp_server_with_mock

        call_count = 0

        async def slow_get_mark_price(symbol=None):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.2)  # slow request
            return MarkPriceResponse(
                symbol=symbol or "BTCUSDT",
                mark_price=Decimal("45000.00"),
                index_price=Decimal("44999.50"),
                last_funding_rate=Decimal("0.0001"),
                next_funding_time=1700003600000,
                exchange="binance",
            )

        mock_client.get_mark_price.side_effect = slow_get_mark_price

        tool_fn = mcp._tool_manager._tools["get_mark_price"].fn

        # launch concurrent requests immediately (before cache could be populated)
        tasks = [tool_fn(symbol="BTCUSDT") for _ in range(3)]
        await asyncio.gather(*tasks)

        # deduplication should have kicked in
        assert call_count == 1


class TestDeduplicationErrorHandling:
    """Tests for error handling in deduplication."""

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="Request deduplication not yet implemented")
    async def test_error_propagates_to_all_waiters(self, mcp_server_with_mock):
        """If deduplicated request fails, all waiters should get error."""
        mcp, mock_client = mcp_server_with_mock

        async def failing_request(symbol=None):
            await asyncio.sleep(0.1)
            raise Exception("API Error")

        mock_client.get_mark_price.side_effect = failing_request

        tool_fn = mcp._tool_manager._tools["get_mark_price"].fn

        # launch concurrent requests
        tasks = [tool_fn(symbol="BTCUSDT") for _ in range(3)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # all should get the same error
        for result in results:
            assert isinstance(result, Exception)
            assert "API Error" in str(result)

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="Request deduplication not yet implemented")
    async def test_cleanup_after_error(self, mcp_server_with_mock):
        """After error, in-flight tracking should be cleaned up."""
        mcp, mock_client = mcp_server_with_mock

        call_count = 0

        async def sometimes_failing_request(symbol=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("First call fails")
            return MarkPriceResponse(
                symbol=symbol or "BTCUSDT",
                mark_price=Decimal("45000.00"),
                index_price=Decimal("44999.50"),
                last_funding_rate=Decimal("0.0001"),
                next_funding_time=1700003600000,
                exchange="binance",
            )

        mock_client.get_mark_price.side_effect = sometimes_failing_request

        tool_fn = mcp._tool_manager._tools["get_mark_price"].fn

        # first request fails
        with pytest.raises(Exception):
            await tool_fn(symbol="BTCUSDT")

        # second request should work (not blocked by stale in-flight entry)
        result = await tool_fn(symbol="BTCUSDT")
        assert result["symbol"] == "BTCUSDT"
        assert call_count == 2
