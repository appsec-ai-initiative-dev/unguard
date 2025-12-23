#!/bin/bash
# ==============================================================================
# Dynatrace Vulnerability Retrieval Script (Shell Wrapper)
# ==============================================================================
# This script provides a convenient wrapper around the Python vulnerability
# retrieval tool with common preset configurations.
#
# Requirements:
#   - Python 3.7+
#   - requests library (pip install requests)
#   - DT_TENANT environment variable
#   - DT_API_TOKEN environment variable
#
# Usage:
#   ./get-vulnerabilities.sh [preset] [additional-args]
#
# Presets:
#   all             - Get all vulnerabilities (default)
#   critical        - Get CRITICAL and HIGH severity only
#   priority        - Get vulnerabilities with function in use
#   recent          - Get vulnerabilities from last 24 hours
#   summary         - Get markdown summary report
#
# Examples:
#   ./get-vulnerabilities.sh
#   ./get-vulnerabilities.sh critical
#   ./get-vulnerabilities.sh priority --format markdown
#   ./get-vulnerabilities.sh all --output report.json
# ==============================================================================

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/get_vulnerabilities.py"

# Check if Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: Python script not found at $PYTHON_SCRIPT" >&2
    exit 1
fi

# Check environment variables
if [ -z "$DT_TENANT" ]; then
    echo "Error: DT_TENANT environment variable not set" >&2
    echo "Example: export DT_TENANT=https://abc12345.live.dynatrace.com" >&2
    exit 1
fi

if [ -z "$DT_API_TOKEN" ]; then
    echo "Error: DT_API_TOKEN environment variable not set" >&2
    echo "Example: export DT_API_TOKEN=dt0c01.XXXXXXXX..." >&2
    exit 1
fi

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found" >&2
    exit 1
fi

# Parse preset (first argument)
PRESET="${1:-all}"
shift || true

# Define preset configurations
case "$PRESET" in
    all)
        echo "==> Getting all vulnerabilities..." >&2
        python3 "$PYTHON_SCRIPT" --days 7 "$@"
        ;;
    
    critical)
        echo "==> Getting CRITICAL and HIGH severity vulnerabilities..." >&2
        python3 "$PYTHON_SCRIPT" --severity CRITICAL,HIGH --days 7 "$@"
        ;;
    
    priority)
        echo "==> Getting high-priority vulnerabilities (function in use)..." >&2
        python3 "$PYTHON_SCRIPT" --severity CRITICAL,HIGH --function-in-use --days 7 "$@"
        ;;
    
    recent)
        echo "==> Getting vulnerabilities from last 24 hours..." >&2
        python3 "$PYTHON_SCRIPT" --days 1 "$@"
        ;;
    
    summary)
        echo "==> Generating vulnerability summary report..." >&2
        python3 "$PYTHON_SCRIPT" --format markdown --days 7 "$@"
        ;;
    
    exploitable)
        echo "==> Getting exploitable vulnerabilities (public exploits + function in use)..." >&2
        python3 "$PYTHON_SCRIPT" --severity CRITICAL,HIGH --function-in-use --days 7 "$@"
        ;;
    
    help|--help|-h)
        cat >&2 << 'EOF'
Dynatrace Vulnerability Retrieval Script

Usage: ./get-vulnerabilities.sh [preset] [additional-args]

Presets:
  all             Get all vulnerabilities (default)
  critical        Get CRITICAL and HIGH severity only
  priority        Get vulnerabilities with function in use
  recent          Get vulnerabilities from last 24 hours
  summary         Get markdown summary report
  exploitable     Get exploitable vulnerabilities (public exploits + function in use)
  help            Show this help message

Additional Arguments:
  --format FORMAT       Output format: json, csv, markdown (default: json)
  --severity SEVERITIES Comma-separated severities: CRITICAL,HIGH,MEDIUM,LOW
  --function-in-use     Filter for vulnerabilities where function is in use
  --cve CVE            Filter by specific CVE (e.g., CVE-2024-12345)
  --entity ID          Filter by specific entity ID
  --days N             Number of days to look back (default: 7)
  --output FILE        Output to file instead of stdout

Environment Variables:
  DT_TENANT      Dynatrace tenant URL (required)
  DT_API_TOKEN   Dynatrace API token with 'storage:events:read' scope (required)

Examples:
  # Get all vulnerabilities as JSON
  ./get-vulnerabilities.sh all

  # Get critical vulnerabilities as CSV
  ./get-vulnerabilities.sh critical --format csv

  # Get priority vulnerabilities as Markdown report
  ./get-vulnerabilities.sh priority --format markdown --output report.md

  # Get vulnerabilities for specific CVE
  ./get-vulnerabilities.sh all --cve CVE-2024-12345

  # Get vulnerabilities from last 30 days
  ./get-vulnerabilities.sh all --days 30

  # Get summary report and save to file
  ./get-vulnerabilities.sh summary --output vulnerabilities.md
EOF
        exit 0
        ;;
    
    *)
        echo "Error: Unknown preset '$PRESET'" >&2
        echo "Run './get-vulnerabilities.sh help' for usage information" >&2
        exit 1
        ;;
esac
