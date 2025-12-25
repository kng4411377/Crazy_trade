# Updating Your Config with New Features

When you pull new code updates, the `.example` templates may have new features or fields. This guide shows you how to merge those updates into your local config files without losing your custom settings.

**Applies to:**
- `config.yaml` (main bot configuration)
- `momentum_config.yaml` (momentum intelligence layer)
- Any future config files

## 🎯 Quick Answer

**Recommended approach:**
```bash
# Smart Python merger (recommended - safest)
python3 merge_config.py

# Or bash helper script
./update_config.sh
```

---

## 📋 All Methods

### Method 1: Smart Python Merger (Recommended) ⭐

**Best for:** Most users - safe, automated, preserves all your settings

```bash
python3 merge_config.py
```

**What it does:**
- ✅ Merges ALL config files (config.yaml, momentum_config.yaml, etc.)
- ✅ Detects new fields in each template
- ✅ Adds them to your configs with defaults
- ✅ Preserves ALL your existing values
- ✅ Creates automatic backups
- ✅ Shows what changed

**Example output:**
```
🔄 Smart Config Merger
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 Processing config.yaml
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 Analyzing differences...

📝 Found 2 new field(s):
  • entries.entry_price_strategy
  • entries.sma_periods

🤔 Merge new fields into config.yaml? (y/n): y

✅ config.yaml updated successfully!

📝 Processing momentum_config.yaml
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ This config is up to date! No new fields to add.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✅ config.yaml
  ✅ momentum_config.yaml
```

---

### Method 2: Bash Helper Script

**Best for:** Quick diff view

```bash
./update_config.sh
```

Shows side-by-side differences and suggests next steps.

---

### Method 3: Manual Merge (Most Control)

**Best for:** Advanced users who want full control

1. **View differences:**
   ```bash
   # For main config
   diff config.yaml config.yaml.example
   
   # For momentum config
   diff momentum_config.yaml momentum_config.yaml.example
   
   # Better formatting
   diff -u config.yaml config.yaml.example | less
   ```

2. **Side-by-side comparison:**
   ```bash
   # In VS Code
   code --diff config.yaml config.yaml.example
   code --diff momentum_config.yaml momentum_config.yaml.example
   
   # In Vim
   vimdiff config.yaml config.yaml.example
   
   # In terminal
   sdiff config.yaml config.yaml.example | less
   ```

3. **Manually add new fields:**
   - Open your config file in your editor
   - Review the `.example` file for new fields
   - Copy the new fields you want
   - Paste into appropriate sections

---

### Method 4: Interactive Merge Tools

**Best for:** Resolving complex changes

```bash
# Using git mergetool (even without git)
git merge-file config.yaml config.yaml.backup config.yaml.example

# Using meld (GUI)
meld config.yaml config.yaml.example

# Using kdiff3 (GUI)
kdiff3 config.yaml config.yaml.example -o config.yaml
```

---

### Method 5: Start Fresh (Nuclear Option)

**Best for:** Major version updates or corrupted config

```bash
# 1. Backup your settings
cp config.yaml config.yaml.old

# 2. Note your important values
cat config.yaml | grep -E "(watchlist|total_usd_cap|per_symbol_usd)"

# 3. Start fresh
cp config.yaml.example config.yaml

# 4. Manually transfer your values from config.yaml.old
# Edit config.yaml and copy your:
#   - watchlist
#   - allocation settings
#   - risk settings
#   - any custom overrides
```

---

## 🆕 What's New in Recent Updates?

### Latest Features (Current Version)

**New fields added:**
```yaml
entries:
  # NEW: Choose how entry price is calculated
  entry_price_strategy: "current"  # "current" | "sma" | "opening"
  
  # NEW: SMA period configuration
  sma_periods: 10
  
  # NEW: Configurable time-in-force (was hard-coded)
  tif: "DAY"  # Now respects your setting!

stops:
  # NEW: Configurable time-in-force for stops
  tif: "GTC"
```

**What they do:**
- `entry_price_strategy` - Use SMA or opening price instead of current price
- `sma_periods` - How many bars to use for SMA calculation
- `tif` - Time-in-force for orders (DAY, GTC, IOC, etc.)

---

## 🔍 Finding What Changed

### Quick check for new fields:
```bash
# Show only field names that are new
grep -E "^  [a-z_]+:" config.yaml.example | while read line; do
  field=$(echo "$line" | cut -d: -f1)
  grep -q "$field" config.yaml || echo "NEW: $line"
done
```

### See comments for new fields:
```bash
# The .example file has detailed comments
grep -A 2 "entry_price_strategy" config.yaml.example
```

---

## ✅ After Updating

1. **Validate your config:**
   ```bash
   python3 -c "from src.config import BotConfig; BotConfig.from_yaml('config.yaml'); print('✅ Config valid!')"
   ```

2. **Test run:**
   ```bash
   # Dry run to check for issues
   python3 main.py --validate  # (if implemented)
   
   # Or just start the bot and watch logs
   ./run.sh
   ```

3. **Review new features:**
   - Read comments in `config.yaml.example`
   - Check `docs/CHANGELOG.md` for details
   - Try out new strategies in paper trading first

---

## 🆘 Troubleshooting

### "I merged but bot won't start"

**Problem:** Syntax error in YAML

**Solution:**
```bash
# Check YAML syntax
python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"

# Or restore backup
cp config.yaml.backup config.yaml
```

### "I lost my watchlist!"

**Problem:** Accidentally overwrote config

**Solution:**
```bash
# Restore from backup
cp config.yaml.backup config.yaml

# If no backup, check git history (if you committed before)
git log --all --full-history -- config.yaml
```

### "Too many changes, what are the important ones?"

**Solution:** Focus on these critical fields:
- `watchlist` - Your stocks
- `allocation.per_symbol_usd` - Position sizing
- `entries.entry_price_strategy` - New feature!
- `risk.max_concurrent_positions` - Risk control

Everything else can use template defaults.

---

## 📚 Best Practices

### ✅ DO:
- Run `python3 merge_config.py` after pulling updates
- Review new features in changelog
- Test changes in paper trading first
- Keep a backup before major changes

### ❌ DON'T:
- Blindly copy entire `config.yaml.example` over your config
- Skip reading comments in the example file
- Update live config without testing in paper first
- Delete your old config without backup

---

## 🚀 Quick Reference

| Task | Command |
|------|---------|
| Smart merge | `python3 merge_config.py` |
| View differences | `./update_config.sh` |
| Manual merge | `code --diff config.yaml config.yaml.example` |
| Validate config | `python3 -c "from src.config import BotConfig; BotConfig.from_yaml('config.yaml')"` |
| Backup current | `cp config.yaml config.yaml.backup` |
| Restore backup | `cp config.yaml.backup config.yaml` |

---

## 📖 Related Docs

- `config.yaml.example` - Latest template with all features
- `docs/CHANGELOG.md` - What changed in each version
- `docs/SETUP_SECRETS.md` - Initial setup guide
- `docs/QUICKSTART.md` - Getting started

---

**Remember:** Your `config.yaml` is gitignored, so you can experiment freely without affecting the repo! 🚀

