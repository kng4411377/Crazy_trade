# Strategy & Risk Enhancements Roadmap

Comprehensive plan to evolve the Crazy Trade Bot from a simple momentum system into a professional-grade autonomous trading framework.

**Source:** ChatGPT Strategy Analysis  
**Status:** Roadmap for phased implementation  

---

## 🎯 Vision

Transform the bot into a **self-regulating, volatility-aware, fully auditable** trading system with:
- Multi-layer risk management
- Dynamic position sizing
- Advanced entry filters
- Comprehensive monitoring

---

## 📋 Enhancement Categories

### 1️⃣ Entry Logic Enhancements

#### 1.1 Breakout Confirmation Layer
**Status:** 📋 Planned  
**Priority:** High  
**Complexity:** Medium

**Description:**
- Require price to close above buy-stop trigger on higher timeframe (15-min or 1-hour)
- Filters out false breakouts from intrabar spikes
- Validates momentum before entry

**Implementation:**
- Add validation module before `place_entry_order()`
- Fetch higher timeframe candle data from Alpaca
- Check close price vs trigger level

**Benefits:**
- ✅ Reduces false breakout entries
- ✅ Improves win rate
- ✅ Better capital efficiency

**Code Impact:**
- `src/state_machine.py` - Add breakout validator
- `src/alpaca_client.py` - Add historical bar fetching
- New module: `src/indicators.py`

---

#### 1.2 Volume or Volatility Filter
**Status:** ⚠️ Partially Implemented (needs enhancement)  
**Priority:** High  
**Complexity:** Low-Medium

**Description:**
- Only activate entries when:
  - Volume > average volume (20-day)
  - ATR > baseline threshold
- Prevents trades during low-liquidity or flat sessions

**Implementation:**
- Use Alpaca's historical data API for rolling averages
- Calculate 20-day average volume and ATR
- Gate entry logic on these thresholds

**Benefits:**
- ✅ Avoids dead markets
- ✅ Better execution quality
- ✅ Reduces slippage

**Config Example:**
```yaml
filters:
  min_volume_multiplier: 1.5  # 1.5x average volume
  min_atr_percentile: 30      # 30th percentile of ATR
```

---

#### 1.3 Dynamic Entry Scaling (ATR-Based)
**Status:** 📋 Planned  
**Priority:** Medium  
**Complexity:** Medium-High

**Description:**
- Scale buy-stop trigger based on recent volatility
- Use ATR (Average True Range) or percentile of true range
- Keeps entry sensitivity consistent across symbols

**Current:** Fixed 5% above last price  
**Enhanced:** `trigger = last_price * (1 + ATR_multiplier * current_ATR / avg_ATR)`

**Benefits:**
- ✅ Adapts to market conditions
- ✅ Better entry timing
- ✅ Consistent across volatile vs stable stocks

**Code Impact:**
- New module: `src/indicators.py` (ATR calculation)
- `src/state_machine.py` - Dynamic trigger calculation
- `config.yaml` - ATR settings

---

#### 1.4 Multi-Signal Confluence
**Status:** 📋 Planned  
**Priority:** Low-Medium  
**Complexity:** High

**Description:**
- Combine multiple confirmation signals:
  - EMA crossover (e.g., 9 EMA > 21 EMA)
  - RSI direction (e.g., RSI > 50)
  - Momentum slope (price trend)
- Only allow entries when signals align

**Benefits:**
- ✅ Higher quality entries
- ✅ Better win rate
- ✅ Trend confirmation

**Dependencies:**
- Requires indicator library (TA-Lib or custom)
- Historical data fetching
- Signal computation framework

**Note:** This is complex and may reduce trade frequency significantly.

---

### 2️⃣ Exit & Risk Management Tools

#### 2.1 Fixed-Risk Stop (Hard Stop Layer)
**Status:** 📋 Planned  
**Priority:** High  
**Complexity:** Low

**Description:**
- Pair trailing stops with static initial stop
- Based on fixed % or ATR from entry
- Acts as fail-safe if trailing updates fail

**Implementation:**
```python
# Dual-layer protection
initial_stop = entry_price * (1 - fixed_stop_pct)  # e.g., -8%
trailing_stop = current_high * (1 - trailing_pct)  # e.g., -10%
effective_stop = max(initial_stop, trailing_stop)
```

**Benefits:**
- ✅ Guaranteed maximum loss per trade
- ✅ Fail-safe if trailing logic fails
- ✅ Better risk control

**Config:**
```yaml
stops:
  fixed_stop_pct: 8.0          # Hard stop at -8%
  trailing_stop_pct: 10.0       # Trailing at -10%
  use_dual_layer: true
```

---

#### 2.2 Time-Based Exit
**Status:** 📋 Planned  
**Priority:** Medium  
**Complexity:** Low

**Description:**
- Automatically close positions older than N trading days
- Frees capital from stagnant positions
- Configurable timeout period

**Implementation:**
- Track entry timestamp in database
- Check age in `_handle_position_open()`
- Force close if age > threshold

**Benefits:**
- ✅ Prevents capital lock-up
- ✅ Frees funds for new opportunities
- ✅ Automatic portfolio turnover

**Config:**
```yaml
exits:
  max_position_days: 10        # Close after 10 trading days
  max_position_hours: 240      # Or 240 hours (10 days)
```

---

#### 2.3 Take-Profit Bracket
**Status:** 📋 Planned  
**Priority:** Medium  
**Complexity:** Medium

**Description:**
- Tiered exit plan with partial closes
- E.g., close 50% at +2R, 50% at +3R
- Use Alpaca's bracket orders (limit + stop combo)

**Implementation:**
- Split position into multiple tranches
- Place limit orders at profit targets
- Adjust trailing stop for remaining position

**Benefits:**
- ✅ Locks in partial gains
- ✅ Reduces risk after profit
- ✅ Better risk-adjusted returns

**Example:**
```yaml
take_profit:
  enabled: true
  tiers:
    - percentage: 50
      profit_target: 2.0      # +2R (2x risk)
    - percentage: 50
      profit_target: 3.0      # +3R (3x risk)
```

---

#### 2.4 Daily Drawdown & Exposure Limit
**Status:** ✅ IMPLEMENTED (v1.2.0)  
**Priority:** Critical  
**Complexity:** Low

**Description:**
- Stop all new entries if daily loss > threshold
- Limit simultaneous open positions
- Global session-level control

**Implementation:**
- Track daily P&L from performance module
- Check before each entry
- Halt trading if threshold breached

**Config:**
```yaml
risk:
  max_daily_loss_pct: 3.0      # Stop trading if -3% daily loss
  max_daily_loss_usd: 500      # Or -$500
  max_concurrent_positions: 5   # Max 5 positions at once
```

**Benefits:**
- ✅ Prevents cascading losses
- ✅ Circuit breaker for bad days
- ✅ Capital preservation

---

#### 2.5 Discrete Trailing Step
**Status:** 📋 Planned  
**Priority:** Low  
**Complexity:** Low

**Description:**
- Move trailing stops in fixed increments (e.g., +1% per adjustment)
- Reduces API load and micro-adjustment noise
- Only update when meaningful price movement occurs

**Current:** Continuous trailing  
**Enhanced:** Update only on +1% gain increments

**Benefits:**
- ✅ Fewer API calls
- ✅ Reduced noise
- ✅ More stable execution

---

### 3️⃣ Portfolio & Session Controls

#### 3.1 Symbol Correlation Guard
**Status:** 📋 Planned  
**Priority:** Medium  
**Complexity:** High

**Description:**
- Prevent simultaneous entries in correlated assets
- E.g., don't trade NVDA and AMD at same time
- Calculate correlation matrix weekly or use static groups

**Implementation:**
- Define correlation groups in config
- Check existing positions before new entry
- Skip entry if correlated position exists

**Config:**
```yaml
correlation_groups:
  - ["NVDA", "AMD", "INTC"]     # Semiconductors
  - ["AAPL", "MSFT", "GOOGL"]   # Big tech
  - ["JPM", "BAC", "WFC"]       # Banks
```

**Benefits:**
- ✅ Diversifies exposure
- ✅ Reduces sector concentration risk
- ✅ Better portfolio balance

---

#### 3.2 Session Scheduler
**Status:** ✅ IMPLEMENTED (v1.2.0)  
**Priority:** High  
**Complexity:** Low

**Description:**
- Avoid trading during unstable windows:
  - Skip first 5 minutes after open
  - Skip last 10 minutes before close
- Use market calendar for precise time gating

**Implementation:**
- Add time checks to market hours module
- Gate entry/exit logic based on session time
- Configurable buffer periods

**Config:**
```yaml
hours:
  skip_first_minutes: 5         # Skip first 5 min after open
  skip_last_minutes: 10         # Skip last 10 min before close
```

**Benefits:**
- ✅ Avoids open/close volatility
- ✅ Better execution quality
- ✅ Reduces slippage

---

#### 3.3 Adaptive Allocation
**Status:** 📋 Planned  
**Priority:** Low  
**Complexity:** High

**Description:**
- Dynamically adjust `per_symbol_usd` based on performance
- Increase exposure after winning streaks
- Decrease after drawdowns
- Kelly Criterion or fixed-fractional approach

**Implementation:**
- Track rolling win rate and profit factor
- Calculate optimal position size
- Adjust allocation within min/max bounds

**Example:**
```python
base_allocation = 1000
win_rate = 0.65
profit_factor = 2.0
kelly_fraction = (win_rate * profit_factor - (1 - win_rate)) / profit_factor
adjusted_allocation = base_allocation * kelly_fraction * 0.5  # Half-Kelly
```

**Benefits:**
- ✅ Optimizes capital efficiency
- ✅ Scales winners, reduces losers
- ✅ Better risk-adjusted returns

**Risks:**
- ⚠️ Can be aggressive
- ⚠️ Requires significant data
- ⚠️ May amplify drawdowns if not careful

---

### 4️⃣ Monitoring & Automation Enhancements

#### 4.1 Profit-Factor Dashboard
**Status:** ⚠️ Partially Implemented (basic metrics exist)  
**Priority:** Medium  
**Complexity:** Medium

**Description:**
- Add `/metrics` endpoint with detailed stats:
  - Win rate, profit factor, avg R:R
  - Max drawdown, Sharpe ratio
  - Trailing stop latency, failure counts
- Integrate with Grafana or Prometheus

**Metrics to Track:**
- Win rate (%)
- Profit factor (gross profit / gross loss)
- Average R:R (reward-to-risk ratio)
- Max drawdown (%)
- Sharpe ratio
- Average trade duration
- Stop failure count
- API latency (p50, p95, p99)

**Implementation:**
- Enhance `api_server.py` with `/metrics` endpoint
- Calculate metrics from database
- Export in Prometheus format

**Benefits:**
- ✅ Transparent performance tracking
- ✅ Real-time monitoring
- ✅ Data-driven optimization

---

#### 4.2 Alert Webhooks
**Status:** 📋 Planned  
**Priority:** Medium  
**Complexity:** Low-Medium

**Description:**
- Push notifications to Slack or Telegram for key events:
  - Stop triggered
  - Daily loss limit reached
  - New profit high watermark
  - Critical system errors

**Implementation:**
- Add webhook configuration
- Send alerts on significant events
- Rate-limit to avoid spam

**Config:**
```yaml
alerts:
  webhook: "https://hooks.slack.com/services/..."
  events:
    - stop_triggered
    - daily_loss_limit
    - profit_high_watermark
    - critical_error
```

**Benefits:**
- ✅ Real-time situational awareness
- ✅ Immediate action on issues
- ✅ Better monitoring for remote deployment

---

#### 4.3 Shadow Mode (Dry Run)
**Status:** 📋 Planned  
**Priority:** Low  
**Complexity:** High

**Description:**
- Simulate trades in parallel with real execution
- Record would-be fills and exits
- Validate strategy modifications safely

**Implementation:**
- Duplicate state machine in shadow mode
- Process same events, don't submit orders
- Record hypothetical outcomes
- Compare shadow vs real performance

**Benefits:**
- ✅ Safe backtesting of new logic
- ✅ A/B testing strategies
- ✅ Risk-free validation

**Note:** This is complex infrastructure work - significant effort required.

---

## 🗓️ Implementation Roadmap

### Phase 1: Core Safety (Sprint 1-2 weeks) ✅ DONE
**Goal:** Add critical safety features

- ✅ Daily drawdown guard (circuit breaker)
- ✅ Session scheduler (avoid open/close volatility)
- ✅ Enhanced metrics logging

**Status:** Completed in v1.2.0

---

### Phase 2: Smart Entries (Sprint 2-3 weeks)
**Goal:** Improve entry quality

- [ ] Volume filter (require 1.5x average volume)
- [ ] ATR-based entry scaling
- [ ] Breakout confirmation layer

**Dependencies:**
- Indicators module (ATR, volume averages)
- Historical data fetching
- Entry validation framework

---

### Phase 3: Advanced Risk Management (Sprint 2-3 weeks)
**Goal:** Multi-layer protection

- [ ] Fixed-risk stop (dual-layer protection)
- [ ] Time-based exit (stale position closer)
- [ ] Take-profit brackets (partial exits)

**Dependencies:**
- Phase 2 indicators
- Enhanced order management

---

### Phase 4: Portfolio Logic (Sprint 3-4 weeks)
**Goal:** Portfolio-level intelligence

- [ ] Correlation guard
- [ ] Adaptive allocation (Kelly-based sizing)
- [ ] Enhanced exposure management

**Dependencies:**
- Phase 3 complete
- Correlation calculation framework
- Performance analytics

---

### Phase 5: Monitoring & Ops (Sprint 1-2 weeks)
**Goal:** Professional observability

- [ ] Profit-factor dashboard (detailed metrics)
- [ ] Alert webhooks (Slack/Telegram)
- [ ] Enhanced logging and analytics

**Dependencies:**
- Any phase can be done in parallel

---

### Phase 6: Advanced Features (Sprint 4-6 weeks)
**Goal:** Cutting-edge capabilities

- [ ] Shadow mode (parallel simulation)
- [ ] Multi-signal confluence (indicator combo)
- [ ] Discrete trailing steps

**Dependencies:**
- All previous phases complete
- Significant infrastructure work

---

## 📊 Priority Matrix

| Feature | Priority | Complexity | Impact | Status |
|---------|----------|------------|--------|--------|
| Daily drawdown limit | 🔴 Critical | Low | High | ✅ Done |
| Session scheduler | 🔴 Critical | Low | High | ✅ Done |
| Volume filter | 🟡 High | Medium | High | 📋 Planned |
| Fixed-risk stop | 🟡 High | Low | High | 📋 Planned |
| Breakout confirmation | 🟡 High | Medium | High | 📋 Planned |
| ATR-based scaling | 🟠 Medium | Medium | Medium | 📋 Planned |
| Time-based exit | 🟠 Medium | Low | Medium | 📋 Planned |
| Take-profit brackets | 🟠 Medium | Medium | Medium | 📋 Planned |
| Correlation guard | 🟠 Medium | High | Medium | 📋 Planned |
| Profit dashboard | 🟠 Medium | Medium | Medium | 📋 Planned |
| Alert webhooks | 🟠 Medium | Low | Medium | 📋 Planned |
| Adaptive allocation | 🟢 Low | High | Low-Med | 📋 Planned |
| Multi-signal | 🟢 Low | High | High | 📋 Planned |
| Shadow mode | 🟢 Low | High | Low | 📋 Planned |
| Discrete trailing | 🟢 Low | Low | Low | 📋 Planned |

---

## 🎯 Quick Wins (Implement First)

These are safe, high-value features that can be implemented quickly:

1. ✅ **Daily drawdown limit** - Circuit breaker (DONE)
2. ✅ **Session time filters** - Skip open/close volatility (DONE)
3. **Volume filter** - Require minimum volume before entry
4. **Fixed-risk stop** - Dual-layer protection
5. **Alert webhooks** - Real-time notifications

---

## ⚠️ Caution Areas

Features that require careful implementation:

- **Adaptive allocation** - Can amplify losses if not careful
- **Multi-signal confluence** - May reduce trade frequency dramatically
- **Shadow mode** - Complex infrastructure, significant effort
- **ATR-based scaling** - Requires thorough backtesting

---

## 🧪 Testing Strategy

For each enhancement:

1. **Unit tests** - Test individual components
2. **Integration tests** - Test with other modules
3. **Paper trading** - Run in paper mode for 1-2 weeks
4. **Small capital** - Start with minimal allocation
5. **Monitor closely** - Watch first week carefully
6. **Scale gradually** - Increase allocation if successful

---

## 📈 Success Metrics

Track these to measure enhancement impact:

- **Win rate** - Should improve with better entries
- **Profit factor** - Gross profit / gross loss ratio
- **Max drawdown** - Should decrease with better risk management
- **Sharpe ratio** - Risk-adjusted returns
- **Trade frequency** - Some features may reduce it
- **Capital efficiency** - Return per dollar allocated

---

## 🤝 Contributing

When implementing enhancements:

1. Create feature branch
2. Implement with tests
3. Run in paper mode
4. Document in CHANGELOG
5. Update this roadmap
6. Submit PR with results

---

## 📝 Notes

- **Don't implement everything at once** - Phased approach is safer
- **Test thoroughly** - Each enhancement changes bot behavior
- **Monitor impact** - Track metrics before and after
- **Keep it simple** - Complexity adds bugs and maintenance burden
- **Document everything** - Future you will thank you

---

## 🔗 References

- **ChatGPT Strategy Analysis** - Source of these ideas
- **CHANGELOG.md** - Track implemented enhancements
- **README.md** - Main project documentation

---

**Status:** Living document - update as features are implemented

**Last Updated:** November 21, 2024

**Next Review:** After Phase 1 completion

