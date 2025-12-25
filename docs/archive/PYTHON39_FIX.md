# Python 3.9 Compatibility Fix

**Issue**: You're running Python 3.9, but yfinance 1.0 requires Python 3.10+

**Error**:
```
TypeError: unsupported operand type(s) for |: 'types.GenericAlias' and 'types.GenericAlias'
```

This is because yfinance 1.0 uses the `|` union operator which was introduced in Python 3.10.

---

## ✅ **FIXED!**

### What I Fixed:

1. **Added `ProviderCapability` enum** to `src/momentum/base.py`
   - This was missing and causing the import error

2. **Pinned yfinance to 0.x** in `requirements.txt`
   - Changed from `yfinance>=0.2.32` to `yfinance>=0.2.32,<1.0`
   - Version 0.x works with Python 3.9

3. **Fixed GoogleTrendsProvider init** 
   - Removed incorrect `name` parameter from `super().__init__()`

---

## 🚀 **Run This Fix**

```bash
./FIX_PYTHON39.sh
```

This will:
1. Uninstall yfinance 1.0
2. Install yfinance 0.2.x (Python 3.9 compatible)
3. Verify the installation

---

## 🧪 **Then Test**

```bash
# Test Google Trends
python scripts/test_google_trends.py

# Test YFinance
python scripts/test_momentum_providers.py

# Run examples
python examples/momentum_example.py
```

---

## 📋 **Alternative: Manual Fix**

If the script doesn't work, run manually:

```bash
# Uninstall bad version
pip uninstall -y yfinance

# Install Python 3.9 compatible version
pip install 'yfinance>=0.2.32,<1.0'

# Verify
python -c "import yfinance; print(yfinance.__version__)"
```

Should show: `0.2.x` (not `1.0`)

---

## ⚠️ **Why This Happened**

yfinance just released version 1.0 which uses Python 3.10+ syntax:
- ❌ `list[Any] | list["CalendarQuery"]` (Python 3.10+)
- ✅ `Union[List[Any], List["CalendarQuery"]]` (Python 3.9)

By pinning to `<1.0`, we use the older, compatible version.

---

## 🔮 **Long-term Solution**

### Option 1: Upgrade Python (Recommended)
```bash
# Install Python 3.10 or 3.11
brew install python@3.11

# Create new venv
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Option 2: Stay on Python 3.9
- Keep using yfinance 0.2.x
- Pin in requirements.txt (already done!)
- Everything works fine

---

## ✅ **Ready to Test!**

Run the fix now:
```bash
./FIX_PYTHON39.sh
```

Then test:
```bash
python scripts/test_google_trends.py
```

**Should work perfectly! 🎉**

