"""Bybit-specific exception classes."""

from crypto_mcp.exceptions import ExchangeError, RateLimitError, SymbolNotFoundError


class BybitAPIError(ExchangeError):
    """Error from Bybit API response."""

    def __init__(self, message: str, code: int | None = None):
        super().__init__(exchange="bybit", message=message, code=code)


class BybitRateLimitError(RateLimitError):
    """Bybit rate limit exceeded (code 10006)."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(exchange="bybit", message=message, code=10006)


class BybitSymbolNotFoundError(SymbolNotFoundError):
    """Invalid symbol on Bybit (code 10001)."""

    def __init__(self, symbol: str):
        super().__init__(
            exchange="bybit",
            message=f"Invalid symbol: {symbol}",
            code=10001,
        )


# common Bybit V5 error codes for reference
# see: https://bybit-exchange.github.io/docs/v5/error
BYBIT_ERROR_CODES = {
    0: "Success",
    10001: "Invalid request - parameter error",
    10002: "Invalid request - unable to process",
    10003: "API key invalid",
    10004: "Sign error",
    10005: "Permission denied",
    10006: "Rate limit exceeded",
    10007: "IP not in whitelist",
    10008: "Unmatched IP",
    10009: "API key expired",
    10010: "Timestamp error",
    10016: "Server error",
    10017: "Route not found",
    10018: "Request body exceeded limit",
    10027: "Trading banned",
    110001: "Invalid symbol",
    110003: "Order not exist",
    110004: "Insufficient wallet balance",
    110007: "Position not exist",
    110012: "Insufficient available balance",
    110017: "Reduce-only rule not satisfied",
    110025: "Trading suspended",
}


def raise_for_bybit_error(code: int, message: str) -> None:
    """Raise appropriate exception based on Bybit error code."""
    if code == 10006:
        raise BybitRateLimitError(message)
    elif code in (10001, 110001):
        raise BybitAPIError(message, code=code)
    else:
        raise BybitAPIError(message, code=code)
