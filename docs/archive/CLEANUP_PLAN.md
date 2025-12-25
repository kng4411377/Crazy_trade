# 🧹 Cleanup Plan

## 📁 Document Organization

### ✅ Keep (User-Facing Docs)
- `README.md` - Main project readme
- `MOMENTUM_STRATEGY.md` - **NEW** Multi-phase momentum strategy guide
- `ENV_SETUP_GUIDE.md` - Environment setup guide
- `ENV_EXAMPLE.txt` - Environment template
- `requirements.txt` - Dependencies

### 📦 Move to docs/archive/ (Development Artifacts)
These are implementation notes, useful for history but not for users:
- `ALPHA_VANTAGE_QUOTA_ALERT.md`
- `ANALYSIS_REPORT.md`
- `APEWISDOM_IMPLEMENTATION_COMPLETE.md`
- `API_FIXES_SUMMARY.md`
- `DOCS_ORGANIZED.md`
- `DOTENV_FIX_SUMMARY.md`
- `FIXES_APPLIED.md`
- `GOOGLE_TRENDS_EXPLAINED.md`
- `GOOGLE_TRENDS_IMPLEMENTATION.md`
- `GOOGLE_TRENDS_READY.md`
- `GOOGLE_TRENDS_RETRY_SYSTEM.md`
- `IMPLEMENTATION_SUMMARY.md`
- `MOMENTUM_STATUS.txt`
- `PROVIDER_ISSUES.md`
- `PYTHON39_FIX.md`
- `RETRY_IMPLEMENTATION_COMPLETE.md`
- `STOCKTWITS_UPDATE.md`
- `YFINANCE_SWITCH_SUMMARY.md`

### 🗑️ Delete (Duplicates/Outdated)
- `MOMENTUM_QUICKSTART.md` - Replaced by V2

### 📝 Consolidate into docs/
- `APEWISDOM_SETUP.md` → Move to `docs/momentum/`
- `MOMENTUM_QUICKSTART_V2.md` → Move to `docs/momentum/QUICKSTART.md`
- `MOMENTUM_STRATEGY.md` → Move to `docs/momentum/STRATEGY.md`

---

## 🗂️ Proposed New Structure

```
/Users/tony.ng/work/temp/crazy_trade/
├── README.md                          # Main readme
├── requirements.txt                   # Dependencies
├── ENV_EXAMPLE.txt                    # Env template
│
├── docs/                              # All documentation
│   ├── INDEX.md                       # Doc index (update)
│   ├── QUICKSTART.md                  # Quick start
│   ├── CONFIGURATION.md               # Config guide
│   │
│   ├── momentum/                      # Momentum layer docs
│   │   ├── QUICKSTART.md              # (from MOMENTUM_QUICKSTART_V2.md)
│   │   ├── STRATEGY.md                # (from MOMENTUM_STRATEGY.md)
│   │   ├── APEWISDOM_SETUP.md         # (from root)
│   │   └── CONFIG_GUIDE.md            # (existing MOMENTUM_CONFIG_GUIDE.md)
│   │
│   └── archive/                       # Development artifacts
│       └── [all implementation notes]
│
├── scripts/                           # Scripts
├── src/                               # Source code
└── tests/                             # Tests
```

---

## 🧹 Code Cleanup Tasks

### 1. Remove Unused Providers
- `src/momentum/providers/google_trends.py` - Not used (Apewisdom preferred)
- `src/momentum/factors/retail_attention.py` - Uses Google Trends (not used)

### 2. Remove Test Scripts (Move to tests/)
- `scripts/test_google_trends.py`
- `scripts/test_combined_scoring.py`
- `scripts/debug_google_trends.py`
- `scripts/test_momentum_providers.py` - Consolidate with test_apewisdom.py

### 3. Remove Utility Scripts (No longer needed)
- `install_dotenv.sh` - Already in requirements.txt
- `INSTALL_GOOGLE_TRENDS.sh` - Not using Google Trends
- `INSTALL_YFINANCE.sh` - Already in requirements.txt
- `FIX_PYTHON39.sh` - One-time fix, not needed ongoing

### 4. Clean Up examples/
- `examples/momentum_example.py` - Update to use only Apewisdom + YFinance

---

## ✅ Action Items

### Phase 1: Archive Development Docs
1. Create `docs/archive/`
2. Move 17 implementation/fix documents
3. Create `docs/archive/README.md` explaining archive purpose

### Phase 2: Reorganize User Docs
1. Create `docs/momentum/`
2. Move momentum docs from root
3. Update cross-references
4. Update `docs/INDEX.md`

### Phase 3: Remove Unused Code
1. Delete Google Trends provider & factor
2. Move test scripts to `tests/momentum/`
3. Delete one-time setup scripts
4. Clean up `examples/`

### Phase 4: Update Main Documentation
1. Update `README.md` with new doc structure
2. Update `docs/INDEX.md`
3. Create `docs/momentum/README.md`

---

## 🎯 Result

**Before:** 25 files in root, scattered docs, unused code
**After:** Clean structure, easy to navigate, no clutter

**User Experience:**
- Clear entry point (README.md)
- Organized docs by topic
- Easy to find momentum guides
- No confusion from implementation artifacts

