# 🔑 .env File Setup Guide

## Problem

You set `ALPHAVANTAGE_API_KEY` in `.env` but the bot still says "no_alphavantage_provider_available".

## Solution

The bot needs to **load** the `.env` file. Here's how to fix it:

---

## Step 1: Install python-dotenv

```bash
# If you're using a virtual environment:
source venv/bin/activate
pip install python-dotenv

# Or without venv:
pip3 install --user python-dotenv
```

**Alternative - Add to requirements.txt:**
```bash
pip install -r requirements.txt
# python-dotenv is now included in requirements.txt
```

---

## Step 2: Create Your .env File

```bash
# Copy the example template
cp ENV_EXAMPLE.txt .env

# Or create manually
touch .env
```

---

## Step 3: Add Your API Keys

Edit `.env` and add your keys:

```bash
# === Required for Momentum Layer ===
ALPHAVANTAGE_API_KEY=your_actual_key_here
RAPIDAPI_KEY=your_actual_rapidapi_key_here
STOCKTWITS_USE_RAPIDAPI=true
```

**Important**: 
- ✅ Use actual values, not placeholders
- ✅ No quotes needed around values
- ✅ No spaces around the `=` sign

**Example**:
```bash
# ❌ Wrong:
ALPHAVANTAGE_API_KEY = "your_key_here"

# ✅ Correct:
ALPHAVANTAGE_API_KEY=ABC123XYZ789
```

---

## Step 4: Verify It Loads

```bash
# Test that environment variables load
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Alpha Vantage Key:', os.getenv('ALPHAVANTAGE_API_KEY'))"
```

Expected output:
```
Alpha Vantage Key: ABC123XYZ789
```

If you see `None`, the `.env` file is not being read.

---

## Step 5: Test the Providers

```bash
python scripts/test_momentum_providers.py
```

Expected output:
```
Testing Alpha Vantage Provider
✅ Initialization successful
✅ Health check passed
✅ Price data retrieved
```

---

## Common Issues

### Issue: "command not found: pip"

**Solution**: Use `pip3` or `python3 -m pip`:
```bash
python3 -m pip install python-dotenv
```

### Issue: Still says "no_alphavantage_provider_available"

**Check**:
1. Is `.env` in the project root? (`ls -la .env`)
2. Are there any typos in variable names?
3. Is `python-dotenv` installed? (`pip list | grep dotenv`)
4. Is the key valid? Test it directly:
   ```bash
   curl "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey=YOUR_KEY"
   ```

### Issue: "Permission denied" or "Operation not permitted"

**Solution**: Install in user directory:
```bash
pip3 install --user python-dotenv
```

---

## How It Works

The code now automatically loads `.env` at startup:

```python
# main.py
from dotenv import load_dotenv
load_dotenv()  # Reads .env file and sets environment variables
```

This happens in:
- ✅ `main.py` (bot entry point)
- ✅ `scripts/test_momentum_providers.py` (test script)
- ✅ `examples/momentum_example.py` (examples)

---

## Security

✅ **Safe**: `.env` is in `.gitignore` - your keys won't be committed  
✅ **Template**: `ENV_EXAMPLE.txt` is committed (no real keys)  
✅ **Best Practice**: Always use `.env` for secrets, never hardcode

---

## Quick Reference

```bash
# Setup checklist
☐ Install python-dotenv
☐ Create .env file
☐ Add ALPHAVANTAGE_API_KEY
☐ Add RAPIDAPI_KEY (for StockTwits)
☐ Test with test_momentum_providers.py
☐ Run the bot!
```

---

## Need Keys?

### Alpha Vantage (Free):
1. Visit: https://www.alphavantage.co/support/#api-key
2. Enter email
3. Get instant key
4. Free tier: 5 calls/min, 500/day

### RapidAPI (Free Tier):
1. Visit: https://rapidapi.com/
2. Sign up
3. Search "StockTwits"
4. Subscribe to free tier
5. Copy your RapidAPI key

---

**Ready to go?** Run `python scripts/test_momentum_providers.py` to verify! 🚀

