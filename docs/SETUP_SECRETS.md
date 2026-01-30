# Setting Up API Keys (Secrets)

## 🔐 One file for all secrets: `secrets.yaml`

All API keys and optional environment overrides live in **one file**: `secrets.yaml` (gitignored).  
You do **not** need a `.env` file; the bot loads Alpaca and Gemini from `secrets.yaml`.  
Optional keys (e.g. for the momentum layer) can go in an `env:` section and are exported to the environment when config loads.

## 📋 Quick Setup

### Step 1: Copy the Example Files

```bash
# Copy config templates (setup.sh does this automatically)
cp config.yaml.example config.yaml
cp secrets.yaml.example secrets.yaml

# Crypto: enable crypto.enabled and set crypto.watchlist in config.yaml (no separate file)
```

### Step 2: Get Your Alpaca API Keys

1. Go to https://app.alpaca.markets/
2. Navigate to **Paper Trading** section
3. Find or generate your **API Keys**:
   - API Key ID
   - Secret Key

### Step 3: Edit secrets.yaml

Open `secrets.yaml` and add your real keys:

```yaml
alpaca:
  api_key: "PKxxxxxxxxxxxxxxxxxx"      # Your real API key
  secret_key: "xxxxxxxxxxxxxxxx"       # Your real secret key

# Optional: Gemini AI (for AI analysis layer)
gemini:
  api_key: "YOUR_GEMINI_API_KEY"
```

**Optional – momentum / other providers:**  
If you use the momentum layer or any code that reads from the environment (e.g. `ALPHAVANTAGE_API_KEY`, `RAPIDAPI_KEY`), add an `env:` section. Those keys are exported to `os.environ` when config loads:

```yaml
env:
  ALPHAVANTAGE_API_KEY: "your_key"
  RAPIDAPI_KEY: "your_key"
  LOG_LEVEL: "INFO"
```

Only add keys you actually use. See `secrets.yaml.example` for the full template.

### Step 4: Verify It's Ignored by Git

```bash
# This should show secrets.yaml is ignored
git status

# secrets.yaml should NOT appear in untracked files
```

---

## 📁 File Structure

```
crazy_trade/
├── config.yaml              ❌ NEVER commit (your local settings - gitignored)
├── config.yaml.example      ✅ Safe to commit (template)
├── secrets.yaml             ❌ NEVER commit (has API keys - gitignored)
├── secrets.yaml.example     ✅ Safe to commit (template)
└── .gitignore               ✅ Excludes config.yaml, secrets.yaml
```

**Why these files are gitignored:**
- `secrets.yaml` - Contains your API keys (security risk)
- `config.yaml` - Contains your personal strategy and crypto settings (prevents git conflicts)

---

## 🔍 How It Works

1. **Load `config.yaml`** – Main settings (watchlist, allocation, etc.)
2. **Load `secrets.yaml`** – Alpaca and Gemini keys are merged into config; any `env:` entries are set in `os.environ` (so momentum/other code using `os.getenv()` can use them).

```python
# This loads both files and exports env section:
config = BotConfig.from_yaml('config.yaml')
```

**Why one file?**  
A single `secrets.yaml` keeps all secrets in one place, avoids duplication with `.env`, and supports optional `env:` for providers that expect environment variables.

---

## 🔄 Fallback: Environment variables only

If `secrets.yaml` does **not** exist, the bot will use environment variables for Alpaca only:

```bash
export ALPACA_API_KEY="PKxxxxxxxxxx"
export ALPACA_SECRET_KEY="xxxxxxxxxxxxxx"
./run.sh
```

Prefer using `secrets.yaml` so Gemini and optional `env` keys are in one place.

---

## ✅ Verify Your Setup

Test that your secrets are loaded correctly:

```bash
python3 test_connection.py
```

**Expected output:**
```
✅ Connected!
Account Value: $100,000.00
...
✅ ALL TESTS PASSED!
```

---

## 🆘 Troubleshooting

### "secrets.yaml not found"

**Error:**
```
FileNotFoundError: secrets.yaml not found
Please create it from secrets.yaml.example
```

**Solution:**
```bash
cp secrets.yaml.example secrets.yaml
# Edit secrets.yaml with your real keys
```

### "Invalid API Key"

**Problem:** Keys are incorrect

**Solution:**
1. Check you copied the **full** key (no spaces)
2. Verify you're using **Paper Trading** keys (start with `PK`)
3. Regenerate keys in Alpaca dashboard if needed

### Git Shows secrets.yaml

**Problem:** secrets.yaml appears in `git status`

**Solution:**
```bash
# Remove from Git if accidentally added
git rm --cached secrets.yaml

# Verify .gitignore includes it
cat .gitignore | grep secrets.yaml
```

---

## 🎯 Best Practices

### ✅ DO:
- Keep `secrets.yaml` out of Git
- Use different keys for paper vs live
- Rotate keys periodically
- Use environment variables in production

### ❌ DON'T:
- Commit secrets.yaml to Git
- Share your secret key
- Use live keys in paper mode
- Hard-code keys in Python files

---

## 🚀 Ready to Run

Once you've set up `secrets.yaml`:

```bash
# Test connection
python3 test_connection.py

# Start the bot
./run.sh

# Monitor (optional)
./run_api.sh
```

---

## 📚 Related Files

- `secrets.yaml` – **Single file for all secrets** (gitignored): Alpaca, Gemini, optional `env:` section
- `secrets.yaml.example` – Template with usage comments (safe to commit)
- `config.yaml` – Your local strategy/config (gitignored)
- `config.yaml.example` – Config template (safe to commit)
- `.gitignore` – Excludes config.yaml, secrets.yaml, health_status.json

---

**Remember: Keep your secrets secret! 🔐**

