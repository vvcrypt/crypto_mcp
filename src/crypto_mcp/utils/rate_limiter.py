"""Rate limiting utilities for API request throttling."""

import asyncio
import time
from collections import deque


class SlidingWindowRateLimiter:
    """Tracks requests in a sliding window and throttles when approaching limit.

    This rate limiter uses a sliding window algorithm to track requests over time.
    When the limit is reached, it automatically waits until capacity is available.

    Example:
        limiter = SlidingWindowRateLimiter(max_requests=100, window_seconds=60)

        # before each API call
        await limiter.acquire()
        response = await client.get(...)
    """

    def __init__(
        self,
        max_requests: int,
        window_seconds: int = 60,
    ):
        """Initialize the rate limiter.

        Args:
            max_requests: Maximum number of requests allowed in the window.
            window_seconds: Size of the sliding window in seconds (default: 60).
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> float:
        """Wait if necessary, then record a request.

        Returns:
            The wait time in seconds (0 if no wait was needed).
        """
        async with self._lock:
            now = time.monotonic()
            self._cleanup_old_requests(now)
            total_wait = 0.0

            # if at limit, wait until oldest request expires
            while len(self._requests) >= self.max_requests:
                wait_time = self._requests[0] + self.window_seconds - now
                if wait_time > 0:
                    total_wait += wait_time
                    await asyncio.sleep(wait_time)
                now = time.monotonic()
                self._cleanup_old_requests(now)

            self._requests.append(now)
            return total_wait

    def _cleanup_old_requests(self, now: float) -> None:
        """Remove requests outside the sliding window."""
        cutoff = now - self.window_seconds
        while self._requests and self._requests[0] < cutoff:
            self._requests.popleft()

    @property
    def current_count(self) -> int:
        """Return current number of requests in the window."""
        now = time.monotonic()
        self._cleanup_old_requests(now)
        return len(self._requests)

    @property
    def current_usage(self) -> float:
        """Return current usage as percentage (0.0 - 1.0)."""
        return self.current_count / self.max_requests

    @property
    def available_capacity(self) -> int:
        """Return number of requests that can be made immediately."""
        return max(0, self.max_requests - self.current_count)

    def reset(self) -> None:
        """Clear all tracked requests."""
        self._requests.clear()
