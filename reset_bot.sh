#!/bin/bash
# Convenience script for resetting the trading bot
# See docs/RESET_GUIDE.md for detailed documentation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "======================================================"
echo "  Crazy Trade Bot - Reset Utility"
echo "======================================================"
echo ""
echo "Select reset option:"
echo ""
echo "  1) Reset Alpaca Account Only (close positions & cancel orders)"
echo "  2) Reset Database Only (clear all historical data)"
echo "  3) Full Reset (account + database)"
echo "  4) Clear Symbol Cooldowns Only"
echo "  5) Export Trades Before Reset"
echo "  0) Cancel"
echo ""
read -p "Enter option (0-5): " option

case $option in
    1)
        echo ""
        echo -e "${BLUE}Resetting Alpaca account (positions & orders)...${NC}"
        python3 scripts/reset_paper_account.py
        ;;
    
    2)
        echo ""
        echo -e "${YELLOW}⚠️  WARNING: This will delete ALL historical data!${NC}"
        echo "   - All order records"
        echo "   - All fill/transaction records"
        echo "   - All performance snapshots"
        echo "   - All symbol states and cooldowns"
        echo ""
        read -p "Are you sure? (yes/no): " confirm
        
        if [ "$confirm" = "yes" ]; then
            if [ -f "bot.db" ]; then
                # Create backup
                backup_name="bot.db.backup.$(date +%Y%m%d_%H%M%S)"
                cp bot.db "$backup_name"
                echo -e "${GREEN}✅ Backup created: $backup_name${NC}"
                
                # Delete database
                rm bot.db
                echo -e "${GREEN}✅ Database deleted${NC}"
                echo ""
                echo "The bot will create a fresh database on next startup."
            else
                echo -e "${YELLOW}ℹ️  No bot.db file found (already clean)${NC}"
            fi
        else
            echo -e "${RED}❌ Aborted${NC}"
        fi
        ;;
    
    3)
        echo ""
        echo -e "${YELLOW}⚠️  WARNING: This is a FULL RESET!${NC}"
        echo "   - Closes all Alpaca positions"
        echo "   - Cancels all Alpaca orders"
        echo "   - Deletes all database records"
        echo ""
        read -p "Are you absolutely sure? (yes/no): " confirm
        
        if [ "$confirm" = "yes" ]; then
            # Step 1: Reset Alpaca account
            echo ""
            echo -e "${BLUE}Step 1/2: Resetting Alpaca account...${NC}"
            python3 scripts/reset_paper_account.py
            
            # Step 2: Delete database
            echo ""
            echo -e "${BLUE}Step 2/2: Deleting database...${NC}"
            if [ -f "bot.db" ]; then
                backup_name="bot.db.backup.$(date +%Y%m%d_%H%M%S)"
                cp bot.db "$backup_name"
                echo -e "${GREEN}✅ Backup created: $backup_name${NC}"
                
                rm bot.db
                echo -e "${GREEN}✅ Database deleted${NC}"
            fi
            
            echo ""
            echo -e "${GREEN}✅ Full reset complete!${NC}"
            echo "The bot will create a fresh database on next startup."
        else
            echo -e "${RED}❌ Aborted${NC}"
        fi
        ;;
    
    4)
        echo ""
        echo -e "${BLUE}Clearing symbol cooldowns...${NC}"
        
        if [ -f "bot.db" ]; then
            sqlite3 bot.db "UPDATE state SET cooldown_until_ts = NULL;"
            count=$(sqlite3 bot.db "SELECT COUNT(*) FROM state WHERE cooldown_until_ts IS NULL;")
            echo -e "${GREEN}✅ Cooldowns cleared for $count symbols${NC}"
        else
            echo -e "${RED}❌ No bot.db file found${NC}"
        fi
        ;;
    
    5)
        echo ""
        echo -e "${BLUE}Exporting trades...${NC}"
        python3 scripts/export_trades.py
        echo ""
        echo "After exporting, you can run this script again to reset."
        ;;
    
    0)
        echo ""
        echo -e "${YELLOW}Cancelled${NC}"
        exit 0
        ;;
    
    *)
        echo ""
        echo -e "${RED}❌ Invalid option${NC}"
        exit 1
        ;;
esac

echo ""
echo "======================================================"
echo "  Reset Complete"
echo "======================================================"
echo ""
echo "Next steps:"
echo "  - Start the bot: ./run.sh"
echo "  - Check status: python scripts/check_status.py"
echo "  - View performance: python scripts/show_performance.py"
echo ""
echo "See docs/RESET_GUIDE.md for detailed documentation."
echo ""

