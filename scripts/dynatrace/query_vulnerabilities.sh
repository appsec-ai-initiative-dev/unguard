#!/bin/bash
#
# Dynatrace Vulnerability Query Script (Shell Wrapper)
#
# This script provides a convenient shell wrapper for querying Dynatrace vulnerabilities.
# It can use either curl directly or the Python script for more advanced queries.
#
# Usage:
#   ./query_vulnerabilities.sh [OPTIONS]
#
# Environment Variables:
#   DT_ENVIRONMENT: Dynatrace environment URL
#   DT_API_TOKEN: Dynatrace API token
#
# Examples:
#   # Query all vulnerabilities
#   ./query_vulnerabilities.sh
#
#   # Query CRITICAL vulnerabilities only
#   ./query_vulnerabilities.sh --severity CRITICAL
#
#   # Use Python script for advanced queries
#   ./query_vulnerabilities.sh --use-python --function-in-use
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
USE_PYTHON=false
DAYS=7
SEVERITY=""
FUNCTION_IN_USE=false
CVE=""
FORMAT="table"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --use-python)
            USE_PYTHON=true
            shift
            ;;
        --severity)
            SEVERITY="$2"
            shift 2
            ;;
        --days)
            DAYS="$2"
            shift 2
            ;;
        --function-in-use)
            FUNCTION_IN_USE=true
            shift
            ;;
        --cve)
            CVE="$2"
            shift 2
            ;;
        --format)
            FORMAT="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --use-python          Use Python script instead of curl"
            echo "  --severity LEVEL      Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)"
            echo "  --days N              Look back N days (default: 7)"
            echo "  --function-in-use     Show only vulnerabilities with function in use"
            echo "  --cve CVE-XXXX-XXXX   Look up specific CVE"
            echo "  --format FORMAT       Output format: table, json, summary (default: table)"
            echo "  --help, -h            Show this help message"
            echo ""
            echo "Environment Variables:"
            echo "  DT_ENVIRONMENT        Dynatrace environment URL (required)"
            echo "  DT_API_TOKEN          Dynatrace API token (required)"
            exit 0
            ;;
        *)
            echo -e "${RED}Error: Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Check required environment variables
if [ -z "$DT_ENVIRONMENT" ]; then
    echo -e "${RED}Error: DT_ENVIRONMENT environment variable is not set${NC}"
    echo "Set it with: export DT_ENVIRONMENT=https://your-environment.live.dynatrace.com"
    exit 1
fi

if [ -z "$DT_API_TOKEN" ]; then
    echo -e "${RED}Error: DT_API_TOKEN environment variable is not set${NC}"
    echo "Set it with: export DT_API_TOKEN=your-api-token"
    exit 1
fi

# Use Python script if requested or if advanced options are used
if [ "$USE_PYTHON" = true ] || [ "$FUNCTION_IN_USE" = true ] || [ -n "$CVE" ]; then
    echo -e "${BLUE}Using Python script for query...${NC}"
    
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    PYTHON_SCRIPT="$SCRIPT_DIR/query_vulnerabilities.py"
    
    if [ ! -f "$PYTHON_SCRIPT" ]; then
        echo -e "${RED}Error: Python script not found at $PYTHON_SCRIPT${NC}"
        exit 1
    fi
    
    # Check if Python 3 is available
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python 3 is required but not found${NC}"
        exit 1
    fi
    
    # Check if requests library is available
    if ! python3 -c "import requests" &> /dev/null; then
        echo -e "${YELLOW}Warning: Python 'requests' library not found${NC}"
        echo -e "${YELLOW}Installing requests...${NC}"
        pip3 install requests || {
            echo -e "${RED}Error: Failed to install requests library${NC}"
            exit 1
        }
    fi
    
    # Build Python command
    CMD="python3 $PYTHON_SCRIPT --days $DAYS --format $FORMAT"
    
    if [ -n "$SEVERITY" ]; then
        CMD="$CMD --severity $SEVERITY"
    fi
    
    if [ "$FUNCTION_IN_USE" = true ]; then
        CMD="$CMD --function-in-use"
    fi
    
    if [ -n "$CVE" ]; then
        CMD="$CMD --cve $CVE"
    fi
    
    # Execute Python script
    eval "$CMD"
    
else
    # Use curl for simple queries
    echo -e "${BLUE}Querying Dynatrace for vulnerabilities (last $DAYS days)...${NC}"
    
    # Build DQL query
    DQL_QUERY="fetch security.events, from:now()-${DAYS}d
| filter dt.system.bucket==\"default_securityevents_builtin\"
     AND event.provider==\"Dynatrace\"
     AND event.type==\"VULNERABILITY_STATE_REPORT_EVENT\"
     AND event.level==\"ENTITY\"
| dedup {vulnerability.display_id, affected_entity.id}, sort:{timestamp desc}
| filter vulnerability.resolution.status == \"OPEN\"
     AND vulnerability.parent.mute.status != \"MUTED\"
     AND vulnerability.mute.status != \"MUTED\""
    
    if [ -n "$SEVERITY" ]; then
        DQL_QUERY="$DQL_QUERY
| summarize{
    vulnerability.risk.score=round(takeMax(vulnerability.risk.score),decimals:1),
    vulnerability.title=takeFirst(vulnerability.title),
    vulnerability.references.cve=takeFirst(vulnerability.references.cve),
    last_detected=coalesce(takeMax(vulnerability.resolution.change_date),takeMax(vulnerability.parent.first_seen)),
    affected_entities=countDistinctExact(affected_entity.id)
}, by: {vulnerability.display_id}
| fieldsAdd vulnerability.risk.level=if(vulnerability.risk.score>=9,\"CRITICAL\",
                                     else:if(vulnerability.risk.score>=7,\"HIGH\",
                                     else:if(vulnerability.risk.score>=4,\"MEDIUM\",
                                     else:if(vulnerability.risk.score>=0.1,\"LOW\",
                                     else:\"NONE\"))))
| filter vulnerability.risk.level == \"$SEVERITY\"
| sort {vulnerability.risk.score, direction:\"descending\"}"
    else
        DQL_QUERY="$DQL_QUERY
| summarize{
    vulnerability.risk.score=round(takeMax(vulnerability.risk.score),decimals:1),
    vulnerability.title=takeFirst(vulnerability.title),
    vulnerability.references.cve=takeFirst(vulnerability.references.cve),
    last_detected=coalesce(takeMax(vulnerability.resolution.change_date),takeMax(vulnerability.parent.first_seen)),
    affected_entities=countDistinctExact(affected_entity.id),
    vulnerable_function_in_use=if(in(\"IN_USE\",collectArray(vulnerability.davis_assessment.vulnerable_function_status)),true, else:false),
    public_internet_exposure=if(in(\"PUBLIC_NETWORK\",collectArray(vulnerability.davis_assessment.exposure_status)),true,else:false),
    public_exploit_available=if(in(\"AVAILABLE\",collectArray(vulnerability.davis_assessment.exploit_status)),true,else:false)
}, by: {vulnerability.display_id}
| fieldsAdd vulnerability.risk.level=if(vulnerability.risk.score>=9,\"CRITICAL\",
                                     else:if(vulnerability.risk.score>=7,\"HIGH\",
                                     else:if(vulnerability.risk.score>=4,\"MEDIUM\",
                                     else:if(vulnerability.risk.score>=0.1,\"LOW\",
                                     else:\"NONE\"))))
| sort {vulnerability.risk.score, direction:\"descending\"}, {affected_entities, direction:\"descending\"}"
    fi
    
    # Execute query
    RESPONSE=$(curl -s -X POST \
        "${DT_ENVIRONMENT}/api/v2/query:execute" \
        -H "Authorization: Api-Token ${DT_API_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "{\"query\": \"$DQL_QUERY\"}")
    
    # Check for errors
    if echo "$RESPONSE" | grep -q '"error"'; then
        echo -e "${RED}Error executing query:${NC}"
        echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
        exit 1
    fi
    
    # Format output based on requested format
    if [ "$FORMAT" = "json" ]; then
        echo "$RESPONSE" | python3 -m json.tool
    else
        # Parse and display results in table format
        echo ""
        echo "==============================================================================="
        echo "DYNATRACE RUNTIME VULNERABILITY ANALYTICS - LATEST VULNERABILITIES"
        echo "==============================================================================="
        echo ""
        
        # Extract and count records
        RECORD_COUNT=$(echo "$RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data.get('result', {}).get('records', [])))" 2>/dev/null || echo "0")
        
        if [ "$RECORD_COUNT" -eq 0 ]; then
            echo "No vulnerabilities found."
        else
            echo "$RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
records = data.get('result', {}).get('records', [])
for idx, record in enumerate(records, 1):
    print(f\"[{idx}] {record.get('vulnerability.display_id', 'N/A')}\")
    print(f\"    Title: {record.get('vulnerability.title', 'N/A')}\")
    cve = record.get('vulnerability.references.cve', [])
    if cve:
        cve_list = cve if isinstance(cve, list) else [cve]
        print(f\"    CVE: {', '.join(cve_list)}\")
    risk_level = record.get('vulnerability.risk.level', 'N/A')
    risk_score = record.get('vulnerability.risk.score', 'N/A')
    print(f\"    Risk: {risk_level} (Score: {risk_score})\")
    print(f\"    Affected Entities: {record.get('affected_entities', 0)}\")
    if 'vulnerable_function_in_use' in record:
        func_in_use = '✓ YES' if record.get('vulnerable_function_in_use') else '✗ NO'
        print(f\"    Vulnerable Function In Use: {func_in_use}\")
    print()
" 2>/dev/null || echo "$RESPONSE" | python3 -m json.tool
            
            echo "==============================================================================="
            echo "Total: $RECORD_COUNT vulnerabilities"
            echo "==============================================================================="
        fi
        echo ""
    fi
fi

echo -e "${GREEN}Query completed successfully${NC}"
