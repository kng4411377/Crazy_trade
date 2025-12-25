# Momentum Layer Tests

Test suite for the Momentum Intelligence Layer providers and factors.

## Test Files

### `test_apewisdom.py`
Tests the Apewisdom provider and Reddit Attention factor.
```bash
python tests/momentum/test_apewisdom.py
```

**Tests:**
- Apewisdom provider initialization
- Fetching Reddit mention data
- RedditAttentionFactor scoring
- Integration with YFinance

**Expected Output:**
- ✅ Provider health checks
- Reddit mention counts and sentiment
- Factor scores for trending stocks

---

### `test_momentum_providers.py`
Tests YFinance and (legacy) AlphaVantage providers.
```bash
python tests/momentum/test_momentum_providers.py
```

**Tests:**
- YFinance provider initialization
- Volume metrics calculation
- AlphaVantage provider (if API key provided)

---

### `test_combined_scoring.py`
Tests combined scoring from multiple factors.
```bash
python tests/momentum/test_combined_scoring.py
```

**Tests:**
- YFinance volume scoring
- Google Trends retail attention (legacy, may fail)
- Combined composite scores

**Note:** This test may show Google Trends rate limiting (429 errors). This is expected.

---

### `test_google_trends.py` & `debug_google_trends.py`
Legacy tests for Google Trends provider (not actively used).

**Status:** Google Trends has aggressive rate limiting and has been replaced by Apewisdom for Reddit sentiment.

---

## Running All Tests

```bash
# Run all momentum tests
cd /Users/tony.ng/work/temp/crazy_trade
python -m pytest tests/momentum/ -v

# Run specific test
python tests/momentum/test_apewisdom.py
```

---

## Test Requirements

### Required:
- `yfinance` - Free, no API key
- `aiohttp` - For async HTTP requests

### Optional:
- `ALPHAVANTAGE_API_KEY` - For AlphaVantage tests (rate-limited)
- `RAPIDAPI_KEY` - For StockTwits tests

Set these in `/Users/tony.ng/work/temp/crazy_trade/.env`

---

## Expected Behavior

### Successful Tests ✅
- **Apewisdom**: Should return mention data for trending Reddit stocks
- **YFinance**: Should return volume metrics for all symbols
- **Factor Scoring**: Should generate scores 0.0-1.0

### Expected Failures/Warnings ⚠️
- **Google Trends**: 429 rate limit errors (expected, use Apewisdom instead)
- **AlphaVantage**: 25 requests/day limit (expected, use YFinance instead)
- **No Reddit Data**: If no stocks are currently trending on Reddit

---

## Integration Tests

For end-to-end momentum scanning, use:
```bash
python scripts/scan_momentum.py --top 5
```

This is the primary way to test the full momentum system.

