# Changelog

All notable changes to the Crazy Trade Bot project.

## [1.0.0] - 2024-11-06

### Major Changes
- **Migrated from IBKR to Alpaca Trading API**
  - Replaced `ib_insync` with `alpaca-py` SDK
  - Updated all trading operations for Alpaca REST API
  - Improved reliability and ease of deployment

### Added
- **Alpaca Integration**
  - Full Alpaca Trading API support
  - Paper and live trading modes
  - Automatic position and order recovery
  
- **Security Improvements**
  - Separate `secrets.yaml` for API keys
  - Keys excluded from Git via `.gitignore`
  - Environment variable support
  
- **Deployment Features**
  - Background mode script (`start_background.sh`)
  - Systemd service files for Ubuntu
  - Automatic restart on failure
  - State recovery after restart
  
- **API Server**
  - REST API for monitoring (port 8080)
  - Status, performance, fills, orders endpoints
  - Read-only access for safety
  
- **Utility Scripts**
  - `reset_paper_account.py` - Reset paper trading account
  - `test_connection.py` - Test Alpaca API connection
  - Background management scripts

### Changed
- **Configuration**
  - `config.yaml` now uses Alpaca settings (no IBKR)
  - Simplified configuration structure
  - Added `secrets.yaml` for API keys
  
- **Order Handling**
  - Entry orders placed first, trailing stops after fill
  - REST API polling for order events (5-second intervals)
  - Compatible with Alpaca's order model
  
- **Documentation**
  - Cleaned up all IBKR references
  - Added `DOCUMENTATION.md` as index
  - Created `UBUNTU_DEPLOYMENT.md` for server setup
  - Updated `QUICKSTART.md` for Alpaca
  - Added `SETUP_SECRETS.md` for security

### Removed
- IBKR Gateway dependency
- `ibkr_client.py` (replaced with `alpaca_client.py`)
- All IBKR-specific configuration
- Outdated migration and temporary documentation

### Technical Details
- **Order Flow:** Entry order → Wait for fill → Place trailing stop
- **Event System:** REST API polling (every 5 seconds)
- **State Recovery:** Automatic via Alpaca API + local database
- **Market Data:** Real-time quotes from Alpaca

### Migration Notes
- Existing `bot.db` database remains compatible
- All historical data preserved
- Positions and orders managed by Alpaca
- Cooldown timers stored in database

---

## Development

### Version Scheme
- **Major.Minor.Patch** (e.g., 1.0.0)
- Major: Breaking changes or platform switches
- Minor: New features
- Patch: Bug fixes

### Current Version
- **1.0.0** - Alpaca-native trading bot

---

For detailed upgrade instructions, see `DOCUMENTATION.md`.

