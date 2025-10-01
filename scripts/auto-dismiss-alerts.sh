#!/bin/bash

# Wrapper script to dismiss Dependabot alerts using COPILOT_SPONSOR_PAT_VALERIY
# This script attempts to use the PAT token if available

set -e

echo "🔍 Checking for available GitHub tokens..."

# Check for the specific PAT mentioned in the comment
if [ -n "$COPILOT_SPONSOR_PAT_VALERIY" ]; then
    echo "✅ Found COPILOT_SPONSOR_PAT_VALERIY token"
    export GITHUB_TOKEN="$COPILOT_SPONSOR_PAT_VALERIY"
    echo "🚀 Attempting to dismiss Dependabot alerts..."
    exec "$(dirname "$0")/dismiss-dependabot-alerts.sh"
elif [ -n "$GITHUB_TOKEN" ]; then
    echo "✅ Found GITHUB_TOKEN"
    echo "🚀 Attempting to dismiss Dependabot alerts..."
    exec "$(dirname "$0")/dismiss-dependabot-alerts.sh"
else
    echo "❌ No suitable GitHub token found"
    echo ""
    echo "Please set one of the following environment variables:"
    echo "  - COPILOT_SPONSOR_PAT_VALERIY (preferred)"
    echo "  - GITHUB_TOKEN"
    echo ""
    echo "The token must have 'security_events' scope to dismiss Dependabot alerts"
    echo ""
    echo "Usage examples:"
    echo "  export COPILOT_SPONSOR_PAT_VALERIY=\"your_token_here\" && $0"
    echo "  export GITHUB_TOKEN=\"your_token_here\" && $0"
    exit 1
fi