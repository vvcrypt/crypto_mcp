"""Base exception classes for crypto MCP server."""

from mcp.server.fastmcp.exceptions import ToolError


class CryptoMCPError(ToolError):
    """Base exception for all crypto MCP errors."""
    pass


class ExchangeError(CryptoMCPError):
    """Error from an exchange API."""

    def __init__(self, exchange: str, message: str, code: int | None = None):
        self.exchange = exchange
        self.code = code
        error_msg = f"[{exchange}] {message}"
        if code is not None:
            error_msg += f" (code: {code})"
        super().__init__(error_msg)


class ValidationError(CryptoMCPError):
    """Invalid input parameters."""
    pass


class RateLimitError(ExchangeError):
    """Rate limit exceeded on exchange."""
    pass


class SymbolNotFoundError(ExchangeError):
    """Trading symbol does not exist on exchange."""
    pass
