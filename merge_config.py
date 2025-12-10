#!/usr/bin/env python3
"""
Smart Config Merger - Preserves your settings while adding new features
"""

import sys
import yaml
from pathlib import Path
from typing import Dict, Any, Set


def load_yaml(filepath: Path) -> Dict[str, Any]:
    """Load YAML file."""
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)


def save_yaml(filepath: Path, data: Dict[str, Any]):
    """Save YAML file."""
    with open(filepath, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, indent=2)


def find_new_keys(template: Dict, current: Dict, prefix: str = "") -> Set[str]:
    """Find keys that exist in template but not in current config."""
    new_keys = set()
    
    for key, value in template.items():
        full_key = f"{prefix}.{key}" if prefix else key
        
        if key not in current:
            new_keys.add(full_key)
        elif isinstance(value, dict) and isinstance(current.get(key), dict):
            # Recursively check nested dictionaries
            nested_new = find_new_keys(value, current[key], full_key)
            new_keys.update(nested_new)
    
    return new_keys


def merge_configs(template: Dict, current: Dict) -> Dict[str, Any]:
    """
    Merge template into current config, preserving current values.
    Adds new keys from template with their default values.
    """
    merged = current.copy()
    
    for key, template_value in template.items():
        if key not in merged:
            # New key - add it with template's default
            merged[key] = template_value
            print(f"  ✅ Added new field: {key}")
        elif isinstance(template_value, dict) and isinstance(merged[key], dict):
            # Both are dicts - merge recursively
            merged[key] = merge_configs(template_value, merged[key])
    
    return merged


def main():
    """Main entry point."""
    print("🔄 Smart Config Merger")
    print("━" * 50)
    print()
    
    # Paths
    current_path = Path("config.yaml")
    template_path = Path("config.yaml.example")
    backup_path = Path("config.yaml.backup")
    
    # Check files exist
    if not template_path.exists():
        print("❌ config.yaml.example not found!")
        sys.exit(1)
    
    if not current_path.exists():
        print("📝 No existing config.yaml found.")
        print("   Creating from template...")
        template_path.read_text()
        current_path.write_text(template_path.read_text())
        print("✅ config.yaml created! Please customize it.")
        sys.exit(0)
    
    # Load configs
    print("📖 Loading configurations...")
    try:
        current = load_yaml(current_path)
        template = load_yaml(template_path)
    except Exception as e:
        print(f"❌ Error loading YAML: {e}")
        sys.exit(1)
    
    # Find new keys
    print("🔍 Analyzing differences...")
    new_keys = find_new_keys(template, current)
    
    if not new_keys:
        print("✅ Your config is up to date! No new fields to add.")
        sys.exit(0)
    
    # Show new keys
    print()
    print(f"📝 Found {len(new_keys)} new field(s):")
    for key in sorted(new_keys):
        print(f"  • {key}")
    print()
    
    # Ask for confirmation
    response = input("🤔 Merge new fields into your config? (y/n): ").strip().lower()
    
    if response != 'y':
        print("❌ Merge cancelled.")
        print()
        print("💡 To review changes manually:")
        print("   ./update_config.sh")
        sys.exit(0)
    
    # Backup current config
    print()
    print("💾 Creating backup...")
    backup_path.write_text(current_path.read_text())
    print(f"   ✅ Backed up to {backup_path}")
    
    # Merge configs
    print()
    print("🔧 Merging configurations...")
    merged = merge_configs(template, current)
    
    # Save merged config
    save_yaml(current_path, merged)
    
    print()
    print("━" * 50)
    print("✅ Config updated successfully!")
    print()
    print("📋 Next steps:")
    print("  1. Review config.yaml for new fields")
    print("  2. Customize new settings as needed")
    print("  3. Check config.yaml.example for detailed comments")
    print()
    print("💡 New features in this version:")
    print("  • entry_price_strategy - Use SMA or opening price")
    print("  • sma_periods - Configure SMA period")
    print("  • tif - Configurable time-in-force")
    print()
    print(f"🔙 Rollback available at: {backup_path}")
    print()


if __name__ == "__main__":
    main()

