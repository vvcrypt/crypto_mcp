"""Binance-specific exception classes."""

from crypto_mcp.exceptions import ExchangeError, RateLimitError, SymbolNotFoundError


class BinanceAPIError(ExchangeError):
    """Error from Binance API response."""

    def __init__(self, message: str, code: int | None = None):
        super().__init__(exchange="binance", message=message, code=code)


class BinanceRateLimitError(RateLimitError):
    """Binance rate limit exceeded (code -1003)."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(exchange="binance", message=message, code=-1003)


class BinanceSymbolNotFoundError(SymbolNotFoundError):
    """Invalid symbol on Binance (code -1121)."""

    def __init__(self, symbol: str):
        super().__init__(
            exchange="binance",
            message=f"Invalid symbol: {symbol}",
            code=-1121,
        )


# common Binance error codes for reference
BINANCE_ERROR_CODES = {
    -1000: "Unknown error",
    -1001: "Disconnected from server",
    -1002: "Unauthorized",
    -1003: "Rate limit exceeded",
    -1006: "Unexpected response",
    -1007: "Timeout",
    -1014: "Unknown order composition",
    -1015: "Too many orders",
    -1016: "Service shutting down",
    -1020: "Unsupported operation",
    -1021: "Timestamp outside recv window",
    -1022: "Invalid signature",
    -1100: "Illegal characters in parameter",
    -1101: "Too many parameters",
    -1102: "Mandatory parameter missing",
    -1103: "Unknown parameter",
    -1104: "Unread parameters",
    -1105: "Parameter empty",
    -1106: "Parameter not required",
    -1111: "Bad precision",
    -1112: "No open orders",
    -1116: "Invalid order type",
    -1117: "Invalid side",
    -1121: "Invalid symbol",
    -1125: "Invalid listen key",
    -1127: "Interval too large",
    -1128: "Combination of parameters invalid",
    -1130: "Invalid data sent",
    -4003: "Quantity too small",
    -4055: "Exceeds max adjustable leverage",
}


def raise_for_binance_error(code: int, message: str) -> None:
    """Raise appropriate exception based on Binance error code."""
    if code == -1003 or code == -1015:
        raise BinanceRateLimitError(message)
    elif code == -1121:
        # extract symbol from message if possible
        raise BinanceAPIError(message, code=code)
    else:
        raise BinanceAPIError(message, code=code)
