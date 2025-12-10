# Setting Up API Keys (Secrets)

## 🔐 Security First!

Your Alpaca API keys should **NEVER** be committed to Git. We keep them in a separate `secrets.yaml` file that is ignored by Git.

## 📋 Quick Setup

### Step 1: Copy the Example Files

```bash
# Copy config templates (setup.sh does this automatically)
cp config.yaml.example config.yaml
cp secrets.yaml.example secrets.yaml

# Optional: for crypto trading
cp config.crypto.yaml.example config.crypto.yaml
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
```

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
├── config.crypto.yaml       ❌ NEVER commit (your crypto settings - gitignored)
├── config.crypto.yaml.example ✅ Safe to commit (template)
└── .gitignore              ✅ Excludes config.yaml, secrets.yaml, etc.
```

**Why both files are gitignored:**
- `secrets.yaml` - Contains your API keys (security risk)
- `config.yaml` - Contains your personal strategy settings (prevents git conflicts)

---

## 🔍 How It Works

The bot loads configuration in two steps:

1. **Load `config.yaml`** - Main settings (watchlist, allocation, etc.)
2. **Load `secrets.yaml`** - API keys (merged automatically)

```python
# This automatically loads both files:
config = BotConfig.from_yaml('config.yaml')
```

---

## 🔄 Alternative: Environment Variables

If you prefer environment variables:

```bash
# Set environment variables
export ALPACA_API_KEY="PKxxxxxxxxxx"
export ALPACA_SECRET_KEY="xxxxxxxxxxxxxx"

# Run the bot (it will use env vars if secrets.yaml doesn't exist)
./run.sh
```

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

- `config.yaml` - Your local settings (gitignored, never committed)
- `config.yaml.example` - Template for config (safe to commit)
- `secrets.yaml` - Your API keys (gitignored, never committed)
- `secrets.yaml.example` - Template for secrets (safe to commit)
- `config.crypto.yaml` - Your crypto settings (gitignored, optional)
- `config.crypto.yaml.example` - Template for crypto (safe to commit)
- `.gitignore` - Excludes local config and secrets files
- `SETUP_SECRETS.md` - This guide

---

**Remember: Keep your secrets secret! 🔐**

