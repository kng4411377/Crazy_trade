#!/bin/bash
# Update Config Helper Script
#
# Helps you merge new features from config.yaml.example into your local config.yaml

set -e

echo "🔄 Config Update Helper"
echo ""

# Check if files exist
if [ ! -f "config.yaml.example" ]; then
    echo "❌ config.yaml.example not found!"
    exit 1
fi

if [ ! -f "config.yaml" ]; then
    echo "📝 No existing config.yaml found. Creating from template..."
    cp config.yaml.example config.yaml
    echo "✅ config.yaml created! Please customize it."
    exit 0
fi

# Show differences
echo "📊 Comparing your config.yaml with the latest template..."
echo ""
echo "Legend:"
echo "  Lines starting with '-' are in your config"
echo "  Lines starting with '+' are new in the template"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Use diff to show differences (ignore comments for clarity)
if diff -u config.yaml config.yaml.example > /tmp/config_diff.txt; then
    echo "✅ Your config is already up to date!"
    exit 0
else
    # Show the diff with color if possible
    if command -v colordiff &> /dev/null; then
        cat /tmp/config_diff.txt | colordiff | head -100
    else
        cat /tmp/config_diff.txt | head -100
    fi
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🔧 Options to update your config:"
    echo ""
    echo "1. Manual merge (recommended):"
    echo "   - Review the differences above"
    echo "   - Edit config.yaml and add new fields you want"
    echo "   - Keep your existing values (watchlist, allocation, etc.)"
    echo ""
    echo "2. Visual merge with editor:"
    if command -v code &> /dev/null; then
        echo "   code --diff config.yaml config.yaml.example"
    fi
    if command -v vimdiff &> /dev/null; then
        echo "   vimdiff config.yaml config.yaml.example"
    fi
    echo ""
    echo "3. Backup and recreate:"
    echo "   cp config.yaml config.yaml.backup"
    echo "   cp config.yaml.example config.yaml"
    echo "   # Then manually copy your settings from config.yaml.backup"
    echo ""
    echo "4. Quick add missing fields:"
    echo "   ./update_config.sh --auto-merge (⚠️  experimental)"
    echo ""
fi

# Check for --auto-merge flag
if [ "$1" = "--auto-merge" ]; then
    echo "🤖 Attempting auto-merge..."
    echo ""
    
    # Backup existing config
    cp config.yaml config.yaml.backup
    echo "✅ Backed up to config.yaml.backup"
    
    # Check for new fields in example that don't exist in current config
    NEW_FIELDS=$(grep -E "^  [a-z_]+:" config.yaml.example | while read line; do
        field=$(echo "$line" | cut -d: -f1 | xargs)
        if ! grep -q "^  $field:" config.yaml 2>/dev/null; then
            echo "$field"
        fi
    done)
    
    if [ -n "$NEW_FIELDS" ]; then
        echo ""
        echo "📝 New fields found:"
        echo "$NEW_FIELDS" | sed 's/^/  - /'
        echo ""
        echo "⚠️  Please manually add these to your config.yaml by reviewing config.yaml.example"
    else
        echo "✅ No new top-level fields detected"
    fi
    
    echo ""
    echo "💡 Tip: Review config.yaml.example for new sub-fields and features"
fi

echo ""
echo "📚 New features in this version:"
echo "  - entry_price_strategy: Use SMA or opening price for entries"
echo "  - sma_periods: Configure SMA calculation period"
echo "  - tif: Configurable time-in-force for orders"
echo ""
echo "See config.yaml.example for details and comments"
echo ""

