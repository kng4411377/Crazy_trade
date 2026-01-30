#!/usr/bin/env python3
"""
System Monitor - Runs alongside the trading bot on Ubuntu.

Checks CPU usage and temperature every 30 seconds. Writes health_status.json
with low_power_mode: true when CPU > 80% or temperature >= 75°C.
Recovers (low_power_mode: false) after 3 consecutive checks with CPU < 40%.

Usage:
  python3 system_monitor.py
  # Or via PM2: pm2 start ecosystem.config.js --only crazy-trade-monitor
"""

import json
import time
import sys
from pathlib import Path

try:
    import psutil
except ImportError:
    print("psutil not installed. Run: pip install psutil", file=sys.stderr)
    sys.exit(1)

# Default path: same directory as this script (project root when run from there)
HEALTH_FILE = Path(__file__).resolve().parent / "health_status.json"
INTERVAL_SEC = 30
CPU_HIGH_THRESHOLD = 80.0   # % - trigger low-power mode
CPU_LOW_THRESHOLD = 40.0    # % - recovery threshold
TEMP_THRESHOLD = 75.0       # °C - trigger low-power mode
RECOVERY_CONSECUTIVE = 3    # Consecutive low CPU checks before recovery


def get_cpu_percent() -> float:
    """Current CPU usage (blocking call, ~1s)."""
    return psutil.cpu_percent(interval=1)


def get_cpu_temperature() -> float | None:
    """Current CPU temperature in °C if available (Linux)."""
    try:
        temps = psutil.sensors_temperatures()
        if not temps:
            return None
        # Prefer 'coretemp' (Intel) or 'cpu_thermal' (RPi/ARM), else first available
        for name in ("coretemp", "cpu_thermal", "k10temp", "zenpower"):
            if name in temps:
                return temps[name][0].current
        return list(temps.values())[0][0].current
    except (AttributeError, IndexError, KeyError):
        return None


def read_health() -> dict:
    """Read current health_status.json or return defaults."""
    if not HEALTH_FILE.exists():
        return {"low_power_mode": False, "updated": None, "cpu_percent": None, "temperature": None}
    try:
        with open(HEALTH_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"low_power_mode": False, "updated": None, "cpu_percent": None, "temperature": None}


def write_health(low_power_mode: bool, cpu_percent: float | None, temperature: float | None):
    """Write health_status.json."""
    from datetime import datetime
    payload = {
        "low_power_mode": low_power_mode,
        "updated": datetime.utcnow().isoformat() + "Z",
        "cpu_percent": round(cpu_percent, 1) if cpu_percent is not None else None,
        "temperature": round(temperature, 1) if temperature is not None else None,
    }
    with open(HEALTH_FILE, "w") as f:
        json.dump(payload, f, indent=2)


def main():
    consecutive_low = 0
    print(f"System monitor started. Writing to {HEALTH_FILE}")
    print(f"  CPU > {CPU_HIGH_THRESHOLD}% or temp >= {TEMP_THRESHOLD}°C → low_power_mode: true")
    print(f"  CPU < {CPU_LOW_THRESHOLD}% for {RECOVERY_CONSECUTIVE} checks → low_power_mode: false")
    print()

    while True:
        try:
            cpu = get_cpu_percent()
            temp = get_cpu_temperature()
            current = read_health()
            low_power = current.get("low_power_mode", False)

            # Trigger: high CPU or high temperature
            if cpu >= CPU_HIGH_THRESHOLD or (temp is not None and temp >= TEMP_THRESHOLD):
                consecutive_low = 0
                if not low_power:
                    write_health(True, cpu, temp)
                    print(f"[LOW POWER] CPU={cpu:.1f}% temp={temp}°C → low_power_mode: true")
                else:
                    write_health(True, cpu, temp)
            else:
                # Below trigger; check recovery
                if cpu < CPU_LOW_THRESHOLD:
                    consecutive_low += 1
                    if low_power and consecutive_low >= RECOVERY_CONSECUTIVE:
                        write_health(False, cpu, temp)
                        print(f"[RECOVERY] CPU={cpu:.1f}% for {RECOVERY_CONSECUTIVE} checks → low_power_mode: false")
                        consecutive_low = 0
                    elif low_power:
                        write_health(True, cpu, temp)
                else:
                    consecutive_low = 0
                    if low_power:
                        write_health(True, cpu, temp)

        except KeyboardInterrupt:
            print("\nMonitor stopped.")
            break
        except Exception as e:
            print(f"Monitor error: {e}", file=sys.stderr)

        time.sleep(INTERVAL_SEC)


if __name__ == "__main__":
    main()
