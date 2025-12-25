# 🎯 Multi-Phase Momentum Strategy

## The Problem with Simple Averaging

**Question:** *"Would this miss Reddit mentions if volume hasn't picked up yet?"*

**Answer:** YES! Traditional weighted averaging misses early signals.

### Example:
```
Stock A: Reddit Score: 0.9, Volume Score: 0.2
  → Weighted Average (50/50): 0.55  ← RANKED LOW, MISSED!

Stock B: Reddit Score: 0.0, Volume Score: 0.8
  → Weighted Average (50/50): 0.40  ← Also ranked low

Stock C: Reddit Score: 0.5, Volume Score: 0.5
  → Weighted Average (50/50): 0.50  ← Ranked higher than A!
```

**Stock A has MASSIVE Reddit buzz** but no volume yet → **This is the BEST entry opportunity!**
But weighted average ranks it low because it needs BOTH factors to score high.

---

## ✅ Solution: Multi-Phase Analysis

### New Scanner Output Structure:

### 1. 🦍 **EARLY SIGNALS - Reddit Buzz (Pre-Volume)**
```
Rank  Symbol  Reddit   Mentions  WSB Rank  Volume   Status
--------------------------------------------------------------
1     GME     0.950    5,234     #2        0.300    ⚠️ NO VOLUME YET  ← GOLD!
2     AMC     0.850    3,122     #5        0.450    ⚠️ NO VOLUME YET
3     PLTR    0.920    4,891     #3        0.850    ✅ CONFIRMING     ← Volume picking up!
```

**Trading Strategy:**
- ⭐ **BEST for early entry** before the move
- Set alerts for volume to confirm
- Enter when volume starts spiking (RVOL > 1.5)
- These are your **pre-breakout plays**

---

### 2. 🔥 **VOLUME BREAKOUTS - Active Now**
```
Rank  Symbol  Volume   RVOL      Reddit   Status
-------------------------------------------------
1     ARM     1.000    1.88x     0.000    📊 Institutional
2     TSLA    0.950    1.75x     0.850    🦍 w/ Reddit  ← CONFIRMED PLAY
3     HTZ     1.000    2.18x     0.000    📊 Institutional
```

**Trading Strategy:**
- Volume is **confirming RIGHT NOW**
- Good for **scalps and momentum trades**
- 📊 Institutional = News/earnings driven
- 🦍 w/ Reddit = Retail-driven, check sentiment

---

### 3. 🏆 **CONFIRMED MOMENTUM - Reddit + Volume**
```
Rank  Symbol  Composite  Volume   Reddit   Signals
----------------------------------------------------
1     PLTR    0.930      0.920    0.940    🔥🦍💥
2     GME     0.880      0.950    0.810    🔥🦍
```

**Trading Strategy:**
- **BOTH factors strong** = powerful momentum
- May have **missed early entry**, but still tradeable
- Good for **continuation/breakout trades**
- High risk if you're late to the party

---

### 4. 📊 **TOP 10 OVERALL**
```
Rank  Symbol  Composite  Volume   Reddit   Signals
----------------------------------------------------
1     ARM     1.000      1.000    0.000    🔥
2     PLTR    0.930      0.920    0.940    🔥🦍💥
3     HTZ     1.000      1.000    0.000    🔥
```

**Trading Strategy:**
- **General watchlist** for multi-day plays
- Mix of all momentum types
- Use for diversified exposure

---

## 🎯 Aggregation Modes

### Mode 1: **MAX** (Recommended for Discovery)
```bash
python scripts/scan_momentum.py --mode max
```

**Logic:** `composite = max(volume_score, reddit_score)`

**Why it's better:**
- ✅ Catches stocks strong in **ANY factor**
- ✅ Won't miss early Reddit buzz
- ✅ Won't miss institutional volume plays
- ✅ **Best for finding opportunities**

**Example:**
```
Stock A: Reddit=0.9, Volume=0.2 → Composite=0.9  ← CAUGHT!
Stock B: Reddit=0.0, Volume=0.8 → Composite=0.8  ← Also caught!
```

---

### Mode 2: **WEIGHTED** (For Confirmed Plays Only)
```bash
python scripts/scan_momentum.py --mode weighted
```

**Logic:** `composite = 0.5*volume + 0.5*reddit`

**Use when:**
- You ONLY want stocks with **BOTH signals**
- You're conservative and want **confirmation**
- You're willing to miss early entries

**Example:**
```
Stock A: Reddit=0.9, Volume=0.2 → Composite=0.55  ← Missed
Stock B: Reddit=0.7, Volume=0.7 → Composite=0.70  ← Caught (both strong)
```

---

## 💡 Recommended Workflow

### Pre-Market (9:00 AM EST)
Run after Apewisdom's 9 AM update:
```bash
python scripts/scan_momentum.py --mode max --top 10
```

**Look at:**
1. 🦍 **EARLY SIGNALS** - Stocks with Reddit buzz
   - Add to watchlist
   - Set volume alerts (RVOL > 1.5)
2. 🔥 **VOLUME BREAKOUTS** - What's moving pre-market
   - Check news/catalysts
   - Prepare entry orders

---

### Intraday (Market Hours)
Run every 30-60 minutes:
```bash
python scripts/scan_momentum.py --mode max --top 10
```

**Monitor:**
- Did your 🦍 **EARLY SIGNALS** get volume? → ENTER!
- New 🔥 **VOLUME BREAKOUTS**? → Quick scalp opportunity
- 🏆 **CONFIRMED MOMENTUM**? → Continuation trades

---

### After-Hours (9:00 PM EST)
Run after Apewisdom's 9 PM update:
```bash
python scripts/scan_momentum.py --mode max --top 20
```

**Analyze:**
- What got Reddit buzz today?
- Which plays developed throughout the day?
- Plan tomorrow's watchlist

---

## 🚨 Key Insights

### ✅ What Makes This Strategy Powerful:

1. **Catches Early Signals**
   - Reddit buzz BEFORE volume = best entries
   - You're ahead of the crowd

2. **Multi-Phase Coverage**
   - Early → Mid → Late momentum phases
   - Don't miss opportunities at any stage

3. **Clear Action Items**
   - Each view has specific trading guidance
   - No confusion about what to do

4. **Flexible Aggregation**
   - MAX mode for discovery (catch everything)
   - WEIGHTED mode for confirmation (conservative)

---

### ⚠️ Common Mistakes to Avoid:

1. **Only using weighted average**
   - Misses early Reddit signals
   - Misses volume-only institutional plays

2. **Ignoring View 1 (Early Signals)**
   - This is your EDGE
   - By the time it's in View 3 (Confirmed), you're late

3. **Not setting alerts**
   - View 1 stocks need volume monitoring
   - Set alerts for RVOL > 1.5

4. **Chasing View 3 (Confirmed)**
   - These are late-stage plays
   - High risk of being a bag-holder

---

## 📊 Example Scenario

### 9:00 AM - Apewisdom Update
```
🦍 EARLY SIGNALS:
  GME - Reddit: 0.90, Volume: 0.30  ← SET ALERT!
```
**Action:** Add GME to watchlist, set alert for RVOL > 1.5

---

### 10:30 AM - Intraday Scan
```
🔥 VOLUME BREAKOUTS:
  GME - Volume: 0.85, RVOL: 1.65x  ← VOLUME CONFIRMING!

🏆 CONFIRMED MOMENTUM:
  GME - Composite: 0.88 (Reddit: 0.90, Volume: 0.85)  ← ENTER HERE!
```
**Action:** Enter GME with trailing stop

---

### 2:00 PM - Update
```
🏆 CONFIRMED MOMENTUM:
  GME - Composite: 0.95 (Reddit: 0.95, Volume: 0.95)  ← STRONG MOMENTUM
```
**Action:** Trail stop, take partials

---

### 4:00 PM - Close
```
📊 TOP 10 OVERALL:
  GME - Closed +15%  ← YOU CAUGHT IT EARLY!
```

---

## 🎯 Summary

**The key is TIMING:**

1. 🦍 **Early Signals** = **BEST entries** (Reddit first)
2. 🔥 **Volume Breakouts** = **Confirmation** (Volume confirms)
3. 🏆 **Confirmed Momentum** = **Late stage** (Both strong, late entry)

**Use MAX mode** to catch stocks strong in ANY factor, then use the multi-phase views to determine your entry strategy!

🚀 **You now have an edge over traders using simple averages!**

