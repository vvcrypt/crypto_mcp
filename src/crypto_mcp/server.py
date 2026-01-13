"""FastMCP server for cryptocurrency futures data."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

import httpx
from mcp.server.fastmcp import FastMCP

from crypto_mcp.config import Settings
from crypto_mcp.exchanges.binance import BinanceClient
from crypto_mcp.exchanges.binance.endpoints import BASE_URL as BINANCE_BASE_URL
from crypto_mcp.exchanges.bybit import BybitClient
from crypto_mcp.exchanges.bybit.endpoints import BASE_URL as BYBIT_BASE_URL
from crypto_mcp.tools import register_all_tools
from crypto_mcp.utils.rate_limiter import SlidingWindowRateLimiter


settings = Settings()


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Manage server lifecycle - creates clients for all exchanges."""
    # create rate limiters if enabled
    binance_limiter = (
        SlidingWindowRateLimiter(max_requests=settings.binance_rate_limit)
        if settings.rate_limit_enabled
        else None
    )
    bybit_limiter = (
        SlidingWindowRateLimiter(max_requests=settings.bybit_rate_limit)
        if settings.rate_limit_enabled
        else None
    )

    # create separate HTTP clients for each exchange
    async with httpx.AsyncClient(
        base_url=settings.binance_futures_base_url or BINANCE_BASE_URL,
        timeout=settings.http_timeout,
    ) as binance_http:
        async with httpx.AsyncClient(
            base_url=settings.bybit_futures_base_url or BYBIT_BASE_URL,
            timeout=settings.http_timeout,
        ) as bybit_http:
            # create exchange clients with rate limiters
            clients = {
                "binance": BinanceClient(
                    http_client=binance_http,
                    rate_limiter=binance_limiter,
                    max_retries=settings.rate_limit_max_retries,
                ),
                "bybit": BybitClient(
                    http_client=bybit_http,
                    rate_limiter=bybit_limiter,
                    max_retries=settings.rate_limit_max_retries,
                ),
            }
            register_all_tools(server, clients)
            yield


mcp = FastMCP(
    name=settings.server_name,
    lifespan=lifespan,
)
