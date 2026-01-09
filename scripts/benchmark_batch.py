#!/usr/bin/env python3
"""Benchmark script to measure batch vs sequential tool performance."""

import asyncio
import time
from unittest.mock import AsyncMock, patch

from mcp.server.fastmcp import FastMCP

from crypto_mcp.exchanges.binance import BinanceClient
from crypto_mcp.models import OpenInterestResponse, FundingRateResponse, LongShortRatioResponse
from crypto_mcp.tools import register_all_tools


# simulated API latency in seconds
API_LATENCY = 0.2


async def create_mock_server():
    """Create MCP server with mock client that simulates API latency."""
    mcp = FastMCP("benchmark")
    mock_client = AsyncMock(spec=BinanceClient)

    # mock get_open_interest with simulated latency
    async def mock_get_open_interest(symbol: str):
        await asyncio.sleep(API_LATENCY)
        return OpenInterestResponse(
            symbol=symbol,
            open_interest=50000.0,
            timestamp=1700000000000,
            exchange="binance",
        )

    # mock get_funding_rate with simulated latency
    async def mock_get_funding_rate(symbol: str, limit: int, start_time=None, end_time=None):
        await asyncio.sleep(API_LATENCY)
        return [
            FundingRateResponse(
                symbol=symbol,
                funding_rate=0.0001,
                funding_time=1700000000000,
                mark_price=45000.0,
                exchange="binance",
            )
        ]

    # mock get_long_short_ratio with simulated latency
    async def mock_get_long_short_ratio(symbol: str, period: str, limit: int, start_time=None, end_time=None):
        await asyncio.sleep(API_LATENCY)
        return [
            LongShortRatioResponse(
                symbol=symbol,
                long_short_ratio=1.5,
                long_account=0.6,
                short_account=0.4,
                timestamp=1700000000000,
                exchange="binance",
            )
        ]

    mock_client.get_open_interest = mock_get_open_interest
    mock_client.get_funding_rate = mock_get_funding_rate
    mock_client.get_long_short_ratio = mock_get_long_short_ratio

    register_all_tools(mcp, mock_client)
    return mcp


async def benchmark_sequential(mcp: FastMCP, tool_name: str, symbols: list[str], extra_args: dict = None):
    """Benchmark sequential single-symbol calls."""
    tool_fn = mcp._tool_manager._tools[tool_name].fn
    extra_args = extra_args or {}

    start = time.perf_counter()
    for symbol in symbols:
        await tool_fn(symbol=symbol, **extra_args)
    elapsed = time.perf_counter() - start

    return elapsed


async def benchmark_batch(mcp: FastMCP, tool_name: str, symbols: list[str], extra_args: dict = None):
    """Benchmark batch tool call."""
    tool_fn = mcp._tool_manager._tools[tool_name].fn
    extra_args = extra_args or {}

    start = time.perf_counter()
    await tool_fn(symbols=symbols, **extra_args)
    elapsed = time.perf_counter() - start

    return elapsed


async def run_benchmarks():
    """Run all benchmarks and print results."""
    mcp = await create_mock_server()

    symbol_counts = [5, 10, 15, 20]

    print("=" * 70)
    print("BATCH TOOL PERFORMANCE BENCHMARK")
    print(f"Simulated API latency: {API_LATENCY * 1000:.0f}ms per request")
    print("=" * 70)

    benchmarks = [
        {
            "name": "Open Interest",
            "single": "get_open_interest",
            "batch": "get_open_interest_batch",
            "extra_args": {},
        },
        {
            "name": "Funding Rate",
            "single": "get_funding_rate",
            "batch": "get_funding_rate_batch",
            "extra_args": {"limit": 10},
        },
        {
            "name": "Long/Short Ratio",
            "single": "get_long_short_ratio",
            "batch": "get_long_short_ratio_batch",
            "extra_args": {"period": "1h", "limit": 10},
        },
    ]

    for bench in benchmarks:
        print(f"\n{bench['name']}")
        print("-" * 70)
        print(f"{'Symbols':<10} {'Sequential':<15} {'Batch':<15} {'Speedup':<10} {'Saved':<15}")
        print("-" * 70)

        for count in symbol_counts:
            symbols = [f"SYMBOL{i}USDT" for i in range(count)]

            seq_time = await benchmark_sequential(
                mcp, bench["single"], symbols, bench["extra_args"]
            )
            batch_time = await benchmark_batch(
                mcp, bench["batch"], symbols, bench["extra_args"]
            )

            speedup = seq_time / batch_time
            saved = seq_time - batch_time

            print(
                f"{count:<10} {seq_time*1000:>10.0f}ms    {batch_time*1000:>10.0f}ms    "
                f"{speedup:>6.1f}x     {saved*1000:>10.0f}ms"
            )

    print("\n" + "=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    print(f"""
Batch tools execute all HTTP requests in parallel using asyncio.gather.
Sequential calls wait for each request to complete before starting the next.

With {API_LATENCY*1000:.0f}ms API latency:
- Sequential: ~{API_LATENCY*1000:.0f}ms x N symbols
- Batch: ~{API_LATENCY*1000:.0f}ms total (parallel execution)

In production with Claude Desktop, add ~5s "thinking time" between sequential
tool calls, making the difference even more dramatic:
- 15 symbols sequential: ~80s (with Claude thinking time)
- 15 symbols batch: ~5s (single tool call)
""")


if __name__ == "__main__":
    asyncio.run(run_benchmarks())
