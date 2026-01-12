"""Common types and validators used across the project."""

from crypto_mcp.exceptions import ValidationError


class ValidInterval:
    """Validator for kline/candlestick intervals."""

    ALLOWED = {
        "1m", "3m", "5m", "15m", "30m",
        "1h", "2h", "4h", "6h", "8h", "12h",
        "1d", "3d", "1w", "1M",
    }

    # Bybit format -> Binance format (auto-convert)
    BYBIT_TO_BINANCE = {
        "1": "1m", "3": "3m", "5": "5m", "15": "15m", "30": "30m",
        "60": "1h", "120": "2h", "240": "4h", "360": "6h", "480": "8h", "720": "12h",
        "D": "1d", "W": "1w", "M": "1M",
    }

    @classmethod
    def validate(cls, interval: str) -> str:
        """Validate and return the interval, or raise ValidationError.

        Accepts both Binance format (1h, 1d) and Bybit format (60, D).
        Returns normalized Binance format.
        """
        # auto-convert Bybit format to Binance format
        if interval in cls.BYBIT_TO_BINANCE:
            return cls.BYBIT_TO_BINANCE[interval]

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
