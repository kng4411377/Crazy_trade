# Archived Scripts

Scripts here are kept for reference but are **not** part of the main workflow. Use them only when needed.

## What's in the main project

**Startup:**
- `run.sh` – start the bot
- `run_api.sh` – start the API server
- `start_background.sh` – start bot/API in background (with status, stop, etc.)
- `setup.sh` – first-time setup (venv, config)

**Config:**
- `merge_config.py` – merge new options from config.yaml.example into your config.yaml (preserves your settings)

**Tests:**
- `test_connection.py` – test Alpaca API connection
- `scripts/test_all.py` – full test (config, Alpaca, Gemini, momentum, indicators, optional order)
- `scripts/test_gemini.py` – test Gemini AI connection and analysis
- `test_crypto_symbols.py` – test Alpaca crypto symbols
- `verify_fills.sh` – verify order fills (requires API server)
- `run_tests.sh` / `run_tests.py` – run pytest suite

---

## archive/shell/

| Script | Purpose |
|--------|--------|
| `check_bot_data.sh` | Inspect bot.db (orders, fills, events). Use when debugging. |
| `reset_bot.sh` | Reset account and/or database. See docs/RESET_GUIDE.md. |
| `update_config.sh` | Compare config.yaml with template and help merge. |

## archive/scripts/

| Script | Purpose |
|--------|--------|
| `check_status.py` | Status report from database (orders, events). |
| `export_trades.py` | Export closed trades to CSV. |
| `reset_paper_account.py` | Reset paper account (close positions, cancel orders). |
| `scan_momentum.py` | Scan and score momentum for symbols (momentum layer). |
| `show_performance.py` | Show performance stats from database. |
| `test_momentum_filter.py` | Test momentum filter only. |
| `verify_project.py` | Old project structure check (references removed). |

To run an archived script from project root:
```bash
python3 archive/scripts/export_trades.py
./archive/shell/reset_bot.sh
```
