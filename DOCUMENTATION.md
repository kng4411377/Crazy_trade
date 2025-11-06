# 📚 Documentation Index

Complete documentation for the Crazy Trade Bot.

## 🚀 Getting Started

### **[README.md](README.md)** - Main Overview
- What the bot does
- Features and architecture
- Basic concepts

### **[QUICKSTART.md](QUICKSTART.md)** - Quick Start Guide
- Installation steps
- Configuration basics
- First run tutorial

### **[SETUP_SECRETS.md](SETUP_SECRETS.md)** - API Keys Setup
- How to get Alpaca API keys
- Secure secrets management
- Environment variables

---

## 🖥️ Deployment

### **[UBUNTU_DEPLOYMENT.md](UBUNTU_DEPLOYMENT.md)** - Ubuntu Server Deployment
- Background mode setup
- Systemd service configuration
- State recovery after restart
- Monitoring and maintenance

---

## 🔌 API & Monitoring

### **[API_GUIDE.md](API_GUIDE.md)** - REST API Documentation
- All API endpoints
- Request/response examples
- Monitoring your bot
- Performance metrics

---

## 📖 Additional Resources

### **[examples/README.md](examples/README.md)** - Code Examples
- Monitoring scripts
- Integration examples

---

## 🆘 Getting Help

### Common Issues

**Connection Problems:**
- Verify `secrets.yaml` has correct API keys
- Test connection: `python3 test_connection.py`
- Check Alpaca service status: https://status.alpaca.markets

**Bot Not Trading:**
- Check market hours (9:30 AM - 4:00 PM ET, weekdays only)
- View logs: `./start_background.sh logs`
- Check status: `curl http://localhost:8080/status`

**API Server Issues:**
- Restart: `./start_background.sh restart`
- Check port 8080 is not in use: `lsof -i :8080`

**State Recovery Questions:**
- See [UBUNTU_DEPLOYMENT.md](UBUNTU_DEPLOYMENT.md) - "State Recovery" section
- Bot automatically recovers positions and orders from Alpaca + database

---

## 🔧 Quick Commands

### Running the Bot
```bash
# Test connection
python3 test_connection.py

# Start bot (foreground)
./run.sh

# Start bot (background)
./start_background.sh start

# Check status
./start_background.sh status

# View logs
./start_background.sh logs

# Stop
./start_background.sh stop
```

### API Server
```bash
# Start API
./run_api.sh

# Or with bot
./start_background.sh start

# Test API
curl http://localhost:8080/health
curl http://localhost:8080/status
curl http://localhost:8080/performance
```

### Utilities
```bash
# Reset paper account
python3 scripts/reset_paper_account.py

# View performance
python3 scripts/show_performance.py

# Export trades
python3 scripts/export_trades.py

# Check bot status
python3 scripts/check_status.py
```

---

## 📁 File Structure

```
crazy_trade/
├── README.md                    # Main overview
├── QUICKSTART.md               # Getting started
├── SETUP_SECRETS.md            # API keys setup
├── UBUNTU_DEPLOYMENT.md        # Server deployment
├── API_GUIDE.md                # API documentation
│
├── config.yaml                 # Main configuration
├── secrets.yaml                # API keys (in .gitignore)
├── secrets.yaml.example        # Template
│
├── run.sh                      # Start bot
├── run_api.sh                  # Start API
├── start_background.sh         # Background mode
│
├── main.py                     # Bot entry point
├── api_server.py               # API server
├── test_connection.py          # Connection test
│
├── src/                        # Source code
│   ├── alpaca_client.py       # Alpaca API wrapper
│   ├── bot.py                 # Main bot logic
│   ├── config.py              # Configuration
│   ├── database.py            # Database models
│   ├── market_hours.py        # Market hours
│   ├── performance.py         # Performance tracking
│   ├── sizing.py              # Position sizing
│   └── state_machine.py       # Symbol state management
│
├── scripts/                    # Utility scripts
│   ├── reset_paper_account.py
│   ├── show_performance.py
│   ├── export_trades.py
│   └── check_status.py
│
├── tests/                      # Unit tests
└── examples/                   # Code examples
```

---

## 🎓 Learning Path

**New Users:**
1. Read [README.md](README.md) - Understand what the bot does
2. Follow [QUICKSTART.md](QUICKSTART.md) - Get it running
3. Review [SETUP_SECRETS.md](SETUP_SECRETS.md) - Secure your keys
4. Read [API_GUIDE.md](API_GUIDE.md) - Learn monitoring

**Deploying to Server:**
1. Complete "New Users" steps above
2. Follow [UBUNTU_DEPLOYMENT.md](UBUNTU_DEPLOYMENT.md)
3. Set up systemd services
4. Configure monitoring

**Advanced:**
1. Review source code in `src/`
2. Check `examples/` for integrations
3. Customize `config.yaml` for your strategy
4. Run tests: `pytest tests/`

---

## 🔗 External Resources

- **Alpaca Docs:** https://docs.alpaca.markets/docs/trading-api
- **Alpaca Dashboard:** https://app.alpaca.markets/paper/dashboard/overview
- **Alpaca Status:** https://status.alpaca.markets
- **Python SDK:** https://github.com/alpacahq/alpaca-py

---

## 📝 Configuration Reference

See `config.yaml` for all options:

- **Mode:** `paper` or `live`
- **Watchlist:** Symbols to trade
- **Allocation:** Position sizing
- **Entries:** Buy stop configuration
- **Stops:** Trailing stop settings
- **Hours:** Market hours restrictions
- **Cooldowns:** After stop-out delays
- **Polling:** Check intervals
- **Risk:** Exposure limits

---

## 🎯 Support Checklist

Before asking for help:

- [ ] Read relevant documentation
- [ ] Check logs: `./start_background.sh logs`
- [ ] Test connection: `python3 test_connection.py`
- [ ] Check API: `curl http://localhost:8080/health`
- [ ] Verify market hours (weekdays 9:30 AM - 4:00 PM ET)
- [ ] Review Alpaca service status

---

**Documentation Version:** 1.0 (Alpaca)  
**Last Updated:** November 2024

