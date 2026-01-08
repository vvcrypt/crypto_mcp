"""FastMCP server for cryptocurrency futures data."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

import httpx
from mcp.server.fastmcp import FastMCP

from crypto_mcp.config import Settings
from crypto_mcp.exchanges.binance import BinanceClient
from crypto_mcp.exchanges.binance.endpoints import BASE_URL
from crypto_mcp.tools import register_all_tools


settings = Settings()


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Manage server lifecycle - creates and closes HTTP client."""
    async with httpx.AsyncClient(
        base_url=settings.binance_futures_base_url or BASE_URL,
        timeout=settings.http_timeout,
    ) as http_client:
        client = BinanceClient(http_client=http_client)
        register_all_tools(server, client)
        yield


mcp = FastMCP(
    name=settings.server_name,
    lifespan=lifespan,
)
