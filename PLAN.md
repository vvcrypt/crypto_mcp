# Crypto Data MCP Server - Detailed Implementation Plan

## Project Goal
Build an MCP server that gives LLMs access to cryptocurrency futures market data from Binance (and later other exchanges) via REST APIs.

---

## Background Context

### What is MCP (Model Context Protocol)?

MCP is an open protocol created by Anthropic that standardizes how LLMs communicate with external tools and data sources. Think of it as a "USB port for AI" - a universal way to plug capabilities into AI assistants.

**How it works:**
```
┌─────────────┐     MCP Protocol      ┌─────────────┐
│   Claude    │ ←──────────────────→  │  MCP Server │
│   (Client)  │   JSON-RPC over       │  (Our Code) │
│             │   stdio/HTTP          │             │
└─────────────┘                       └─────────────┘
                                            │
                                            ▼
                                      ┌───────────┐
                                      │  Binance  │
                                      │    API    │
                                      └───────────┘
```

**MCP exposes three types of capabilities:**
1. **Tools** - Functions the LLM can call (we use this)
   - Example: `get_open_interest(symbol="BTCUSDT")`
   - LLM decides when to call, server executes and returns result
2. **Resources** - Read-only data (like files)
   - Not used in our project
3. **Prompts** - Reusable prompt templates
   - Not used in our project

**Why MCP matters for us:**
- Claude can directly query crypto data without user copy-pasting
- Standardized interface = works with any MCP-compatible client
- No custom integration needed per LLM

### What is FastMCP?

FastMCP is a Python framework (now part of the official MCP SDK) that makes building MCP servers easy. It's like Flask for MCP.

**Without FastMCP (raw MCP):**
```python
# Verbose, manual JSON schema definition
server = Server("crypto")
@server.call_tool()
async def handle_tool(name, arguments):
    if name == "get_open_interest":
        # manual argument parsing
        # manual response formatting
```

**With FastMCP:**
```python
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("crypto")

@mcp.tool()
async def get_open_interest(symbol: str) -> dict:
    """Get current open interest for a futures symbol."""
    # Type hints become JSON schema automatically
    # Docstring becomes tool description
    return {"symbol": symbol, "open_interest": 12345}
```

**FastMCP handles:**
- JSON schema generation from type hints
- Request/response serialization
- Error formatting
- Transport (stdio/HTTP)

### Binance USDT-M Futures API

We're using Binance's USDT-Margined Futures API (not Spot, not Coin-M).

**Base URL:** `https://fapi.binance.com`

**Why USDT-M Futures?**
- Most liquid crypto derivatives market
- All data endpoints are public (no auth needed)
- Good historical data availability
- Standard for crypto trading analysis

**Key Concepts:**

| Term | Meaning |
|------|---------|
| **Open Interest (OI)** | Total number of outstanding futures contracts. Rising OI = new money entering. |
| **Funding Rate** | Periodic payment between longs and shorts to keep futures price near spot. Positive = longs pay shorts. |
| **Mark Price** | Fair price calculated from index + funding. Used for liquidations. |
| **Klines/Candlesticks** | OHLCV data (Open, High, Low, Close, Volume) at intervals. |
| **Long/Short Ratio** | Ratio of long vs short positions among top traders. |

**API Response Examples:**

Open Interest (`/fapi/v1/openInterest`):
```json
{
  "symbol": "BTCUSDT",
  "openInterest": "12345.678",    // in BTC
  "time": 1700000000000           // unix ms
}
```

Funding Rate (`/fapi/v1/fundingRate`):
```json
[
  {
    "symbol": "BTCUSDT",
    "fundingRate": "0.00010000",  // 0.01%
    "fundingTime": 1700000000000,
    "markPrice": "45000.00"
  }
]
```

Klines (`/fapi/v1/klines`):
```json
[
  [
    1700000000000,    // open time
    "45000.00",       // open
    "45500.00",       // high
    "44800.00",       // low
    "45200.00",       // close
    "1234.567",       // volume
    1700003600000,    // close time
    "55555555.00",    // quote volume
    5000,             // trade count
    "600.123",        // taker buy base
    "27000000.00"     // taker buy quote
  ]
]
```

**Rate Limits:**
- 2400 request weight per minute (IP-based)
- Most endpoints = 1-5 weight
- No API key = works fine for our use case
- Optional API key = higher limits

### How The Pieces Connect

```
User asks Claude: "What's the open interest for BTC futures?"
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Claude decides to call get_open_interest tool              │
│  Sends: {"method": "tools/call", "params": {                │
│           "name": "get_open_interest",                      │
│           "arguments": {"symbol": "BTCUSDT"}}}              │
└─────────────────────────────────────────────────────────────┘
                            │ (stdio pipe)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  FastMCP Server (server.py)                                 │
│  - Receives JSON-RPC request                                │
│  - Routes to @mcp.tool() handler                            │
│  - Passes to get_open_interest() in tools/open_interest.py  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Tool Handler (tools/open_interest.py)                      │
│  - Validates input (symbol format)                          │
│  - Calls binance_client.get_open_interest("BTCUSDT")        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Binance Client (exchanges/binance/client.py)               │
│  - Builds URL: https://fapi.binance.com/fapi/v1/openInterest│
│  - Makes HTTP GET request via httpx                         │
│  - Parses JSON response into BinanceOpenInterest model      │
│  - Converts to OpenInterestResponse (unified format)        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Response flows back up                                     │
│  - Tool returns OpenInterestResponse                        │
│  - FastMCP serializes to JSON                               │
│  - Sends back to Claude via stdio                           │
│  - Claude presents answer to user                           │
└─────────────────────────────────────────────────────────────┘
```

### Why This Architecture?

| Layer | Purpose | Benefit |
|-------|---------|---------|
| **FastMCP + Tools** | MCP protocol handling | Standardized interface, auto JSON schema |
| **Exchange Abstraction** | Common interface | Add Bybit/OKX without changing tools |
| **Binance Client** | API specifics isolated | Easy to update when Binance changes |
| **Pydantic Models** | Type safety | Catch errors at parse time, not runtime |
| **Unified Responses** | Exchange-agnostic output | LLM sees consistent format regardless of source |

---

## Architecture Decision: Hybrid Structure

### The Choice
We organize code in two layers:
1. **Exchange Layer** (`exchanges/`) - Raw API clients, one folder per exchange
2. **Tool Layer** (`tools/`) - MCP tool definitions, one file per function type

### Why Hybrid?

| Approach | Pros | Cons |
|----------|------|------|
| **By Exchange Only** | Self-contained exchanges, easy to add/remove | Duplicate MCP logic, harder to ensure consistent tool interfaces |
| **By Function Only** | Easy to compare implementations | Exchange code scattered, harder to swap exchanges |
| **Hybrid** | Clean separation of concerns, exchange code isolated, tools are thin wrappers | Slightly more files |

**Decision**: Hybrid gives us the best of both:
- Adding Bybit = add `exchanges/bybit/` folder, minimal tool changes
- Tools stay thin and focused on MCP interface
- Exchange clients can be tested independently of MCP

---

## Directory Structure with Reasoning

```
crypto_mcp/
├── pyproject.toml              # WHY: Standard Python project metadata, dependencies
├── README.md                   # WHY: User documentation (exists)
├── CLAUDE.md                   # WHY: Code style rules (exists)
├── PLAN.md                     # WHY: This file - implementation guide
├── .env.example                # WHY: Template for env vars, no secrets committed
│
├── src/                        # WHY: src layout is Python best practice
│   └── crypto_mcp/             # WHY: Package name matches project
│       ├── __init__.py         # WHY: Package marker, exposes version
│       ├── __main__.py         # WHY: Allows `python -m crypto_mcp`
│       ├── server.py           # WHY: Single entry point, FastMCP setup
│       ├── config.py           # WHY: Centralized config, env vars -> typed Settings
│       │
│       ├── exchanges/          # WHY: Isolate exchange-specific API logic
│       │   ├── __init__.py
│       │   ├── base.py         # WHY: Abstract interface, enforces consistency
│       │   │                   #      across exchanges, enables polymorphism
│       │   └── binance/
│       │       ├── __init__.py
│       │       ├── client.py   # WHY: Single class for all Binance API calls
│       │       ├── endpoints.py# WHY: URL constants in one place, easy to update
│       │       ├── models.py   # WHY: Parse Binance JSON -> typed objects
│       │       └── exceptions.py # WHY: Binance-specific error codes
│       │
│       ├── tools/              # WHY: MCP tool definitions, separate from API logic
│       │   ├── __init__.py     # WHY: Registers all tools with FastMCP
│       │   ├── open_interest.py
│       │   ├── funding_rate.py
│       │   ├── ticker.py
│       │   ├── klines.py
│       │   ├── mark_price.py
│       │   └── long_short_ratio.py
│       │
│       ├── models/             # WHY: Shared types across all exchanges
│       │   ├── __init__.py
│       │   ├── common.py       # WHY: Validators (intervals, periods)
│       │   └── responses.py    # WHY: Unified response types LLM sees
│       │
│       ├── exceptions/         # WHY: Consistent error handling
│       │   ├── __init__.py
│       │   ├── base.py         # WHY: Error hierarchy (ExchangeError, ValidationError)
│       │   └── handlers.py     # WHY: Convert exchange errors -> MCP ToolErrors
│       │
│       └── utils/              # WHY: Shared utilities
│           ├── __init__.py
│           └── http.py         # WHY: Configured httpx client factory
│
└── tests/                      # WHY: Tests alongside code, pytest standard
    ├── conftest.py             # WHY: Shared fixtures (mock clients, settings)
    ├── unit/                   # WHY: Fast, isolated tests
    │   ├── exchanges/
    │   │   └── binance/
    │   │       ├── test_client.py
    │   │       └── test_models.py
    │   └── tools/
    │       ├── test_open_interest.py
    │       └── ...
    └── integration/            # WHY: End-to-end MCP protocol tests
        └── test_server.py
```

---

## Dependencies with Reasoning

```toml
[project]
dependencies = [
    "mcp[cli]>=1.0.0",      # WHY: Official MCP SDK with FastMCP framework
    "httpx>=0.27.0",        # WHY: Modern async HTTP, better than aiohttp/requests
    "pydantic>=2.0.0",      # WHY: Data validation, JSON schema generation
    "pydantic-settings>=2.0.0",  # WHY: Env var -> Settings mapping
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",        # WHY: Standard test framework
    "pytest-asyncio>=0.24.0",  # WHY: Async test support
    "pytest-httpx>=0.30.0", # WHY: Mock httpx requests
    "ruff>=0.5.0",          # WHY: Fast linter/formatter
    "mypy>=1.10.0",         # WHY: Type checking
]
```

### Why These Specific Libraries?

| Library | Why This One | Alternatives Considered |
|---------|--------------|------------------------|
| `mcp` | Official SDK, FastMCP included, maintained by Anthropic | None - this is the standard |
| `httpx` | Async-native, better API than requests, connection pooling | `aiohttp` (more complex), `requests` (sync only) |
| `pydantic` | Industry standard, auto JSON schema, great error messages | `dataclasses` (no validation), `attrs` (less ecosystem) |
| `pytest` | De facto standard, rich plugin ecosystem | `unittest` (verbose), `nose` (deprecated) |

---

## MCP Tools Specification

Each tool is a thin wrapper: validate input -> call exchange client -> return response.

### Tool 1: `get_open_interest`
```
Purpose: Current open interest for a symbol
Input: symbol (required)
Output: { symbol, open_interest, timestamp, exchange }
Binance endpoint: GET /fapi/v1/openInterest
```

### Tool 2: `get_open_interest_history`
```
Purpose: Historical open interest
Input: symbol (required), period (5m-1d), limit (1-500), start_time, end_time
Output: List of { symbol, open_interest, timestamp, exchange }
Binance endpoint: GET /futures/data/openInterestHist
```

### Tool 3: `get_funding_rate`
```
Purpose: Funding rate history
Input: symbol (optional), limit (1-1000), start_time, end_time
Output: List of { symbol, funding_rate, funding_time, exchange }
Binance endpoint: GET /fapi/v1/fundingRate
```

### Tool 4: `get_ticker_24h`
```
Purpose: 24h price and volume statistics
Input: symbol (optional, omit for all symbols)
Output: { symbol, price_change, price_change_percent, volume, high, low, ... }
Binance endpoint: GET /fapi/v1/ticker/24hr
```

### Tool 5: `get_klines`
```
Purpose: OHLCV candlestick data
Input: symbol (required), interval (1m-1M), limit (1-1500), start_time, end_time
Output: { symbol, interval, candles: [{ open, high, low, close, volume, ... }] }
Binance endpoint: GET /fapi/v1/klines
```

### Tool 6: `get_mark_price`
```
Purpose: Current mark price and funding info
Input: symbol (optional)
Output: { symbol, mark_price, index_price, funding_rate, next_funding_time, ... }
Binance endpoint: GET /fapi/v1/premiumIndex
```

### Tool 7: `get_long_short_ratio`
```
Purpose: Top trader long/short position ratio
Input: symbol (required), period (5m-1d), limit (1-500), start_time, end_time
Output: List of { symbol, long_short_ratio, long_account, short_account, timestamp }
Binance endpoint: GET /futures/data/topLongShortPositionRatio
```

---

## Build Sequence (Granular Steps)

Each step is independently testable. Run tests after each step.

### Phase 1: Project Foundation
**Goal**: Runnable Python package with config

| Step | File | What | Why |
|------|------|------|-----|
| 1.1 | `pyproject.toml` | Project metadata, deps | Need installable package |
| 1.2 | `src/crypto_mcp/__init__.py` | `__version__ = "0.1.0"` | Package marker |
| 1.3 | `src/crypto_mcp/config.py` | `Settings` class | Centralized config |
| 1.4 | `tests/conftest.py` | `settings` fixture | Test infrastructure |
| 1.5 | `tests/unit/test_config.py` | Config loading tests | Verify config works |

**Checkpoint**: `pip install -e .` works, `pytest` passes

### Phase 2: Exception Hierarchy
**Goal**: Consistent error types

| Step | File | What | Why |
|------|------|------|-----|
| 2.1 | `src/crypto_mcp/exceptions/base.py` | `CryptoMCPError`, `ExchangeError`, etc. | Error classification |
| 2.2 | `src/crypto_mcp/exceptions/__init__.py` | Export exceptions | Clean imports |

**Checkpoint**: Can import and raise custom exceptions

### Phase 3: Shared Models
**Goal**: Reusable types

| Step | File | What | Why |
|------|------|------|-----|
| 3.1 | `src/crypto_mcp/models/common.py` | `ValidInterval`, `ValidPeriod` validators | Input validation |
| 3.2 | `src/crypto_mcp/models/responses.py` | `OpenInterestResponse`, etc. | Unified outputs |
| 3.3 | `src/crypto_mcp/models/__init__.py` | Export models | Clean imports |

**Checkpoint**: Can create and serialize response models

### Phase 4: Exchange Abstraction
**Goal**: Interface for all exchanges

| Step | File | What | Why |
|------|------|------|-----|
| 4.1 | `src/crypto_mcp/exchanges/base.py` | `BaseExchangeClient` ABC | Enforces consistency |
| 4.2 | `src/crypto_mcp/exchanges/__init__.py` | Export base | Clean imports |

**Checkpoint**: Abstract interface defined

### Phase 5: Binance Client
**Goal**: Working Binance API client

| Step | File | What | Why |
|------|------|------|-----|
| 5.1 | `src/crypto_mcp/exchanges/binance/endpoints.py` | URL constants | Centralized URLs |
| 5.2 | `src/crypto_mcp/exchanges/binance/exceptions.py` | `BinanceAPIError` | Binance error codes |
| 5.3 | `src/crypto_mcp/exchanges/binance/models.py` | Parse Binance responses | JSON -> typed objects |
| 5.4 | `src/crypto_mcp/exchanges/binance/client.py` | `BinanceClient` class | API implementation |
| 5.5 | `src/crypto_mcp/exchanges/binance/__init__.py` | Export client | Clean imports |
| 5.6 | `tests/unit/exchanges/binance/test_models.py` | Model parsing tests | Verify parsing |
| 5.7 | `tests/unit/exchanges/binance/test_client.py` | Client tests with mocks | Verify API calls |

**Checkpoint**: Can call Binance client methods with mocked HTTP

### Phase 6: Utilities
**Goal**: Shared helpers

| Step | File | What | Why |
|------|------|------|-----|
| 6.1 | `src/crypto_mcp/utils/http.py` | HTTP client factory | Configured client |
| 6.2 | `src/crypto_mcp/utils/__init__.py` | Export utils | Clean imports |
| 6.3 | `src/crypto_mcp/exceptions/handlers.py` | Error conversion | Exchange -> ToolError |

**Checkpoint**: Can create HTTP client, convert errors

### Phase 7: MCP Tools (One at a Time)
**Goal**: Working MCP tools

For each tool (repeat 7x):
| Step | File | What | Why |
|------|------|------|-----|
| 7.N.1 | `src/crypto_mcp/tools/{name}.py` | Tool definition | MCP interface |
| 7.N.2 | `tests/unit/tools/test_{name}.py` | Tool tests | Verify behavior |

Order:
1. open_interest (simplest, good starting point)
2. mark_price (similar structure)
3. ticker (optional symbol parameter)
4. klines (more parameters)
5. funding_rate (pagination)
6. open_interest_history (historical data pattern)
7. long_short_ratio (similar to OI history)

| Step | File | What |
|------|------|------|
| 7.8 | `src/crypto_mcp/tools/__init__.py` | `register_all_tools()` |

**Checkpoint**: Each tool can be called via MCP protocol

### Phase 8: Server Assembly
**Goal**: Runnable MCP server

| Step | File | What | Why |
|------|------|------|-----|
| 8.1 | `src/crypto_mcp/server.py` | FastMCP setup, lifespan | Entry point |
| 8.2 | `src/crypto_mcp/__main__.py` | `python -m crypto_mcp` | CLI entry |
| 8.3 | `tests/integration/test_server.py` | End-to-end tests | Verify MCP protocol |
| 8.4 | `.env.example` | Example env vars | User documentation |

**Checkpoint**: `python -m crypto_mcp` starts server, Claude can use it

---

## Key Decisions Summary

| Decision | Choice | Reasoning |
|----------|--------|-----------|
| Architecture | Hybrid (exchanges + tools) | Separates API from MCP, easy to add exchanges |
| Testing | Alongside code | Catch errors early, no test debt |
| API auth | Optional API key | Works without, faster with key |
| Transport | stdio first | Standard for MCP, HTTP/SSE later for product |
| HTTP lib | httpx | Async-native, clean API, connection pooling |
| Validation | Pydantic | Industry standard, auto JSON schema |
| Build order | Foundation -> Models -> Exchange -> Tools -> Server | Each layer builds on previous |

---

## CLAUDE.md Update (To Be Added)

```markdown
# Additional Rules

- Build process should be as granular as possible, implementing one component at a time
- Each component should be testable independently before moving to the next
- Run tests after each implementation step to catch errors early
```

---

## Step-by-Step Progress Tracker

Use this section to track where we are. Mark steps as done with [x].

### Phase 0: Setup
- [x] 0.1 Update CLAUDE.md with granular building rule

### Phase 1: Project Foundation
- [x] 1.1 Create `pyproject.toml`
- [x] 1.2 Create `src/crypto_mcp/__init__.py`
- [x] 1.3 Create `src/crypto_mcp/config.py`
- [x] 1.4 Create `tests/conftest.py`
- [x] 1.5 Create `tests/unit/test_config.py`
- [x] 1.6 **CHECKPOINT**: Run `pip install -e .` and `pytest` (3/3 passed)

### Phase 2: Exception Hierarchy
- [x] 2.1 Create `src/crypto_mcp/exceptions/base.py`
- [x] 2.2 Create `src/crypto_mcp/exceptions/__init__.py`
- [x] 2.3 **CHECKPOINT**: Test exception imports (passed)

### Phase 3: Shared Models
- [x] 3.1 Create `src/crypto_mcp/models/common.py`
- [x] 3.2 Create `src/crypto_mcp/models/responses.py`
- [x] 3.3 Create `src/crypto_mcp/models/__init__.py`
- [x] 3.4 **CHECKPOINT**: Test model creation/serialization (passed)

### Phase 4: Exchange Abstraction
- [x] 4.1 Create `src/crypto_mcp/exchanges/base.py`
- [x] 4.2 Create `src/crypto_mcp/exchanges/__init__.py`
- [x] 4.3 **CHECKPOINT**: Abstract interface importable (7 methods)

### Phase 5: Binance Client
- [ ] 5.1 Create `src/crypto_mcp/exchanges/binance/endpoints.py`
- [ ] 5.2 Create `src/crypto_mcp/exchanges/binance/exceptions.py`
- [ ] 5.3 Create `src/crypto_mcp/exchanges/binance/models.py`
- [ ] 5.4 Create `src/crypto_mcp/exchanges/binance/client.py`
- [ ] 5.5 Create `src/crypto_mcp/exchanges/binance/__init__.py`
- [ ] 5.6 Create `tests/unit/exchanges/binance/test_models.py`
- [ ] 5.7 Create `tests/unit/exchanges/binance/test_client.py`
- [ ] 5.8 **CHECKPOINT**: Run pytest, all Binance tests pass

### Phase 6: Utilities
- [ ] 6.1 Create `src/crypto_mcp/utils/http.py`
- [ ] 6.2 Create `src/crypto_mcp/utils/__init__.py`
- [ ] 6.3 Create `src/crypto_mcp/exceptions/handlers.py`
- [ ] 6.4 **CHECKPOINT**: Utils importable, error conversion works

### Phase 7: MCP Tools
- [ ] 7.1 Create `src/crypto_mcp/tools/open_interest.py`
- [ ] 7.2 Create `tests/unit/tools/test_open_interest.py`
- [ ] 7.3 Create `src/crypto_mcp/tools/mark_price.py`
- [ ] 7.4 Create `tests/unit/tools/test_mark_price.py`
- [ ] 7.5 Create `src/crypto_mcp/tools/ticker.py`
- [ ] 7.6 Create `tests/unit/tools/test_ticker.py`
- [ ] 7.7 Create `src/crypto_mcp/tools/klines.py`
- [ ] 7.8 Create `tests/unit/tools/test_klines.py`
- [ ] 7.9 Create `src/crypto_mcp/tools/funding_rate.py`
- [ ] 7.10 Create `tests/unit/tools/test_funding_rate.py`
- [ ] 7.11 Create `src/crypto_mcp/tools/open_interest_history.py`
- [ ] 7.12 Create `tests/unit/tools/test_open_interest_history.py`
- [ ] 7.13 Create `src/crypto_mcp/tools/long_short_ratio.py`
- [ ] 7.14 Create `tests/unit/tools/test_long_short_ratio.py`
- [ ] 7.15 Create `src/crypto_mcp/tools/__init__.py`
- [ ] 7.16 **CHECKPOINT**: All tool tests pass

### Phase 8: Server Assembly
- [ ] 8.1 Create `src/crypto_mcp/server.py`
- [ ] 8.2 Create `src/crypto_mcp/__main__.py`
- [ ] 8.3 Create `tests/integration/test_server.py`
- [ ] 8.4 Create `.env.example`
- [ ] 8.5 **CHECKPOINT**: `python -m crypto_mcp` runs, integration tests pass

---

## Workflow

For each step:
1. I explain what we're about to create and why
2. You approve (or ask questions)
3. I create the file
4. I show you the result
5. We run tests if applicable
6. Move to next step
