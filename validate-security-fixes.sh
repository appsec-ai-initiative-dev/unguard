#!/bin/bash
# Validation script for Unguard frontend security fixes
# This script verifies that the security fixes have been properly applied

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/src/frontend-nextjs"

echo "🔍 Unguard Frontend Security Validation"
echo "========================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}❌ Error: Frontend directory not found at $FRONTEND_DIR${NC}"
    exit 1
fi

cd "$FRONTEND_DIR"

echo "📦 Checking package.json versions..."
echo ""

# Function to check package version
check_version() {
    local package=$1
    local expected=$2
    local actual=$(grep "\"$package\":" package.json | sed 's/.*":  *"//;s/".*//' | tr -d ' ')
    
    if [ "$actual" == "$expected" ]; then
        echo -e "${GREEN}✅ $package: $actual${NC}"
        return 0
    else
        echo -e "${RED}❌ $package: Expected $expected, got $actual${NC}"
        return 1
    fi
}

# Check critical package versions
ALL_GOOD=true

check_version "axios" "1.12.2" || ALL_GOOD=false
check_version "next" "15.5.5" || ALL_GOOD=false
check_version "swagger-ui-react" "5.29.4" || ALL_GOOD=false
check_version "@next/eslint-plugin-next" "15.5.5" || ALL_GOOD=false
check_version "eslint-config-next" "15.5.5" || ALL_GOOD=false

echo ""
echo "📋 Checking documentation..."
echo ""

# Check if documentation files exist
DOCS=(
    "SECURITY_ADVISORY.md"
    "SECURITY_FIX_NOTES.md"
    "VULNERABILITY_INVESTIGATION_REPORT.md"
    "VULNERABILITY_REMEDIATION_PLAN.md"
    "VULNERABILITY_QUICK_REFERENCE.md"
    "EXECUTIVE_SUMMARY.md"
)

cd "$SCRIPT_DIR"

for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        echo -e "${GREEN}✅ $doc exists${NC}"
    else
        echo -e "${RED}❌ $doc missing${NC}"
        ALL_GOOD=false
    fi
done

echo ""
echo "🔐 Checking .npmrc configuration..."
echo ""

cd "$FRONTEND_DIR"

if grep -q "@ctrl:registry=http://127.0.0.1:4873" .npmrc; then
    echo -e "${GREEN}✅ Verdaccio configuration present for @ctrl scope${NC}"
else
    echo -e "${YELLOW}⚠️  Verdaccio configuration not found - @ctrl/tinycolor demo may not work${NC}"
fi

echo ""
echo "📝 Summary"
echo "=========="
echo ""

if [ "$ALL_GOOD" = true ]; then
    echo -e "${GREEN}✅ All security fixes validated successfully!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Start Verdaccio: npx verdaccio --config ops/verdaccio/config.yaml"
    echo "2. Publish safe simulation: node ops/verdaccio/publish-tinycolor.js"
    echo "3. Install dependencies: cd src/frontend-nextjs && npm install"
    echo "4. Build application: npm run build"
    echo ""
    echo "See SECURITY_ADVISORY.md for detailed instructions."
    exit 0
else
    echo -e "${RED}❌ Some validations failed. Please review the output above.${NC}"
    exit 1
fi
