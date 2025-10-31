# Troubleshooting Guide

## Connection Timeout Error

### The Error
```
INFO:ib_insync.client:Connecting to localhost:5000 with clientId 12...
INFO:ib_insync.client:Connected
INFO:ib_insync.client:Disconnecting
ERROR:ib_insync.client:API connection failed: TimeoutError()
```

This means:
- ✅ TCP connection succeeds (port 5000 is open)
- ❌ API handshake times out (Gateway not accepting API connections)

---

## Step-by-Step Fix

### 1. Check IB Gateway is Running

```bash
# Check if something is listening on port 5000
lsof -i :5000

# Or on Linux
netstat -an | grep 5000
```

**Expected output:**
```
java    12345 user   123u  IPv6 0x...  TCP localhost:5000 (LISTEN)
```

**If nothing:** IB Gateway is not running → Start IB Gateway first

---

### 2. Configure IB Gateway API Settings

This is the **most common issue**!

#### Open IB Gateway Settings:
1. Launch IB Gateway
2. Click **Configure → Settings** (gear icon)
3. Go to **API → Settings**

#### Required Settings:

**Enable API:**
- ✅ Check "Enable ActiveX and Socket Clients"

**Socket Port:**
- Set to: `5000` (must match config.yaml)

**Master API Client ID** (IMPORTANT):
- Set to: `0` or leave blank
- **OR** set to a different number than your bot (not 12)

**Trusted IP Addresses:**
- Add: `127.0.0.1`

**Read-Only API:**
- ⚠️ **UNCHECK** this box (must be unchecked for trading)

**Create API Message Log File:**
- Optional, but helpful for debugging

#### After Changing Settings:
1. Click **OK**
2. **RESTART IB Gateway** (very important!)
3. Log back in

---

### 3. Verify Configuration

Check your `config.yaml`:

```yaml
ibkr:
  host: "127.0.0.1"  # localhost
  port: 5000         # Must match Gateway settings
  client_id: 12      # Must NOT conflict with Master API Client ID
```

**If Gateway Master Client ID is 12:** Change bot's client_id to something else (e.g., 10 or 100)

---

### 4. Test Connection Manually

```bash
# Test basic connectivity
python3 -c "
from ib_insync import IB
ib = IB()
print('Attempting connection...')
ib.connect('127.0.0.1', 5000, clientId=999)
print('✅ Connected successfully!')
print('Account:', ib.managedAccounts())
ib.disconnect()
"
```

**Success:** "✅ Connected successfully!"
**Failure:** Will show where it's failing

---

### 5. Common Issues & Solutions

#### Issue: "TimeoutError" (Your Current Issue)

**Causes:**
1. ❌ "Enable ActiveX and Socket Clients" not checked
2. ❌ "Read-Only API" is checked (prevents trading)
3. ❌ Client ID conflict with Master API Client ID
4. ❌ Gateway wasn't restarted after changing settings
5. ❌ Using wrong port number

**Solution:**
- Double-check API settings (see Step 2)
- **RESTART Gateway**
- Try different client_id in config.yaml

---

#### Issue: "Connection refused"

```
ConnectionRefusedError: [Errno 61] Connection refused
```

**Causes:**
- IB Gateway is not running
- Wrong port number
- Gateway listening on different interface

**Solution:**
```bash
# Check if Gateway is running
ps aux | grep -i "ibgateway\|tws"

# Check what's on port 5000
lsof -i :5000

# Try paper trading port instead (7497)
# Edit config.yaml:
#   port: 7497
```

---

#### Issue: "Permission denied" or "Read-only"

```
Error: API connection is read-only
```

**Cause:**
- "Read-Only API" is checked in Gateway settings

**Solution:**
- Gateway Settings → API → Settings
- **UNCHECK** "Read-Only API"
- Restart Gateway

---

#### Issue: Client ID Conflict

```
Error: clientId 12 is already in use
```

**Solution:**
- Change client_id in config.yaml to something else:
```yaml
ibkr:
  client_id: 100  # Change from 12 to 100 (or any unused number)
```

---

### 6. Firewall / Security

#### macOS Firewall:
```bash
# Check if firewall is blocking
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# Allow Python through firewall
System Preferences → Security & Privacy → Firewall → Firewall Options
→ Add Python to allowed apps
```

#### Linux Firewall:
```bash
# Check firewall rules
sudo iptables -L -n

# Allow localhost connections (usually already allowed)
sudo ufw allow from 127.0.0.1
```

---

### 7. Check IB Gateway Logs

**Location:**
- macOS: `~/Jts/ibgateway/[VERSION]/log/`
- Linux: `~/Jts/ibgateway/[VERSION]/log/`
- Windows: `C:\Jts\ibgateway\[VERSION]\log\`

**Look for:**
```bash
# View latest log
tail -f ~/Jts/ibgateway/*/log/*.log

# Look for API connection messages
grep -i "api\|client\|connection" ~/Jts/ibgateway/*/log/*.log
```

---

### 8. Paper Trading vs Live

#### Paper Trading:
- Uses different TWS/Gateway instance
- Default ports: 4001 (TWS) or 7497 (Gateway)
- **OR** port 5000 if configured

#### Live Trading:
- Main TWS/Gateway
- Default ports: 7496 (TWS) or 4000 (Gateway)
- **OR** port 5000 if configured

**Make sure you're connecting to the right one!**

```yaml
# config.yaml
mode: "paper"  # Must match which Gateway you're running

ibkr:
  port: 5000   # Must match Gateway's socket port
```

---

### 9. Quick Diagnostic Script

Save as `test_connection.py`:

```python
#!/usr/bin/env python3
import sys
from ib_insync import IB
import asyncio

async def test():
    ib = IB()
    
    print("=" * 60)
    print("IB Gateway Connection Test")
    print("=" * 60)
    
    try:
        print("\n1. Attempting connection to localhost:5000...")
        await ib.connectAsync('127.0.0.1', 5000, clientId=999, timeout=10)
        
        print("✅ Connected!")
        
        print("\n2. Getting account info...")
        accounts = ib.managedAccounts()
        print(f"   Accounts: {accounts}")
        
        print("\n3. Getting positions...")
        positions = ib.positions()
        print(f"   Positions: {len(positions)}")
        
        print("\n4. Testing market data...")
        contract = ib.Stock('AAPL', 'SMART', 'USD')
        ticker = ib.reqMktData(contract)
        await asyncio.sleep(2)
        print(f"   AAPL last price: {ticker.last}")
        
        print("\n✅ ALL TESTS PASSED!")
        print("   Your IB Gateway is configured correctly.")
        
    except asyncio.TimeoutError:
        print("\n❌ TIMEOUT ERROR")
        print("\nMost likely causes:")
        print("1. 'Enable ActiveX and Socket Clients' not checked")
        print("2. 'Read-Only API' is checked (should be unchecked)")
        print("3. Client ID conflict")
        print("4. Gateway needs restart after config change")
        print("\nSee TROUBLESHOOTING.md for detailed steps")
        
    except ConnectionRefusedError:
        print("\n❌ CONNECTION REFUSED")
        print("\nIB Gateway is not running or not on port 5000")
        print("1. Start IB Gateway")
        print("2. Check port in Gateway settings")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        
    finally:
        if ib.isConnected():
            ib.disconnect()
            print("\n✅ Disconnected cleanly")

if __name__ == '__main__':
    asyncio.run(test())
```

Run it:
```bash
python3 test_connection.py
```

---

## Your Specific Error - Quick Fix

Based on your error, try these in order:

### Fix #1: Enable API in Gateway (Most Likely)
1. IB Gateway → Configure → Settings → API → Settings
2. ✅ Check "Enable ActiveX and Socket Clients"
3. ⚠️ **UNCHECK** "Read-Only API"
4. Click OK
5. **RESTART IB Gateway**
6. Try bot again: `./run.sh`

### Fix #2: Change Client ID
Edit `config.yaml`:
```yaml
ibkr:
  client_id: 100  # Change from 12 to 100
```

Then try: `./run.sh`

### Fix #3: Try Paper Trading Port
If using paper trading, try:
```yaml
ibkr:
  port: 7497  # Paper trading default port
```

---

## Still Not Working?

### Get More Info:

```bash
# 1. Check Gateway is running
lsof -i :5000

# 2. Test with diagnostic script
python3 test_connection.py

# 3. Check Gateway logs
tail -20 ~/Jts/ibgateway/*/log/*.log

# 4. Try different client ID
# Edit config.yaml, change client_id to 100

# 5. Verify you're using correct mode
# config.yaml: mode should match Gateway (paper vs live)
```

### Report Issue With:
1. Output of `lsof -i :5000`
2. Gateway version and settings screenshot
3. Full bot.log output
4. Result of `python3 test_connection.py`

---

## Prevention Tips

✅ **Always:**
1. Start IB Gateway first, then start bot
2. Restart Gateway after changing API settings
3. Use unique client IDs for each bot
4. Check Gateway logs if issues occur
5. Test connection manually before running bot

⚠️ **Never:**
1. Run multiple bots with same client_id
2. Forget to uncheck "Read-Only API"
3. Skip restarting Gateway after settings change

---

## Quick Reference

### Working Configuration Example:

**IB Gateway Settings:**
- ✅ Enable ActiveX and Socket Clients: CHECKED
- ❌ Read-Only API: UNCHECKED
- Socket Port: 5000
- Master API Client ID: 0 or blank
- Trusted IPs: 127.0.0.1

**config.yaml:**
```yaml
ibkr:
  host: "127.0.0.1"
  port: 5000
  client_id: 12  # (or 100 if 12 conflicts)
mode: "paper"  # Must match Gateway type
```

---

**Good luck! Most connection issues are solved by properly enabling API in Gateway settings and restarting.** 🚀

