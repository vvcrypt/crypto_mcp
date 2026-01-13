"""MCP tool for derived metrics calculations."""

from decimal import Decimal

from mcp.server.fastmcp import FastMCP

from crypto_mcp.exchanges.base import BaseExchangeClient
from crypto_mcp.tools._utils import get_client


def register_derived_metrics_tools(
    mcp: FastMCP,
    clients: dict[str, BaseExchangeClient],
) -> None:
    """Register derived metrics tools with the MCP server."""

    @mcp.tool()
    async def get_derived_metrics(
        symbol: str,
        metrics: list[str],
        vwap_period: str = "1h",
        exchange: str = "binance",
    ) -> dict:
        """Calculate derived metrics from market data.

        Computes analytical metrics like VWAP, funding trends, and divergence
        signals from raw market data.

        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT)
            metrics: List of metrics to calculate. Options:
                     - "vwap": Volume Weighted Average Price
                     - "funding_trend": Funding rate direction and strength
                     - "oi_change_rate": Open interest % change
                     - "price_oi_divergence": Price vs OI divergence detection
            vwap_period: Interval for VWAP calculation (default: 1h)
            exchange: Exchange to query ("binance" or "bybit", default: binance)

        Returns:
            Dict containing only the requested metrics
        """
        client = get_client(clients, exchange)
        normalized_symbol = symbol.upper()
        result = {}

        if "vwap" in metrics:
            result["vwap"] = await _calculate_vwap(
                client, normalized_symbol, vwap_period
            )

        if "funding_trend" in metrics:
            result["funding_trend"] = await _calculate_funding_trend(
                client, normalized_symbol
            )

        if "oi_change_rate" in metrics:
            result["oi_change_rate"] = await _calculate_oi_change_rate(
                client, normalized_symbol
            )

        if "price_oi_divergence" in metrics:
            result["price_oi_divergence"] = await _calculate_price_oi_divergence(
                client, normalized_symbol
            )

        return result


async def _calculate_vwap(
    client: BaseExchangeClient,
    symbol: str,
    interval: str,
) -> Decimal:
    """Calculate Volume Weighted Average Price.

    VWAP = sum(price * volume) / sum(volume)
    Using quote_volume as price*volume proxy from klines.
    """
    klines = await client.get_klines(symbol=symbol, interval=interval, limit=24)

    total_quote_volume = Decimal("0")
    total_volume = Decimal("0")

    for candle in klines.candles:
        total_quote_volume += candle.quote_volume
        total_volume += candle.volume

    if total_volume == 0:
        return Decimal("0")

    vwap = total_quote_volume / total_volume
    return vwap.quantize(Decimal("0.01"))


async def _calculate_funding_trend(
    client: BaseExchangeClient,
    symbol: str,
) -> dict:
    """Analyze funding rate trend.

    Returns direction (bullish/bearish/neutral) and strength.
    """
    funding_rates = await client.get_funding_rate(symbol=symbol, limit=10)

    if len(funding_rates) < 2:
        return {"direction": "neutral", "strength": Decimal("0")}

    # sort by funding_time to ensure chronological order
    sorted_rates = sorted(funding_rates, key=lambda x: x.funding_time)
    rates = [fr.funding_rate for fr in sorted_rates]

    # calculate average change between consecutive rates
    changes = []
    for i in range(1, len(rates)):
        change = rates[i] - rates[i - 1]
        changes.append(change)

    if not changes:
        return {"direction": "neutral", "strength": Decimal("0")}

    avg_change = sum(changes) / len(changes)

    # determine direction
    threshold = Decimal("0.00001")  # 0.001%
    if avg_change > threshold:
        direction = "bullish"
    elif avg_change < -threshold:
        direction = "bearish"
    else:
        direction = "neutral"

    # calculate strength as absolute change magnitude normalized
    # higher funding rate changes = stronger trend
    strength = abs(avg_change) * 10000  # scale to reasonable range
    strength = min(strength, Decimal("1.0"))  # cap at 1.0

    return {
        "direction": direction,
        "strength": strength.quantize(Decimal("0.01")),
    }


async def _calculate_oi_change_rate(
    client: BaseExchangeClient,
    symbol: str,
) -> Decimal:
    """Calculate open interest percentage change.

    Returns % change between oldest and newest OI values.
    """
    oi_history = await client.get_open_interest_history(
        symbol=symbol, period="1h", limit=24
    )

    if len(oi_history) < 2:
        return Decimal("0")

    # sort by timestamp to ensure chronological order
    sorted_oi = sorted(oi_history, key=lambda x: x.timestamp)
    oldest_oi = sorted_oi[0].open_interest
    newest_oi = sorted_oi[-1].open_interest

    if oldest_oi == 0:
        return Decimal("0")

    change_rate = ((newest_oi - oldest_oi) / oldest_oi) * 100
    return change_rate.quantize(Decimal("0.1"))


async def _calculate_price_oi_divergence(
    client: BaseExchangeClient,
    symbol: str,
) -> dict:
    """Detect price-OI divergence.

    Bearish divergence: price up, OI down (weak rally, shorts closing)
    Bullish divergence: price down, OI up (accumulation during dip)
    """
    # get price data
    klines = await client.get_klines(symbol=symbol, interval="1h", limit=24)

    # get OI data
    oi_history = await client.get_open_interest_history(
        symbol=symbol, period="1h", limit=24
    )

    if len(klines.candles) < 2 or len(oi_history) < 2:
        return {"detected": False, "type": None}

    # calculate price change (oldest to newest)
    # sort klines by open_time to ensure chronological order
    sorted_candles = sorted(klines.candles, key=lambda x: x.open_time)
    oldest_price = sorted_candles[0].close
    newest_price = sorted_candles[-1].close
    price_change_pct = ((newest_price - oldest_price) / oldest_price) * 100

    # calculate OI change
    # sort by timestamp to ensure chronological order
    sorted_oi = sorted(oi_history, key=lambda x: x.timestamp)
    oldest_oi = sorted_oi[0].open_interest
    newest_oi = sorted_oi[-1].open_interest
    oi_change_pct = ((newest_oi - oldest_oi) / oldest_oi) * 100

    # detect divergence
    threshold = Decimal("1.0")  # 1% threshold for significance

    price_up = price_change_pct > threshold
    price_down = price_change_pct < -threshold
    oi_up = oi_change_pct > threshold
    oi_down = oi_change_pct < -threshold

    if price_up and oi_down:
        return {"detected": True, "type": "bearish"}
    elif price_down and oi_up:
        return {"detected": True, "type": "bullish"}
    else:
        return {"detected": False, "type": None}
