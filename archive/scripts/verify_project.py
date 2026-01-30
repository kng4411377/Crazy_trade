#!/usr/bin/env python3
"""Verify project structure and completeness."""

import os
from pathlib import Path

def check_file(path, description):
    """Check if a file exists."""
    exists = Path(path).exists()
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {path}")
    return exists

def main():
    """Verify project completeness."""
    print("=" * 70)
    print("CRAZY TRADE BOT - PROJECT VERIFICATION")
    print("=" * 70)
    print()
    
    all_good = True
    
    # Core source files
    print("📦 Core Source Files:")
    core_files = [
        ("src/__init__.py", "Package init"),
        ("src/bot.py", "Main bot orchestrator"),
        ("src/config.py", "Configuration management"),
        ("src/database.py", "Database models"),
        ("src/ibkr_client.py", "IBKR client wrapper"),
        ("src/market_hours.py", "Market hours checker"),
        ("src/sizing.py", "Position sizing"),
        ("src/state_machine.py", "State machine"),
    ]
    for file, desc in core_files:
        all_good &= check_file(file, desc)
    print()
    
    # Test files
    print("🧪 Test Files:")
    test_files = [
        ("tests/__init__.py", "Test package init"),
        ("tests/conftest.py", "Shared fixtures"),
        ("tests/test_config.py", "Config tests"),
        ("tests/test_database.py", "Database tests"),
        ("tests/test_market_hours.py", "Market hours tests"),
        ("tests/test_sizing.py", "Sizing tests"),
        ("tests/test_state_machine.py", "State machine tests"),
        ("tests/test_integration.py", "Integration tests"),
    ]
    for file, desc in test_files:
        all_good &= check_file(file, desc)
    print()
    
    # Configuration & docs
    print("📄 Configuration & Documentation:")
    doc_files = [
        ("config.yaml", "Main configuration"),
        ("requirements.txt", "Python dependencies"),
        ("README.md", "Main documentation"),
        ("QUICKSTART.md", "Quick start guide"),
        ("PROJECT_SUMMARY.md", "Project summary"),
        ("pytest.ini", "Pytest configuration"),
        (".gitignore", "Git ignore rules"),
    ]
    for file, desc in doc_files:
        all_good &= check_file(file, desc)
    print()
    
    # Scripts
    print("🔧 Scripts:")
    script_files = [
        ("main.py", "Bot entry point"),
        ("setup.sh", "Setup script"),
        ("run.sh", "Run script"),
        ("scripts/check_status.py", "Status checker"),
    ]
    for file, desc in script_files:
        all_good &= check_file(file, desc)
    print()
    
    # Check line counts
    print("📊 Code Statistics:")
    try:
        import subprocess
        result = subprocess.run(
            ["find", "src", "-name", "*.py", "-exec", "wc", "-l", "{}", "+"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            if lines:
                total_line = lines[-1]
                total_count = total_line.strip().split()[0]
                print(f"   Source code: {total_count} lines")
        
        result = subprocess.run(
            ["find", "tests", "-name", "*.py", "-exec", "wc", "-l", "{}", "+"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            if lines:
                total_line = lines[-1]
                total_count = total_line.strip().split()[0]
                print(f"   Test code: {total_count} lines")
    except:
        pass
    print()
    
    # Summary
    print("=" * 70)
    if all_good:
        print("✅ PROJECT COMPLETE - All files present!")
        print()
        print("Next steps:")
        print("1. Run: ./setup.sh (install dependencies)")
        print("2. Configure IB Gateway on port 5000")
        print("3. Review config.yaml")
        print("4. Run: ./run.sh (start bot)")
    else:
        print("❌ Some files are missing - please check above")
    print("=" * 70)

if __name__ == "__main__":
    main()

