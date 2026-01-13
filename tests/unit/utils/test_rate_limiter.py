"""Tests for the sliding window rate limiter."""

import asyncio
import time

import pytest

from crypto_mcp.utils.rate_limiter import SlidingWindowRateLimiter


class TestSlidingWindowRateLimiter:
    """Tests for SlidingWindowRateLimiter."""

    @pytest.mark.asyncio
    async def test_allows_requests_under_limit(self):
        """Requests under the limit should be allowed immediately."""
        limiter = SlidingWindowRateLimiter(max_requests=10, window_seconds=60)

        for _ in range(5):
            wait_time = await limiter.acquire()
            assert wait_time == 0.0

        assert limiter.current_count == 5
        assert limiter.available_capacity == 5

    @pytest.mark.asyncio
    async def test_blocks_when_at_limit(self):
        """Should block when limit is reached until window expires."""
        limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=0.1)

        # fill up the limit
        for _ in range(3):
            await limiter.acquire()

        assert limiter.current_count == 3
        assert limiter.available_capacity == 0

        # next request should wait
        start = time.monotonic()
        await limiter.acquire()
        elapsed = time.monotonic() - start

        # should have waited approximately 0.1 seconds
        assert elapsed >= 0.05  # allow some tolerance

    @pytest.mark.asyncio
    async def test_sliding_window_cleanup(self):
        """Old requests should be cleaned up after window expires."""
        limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=0.1)

        # make some requests
        for _ in range(3):
            await limiter.acquire()

        assert limiter.current_count == 3

        # wait for window to expire
        await asyncio.sleep(0.15)

        assert limiter.current_count == 0
        assert limiter.available_capacity == 5

    @pytest.mark.asyncio
    async def test_current_usage_percentage(self):
        """current_usage should return correct percentage."""
        limiter = SlidingWindowRateLimiter(max_requests=10, window_seconds=60)

        await limiter.acquire()
        assert limiter.current_usage == 0.1

        for _ in range(4):
            await limiter.acquire()
        assert limiter.current_usage == 0.5

    @pytest.mark.asyncio
    async def test_reset_clears_all_requests(self):
        """reset() should clear all tracked requests."""
        limiter = SlidingWindowRateLimiter(max_requests=10, window_seconds=60)

        for _ in range(5):
            await limiter.acquire()

        assert limiter.current_count == 5

        limiter.reset()

        assert limiter.current_count == 0
        assert limiter.available_capacity == 10

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Multiple concurrent requests should be handled correctly."""
        limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=60)

        # make 5 concurrent requests
        tasks = [limiter.acquire() for _ in range(5)]
        await asyncio.gather(*tasks)

        assert limiter.current_count == 5

    @pytest.mark.asyncio
    async def test_returns_wait_time(self):
        """acquire() should return actual wait time."""
        limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=0.1)

        # first two should not wait
        wait1 = await limiter.acquire()
        wait2 = await limiter.acquire()
        assert wait1 == 0.0
        assert wait2 == 0.0

        # third should wait
        wait3 = await limiter.acquire()
        assert wait3 > 0.0

    @pytest.mark.asyncio
    async def test_high_throughput(self):
        """Should handle high throughput correctly."""
        limiter = SlidingWindowRateLimiter(max_requests=100, window_seconds=1)

        start = time.monotonic()

        # make 100 requests (should be instant)
        for _ in range(100):
            await limiter.acquire()

        first_batch = time.monotonic() - start

        # next 10 requests should have to wait
        for _ in range(10):
            await limiter.acquire()

        total = time.monotonic() - start

        # first 100 should be fast
        assert first_batch < 0.5
        # additional requests should cause waiting
        assert total > first_batch
