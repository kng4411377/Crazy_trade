# Momentum Config Update Guide

Quick reference for updating `momentum_config.yaml` when new features are added.

---

## 🔄 Updating Momentum Config

### When to Update

After `git pull`, if there are new features in the momentum layer:

```bash
# Check if momentum config needs updating
diff momentum_config.yaml momentum_config.yaml.example
```

### Method 1: Smart Merge (Recommended)

```bash
python3 merge_config.py
```

This will:
- ✅ Merge updates from `momentum_config.yaml.example`
- ✅ Preserve your existing settings
- ✅ Create backup at `momentum_config.yaml.backup`

### Method 2: Manual Update

```bash
# Compare files
diff momentum_config.yaml momentum_config.yaml.example

# Or visual diff
code --diff momentum_config.yaml momentum_config.yaml.example

# Copy new fields manually
nano momentum_config.yaml
```

---

## 📋 Common Updates

### Adding New Providers

When a new provider is added:

```yaml
# NEW: Added to momentum_config.yaml.example
providers:
  marketstack:
    enabled: false  # New provider

# Your momentum_config.yaml - add this section
providers:
  alphavantage:
    enabled: true  # Your existing config
  stocktwits:
    enabled: true  # Your existing config
  marketstack:     # ADD THIS
    enabled: false
```

### Adding New Factors

When a new factor is added:

```yaml
# NEW: Added to momentum_config.yaml.example
factors:
  options_flow:  # New factor
    enabled: false
    weight: 0.20

# Your momentum_config.yaml - add this section
factors:
  volume_anomaly:
    enabled: true
    weight: 0.30
  sentiment_velocity:
    enabled: true
    weight: 0.30
  options_flow:      # ADD THIS
    enabled: false
    weight: 0.20
```

### Updating Weights

When default weights change:

```yaml
# OLD default
factors:
  volume_anomaly:
    weight: 0.30

# NEW default (in .example)
factors:
  volume_anomaly:
    weight: 0.35  # Increased

# You can keep your old value or update to new default
```

---

## ✅ After Updating

1. **Validate syntax:**
   ```bash
   python3 -c "import yaml; yaml.safe_load(open('momentum_config.yaml'))"
   ```

2. **Test it:**
   ```bash
   python scripts/test_momentum_providers.py
   ```

3. **Restart bot:**
   ```bash
   ./run.sh
   ```

---

## 🔙 Rollback

If something goes wrong:

```bash
# Restore from backup
cp momentum_config.yaml.backup momentum_config.yaml

# Or start fresh
cp momentum_config.yaml.example momentum_config.yaml
# Then re-apply your customizations
```

---

## 📚 Related Docs

- **Main Update Guide**: [UPDATING_CONFIG.md](UPDATING_CONFIG.md)
- **Momentum Layer Requirements**: [MOMENTUM_LAYER_REQUIREMENTS.md](MOMENTUM_LAYER_REQUIREMENTS.md)
- **Momentum Status**: [MOMENTUM_LAYER_STATUS.md](MOMENTUM_LAYER_STATUS.md)

---

**Tip**: Always review the `.example` file comments - they explain what each new field does!

