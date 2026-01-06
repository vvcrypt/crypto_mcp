"""Common types and validators used across the project."""

from crypto_mcp.exceptions import ValidationError


class ValidInterval:
    """Validator for kline/candlestick intervals."""

    ALLOWED = {
        "1m", "3m", "5m", "15m", "30m",
        "1h", "2h", "4h", "6h", "8h", "12h",
        "1d", "3d", "1w", "1M",
    }

    @classmethod
    def validate(cls, interval: str) -> str:
        """Validate and return the interval, or raise ValidationError."""
        if interval not in cls.ALLOWED:
            allowed = ", ".join(sorted(cls.ALLOWED))
            raise ValidationError(f"Invalid interval '{interval}'. Allowed: {allowed}")
        return interval


class ValidPeriod:
    """Validator for historical data periods (OI history, L/S ratio)."""

    ALLOWED = {"5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d"}

    @classmethod
    def validate(cls, period: str) -> str:
        """Validate and return the period, or raise ValidationError."""
        if period not in cls.ALLOWED:
            allowed = ", ".join(sorted(cls.ALLOWED))
            raise ValidationError(f"Invalid period '{period}'. Allowed: {allowed}")
        return period
