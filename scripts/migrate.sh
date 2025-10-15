#!/bin/bash

# Configuration Migration Script
# Migrates legacy configuration to multi-domain format

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo -e "${BLUE}🔄 Dashboard Configuration Migration${NC}"
echo "=================================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is required but not installed${NC}"
    exit 1
fi

# Check if backend directory exists
if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}❌ Backend directory not found: $BACKEND_DIR${NC}"
    exit 1
fi

# Change to backend directory
cd "$BACKEND_DIR"

# Check if migration module exists
if [ ! -f "config_migration.py" ]; then
    echo -e "${RED}❌ Migration module not found: config_migration.py${NC}"
    exit 1
fi

# Function to run migration commands
run_migration_command() {
    local command=$1
    local description=$2
    
    echo -e "\n${YELLOW}$description${NC}"
    echo "----------------------------------------"
    
    if python3 config_migration.py "$command"; then
        echo -e "${GREEN}✅ Command completed successfully${NC}"
    else
        echo -e "${RED}❌ Command failed${NC}"
        return 1
    fi
}

# Parse command line arguments
case "${1:-}" in
    "detect")
        run_migration_command "--detect" "🔍 Detecting legacy configurations"
        ;;
    "validate")
        run_migration_command "--validate" "✅ Validating Desktop compatibility"
        ;;
    "report")
        run_migration_command "--report" "📋 Generating migration report"
        ;;
    "migrate")
        echo -e "\n${YELLOW}🚀 Starting automatic migration${NC}"
        echo "----------------------------------------"
        
        # First show what will be migrated
        echo -e "\n${BLUE}📋 Current status:${NC}"
        python3 config_migration.py --report
        
        echo -e "\n${YELLOW}❓ Do you want to proceed with migration? (y/N):${NC} "
        read -r response
        
        if [[ "$response" =~ ^[Yy]([Ee][Ss])?$ ]]; then
            run_migration_command "--migrate" "🔄 Performing migration"
            
            if [ $? -eq 0 ]; then
                echo -e "\n${GREEN}🎉 Migration completed successfully!${NC}"
                echo -e "${BLUE}📖 Next steps:${NC}"
                echo "  1. Review the generated domains.json file"
                echo "  2. Test your application with: ./scripts/dev.sh"
                echo "  3. Add additional domains as needed"
            fi
        else
            echo -e "${YELLOW}Migration cancelled${NC}"
        fi
        ;;
    "interactive")
        # Interactive migration using Python script
        python3 "$SCRIPT_DIR/migrate_config.py"
        ;;
    *)
        echo -e "${BLUE}Usage: $0 {detect|validate|report|migrate|interactive}${NC}"
        echo ""
        echo "Commands:"
        echo "  detect      - Detect legacy configurations"
        echo "  validate    - Validate Desktop compatibility"
        echo "  report      - Generate detailed migration report"
        echo "  migrate     - Perform automatic migration"
        echo "  interactive - Run interactive migration wizard"
        echo ""
        echo "Examples:"
        echo "  $0 report    # Show current status"
        echo "  $0 migrate   # Migrate legacy configuration"
        echo "  $0 interactive # Run interactive wizard"
        exit 1
        ;;
esac