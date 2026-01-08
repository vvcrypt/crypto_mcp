# Problem 001: Langsame sequentielle Tool-Aufrufe

**Datum:** 2026-01-08
**Status:** Geloest
**Betroffene Tools:** `get_open_interest_history` (und potenziell alle anderen)

---

## Symptom

Bei Abfragen fuer mehrere Symbole (z.B. "Zeig mir das Open Interest fuer die neuesten Coins") dauerte die Antwort sehr lange (>1 Minute fuer ~15 Symbole).

## Analyse

### Log-Analyse

```
07:23:03.431Z - Request GUAUSDT
07:23:03.690Z - Response (259ms)    <-- HTTP Request schnell
07:23:08.787Z - Request LABUSDT     <-- 5 Sekunden Pause!
07:23:09.079Z - Response (292ms)
07:23:13.822Z - Request YALAUSDT    <-- wieder 5 Sekunden Pause
...
```

### Ursache

Das Problem lag **nicht** am MCP-Server oder der Binance API:
- HTTP-Requests: ~200-300ms (schnell)
- Verzoegerung: ~5 Sekunden zwischen jedem Request

**Root Cause:** Claude Desktop macht sequentielle Tool-Aufrufe. Zwischen jedem Aufruf:
1. Claude empfaengt Response
2. Claude "denkt" ueber das Ergebnis nach
3. Claude entscheidet den naechsten Aufruf zu machen
4. Naechster Request wird gesendet

Diese "Denkzeit" (~5s) multipliziert mit der Anzahl der Symbole fuehrt zu langen Wartezeiten.

```
Gesamtzeit = (HTTP_Zeit + Claude_Denkzeit) * Anzahl_Symbole
           = (0.3s + 5s) * 15
           = ~80 Sekunden
```

## Loesung

### Batch-Tool implementiert

Neues Tool `get_open_interest_history_batch` hinzugefuegt:

```python
@mcp.tool()
async def get_open_interest_history_batch(
    symbols: list[str],  # ["BTCUSDT", "ETHUSDT", ...]
    period: str,
    limit: int = 30,
    ...
) -> dict[str, list[dict]]:
    """Get historical open interest for MULTIPLE symbols in parallel."""

    async def fetch_one(sym: str):
        result = await client.get_open_interest_history(...)
        return sym, [r.model_dump() for r in result]

    # Alle Requests parallel ausfuehren
    results = await asyncio.gather(*[fetch_one(s) for s in symbols])
    return dict(results)
```

### Vorher vs. Nachher

| Szenario | Vorher | Nachher |
|----------|--------|---------|
| 15 Symbole abfragen | ~80s (15 Tool-Aufrufe) | ~5s (1 Tool-Aufruf) |
| Anzahl HTTP-Requests | 15 (sequentiell) | 15 (parallel) |
| Claude "Denkzeit" | 15x | 1x |

### Aenderungen

**Datei:** `src/crypto_mcp/tools/open_interest_history.py`
- `get_open_interest_history_batch` Tool hinzugefuegt
- Nutzt `asyncio.gather` fuer parallele Requests

**Datei:** `tests/integration/test_server.py`
- Tool-Count von 7 auf 8 aktualisiert
- Neues Tool in EXPECTED_TOOLS Liste

---

## Lessons Learned

1. **MCP Tool-Design:** Bei Daten die oft in Batches abgefragt werden, immer ein Batch-Tool anbieten
2. **Bottleneck-Analyse:** Der Bottleneck war nicht der Server, sondern die Client-Seite (Claude's Denkzeit)
3. **Log-Analyse:** Timestamps in Logs sind entscheidend um Latenz-Quellen zu identifizieren

## Potenzielle weitere Optimierungen

Falls aehnliche Probleme bei anderen Tools auftreten:
- `get_funding_rate_batch` fuer mehrere Symbole
- `get_klines_batch` fuer mehrere Symbole
- `get_mark_price` unterstuetzt bereits alle Symbole ohne Parameter
