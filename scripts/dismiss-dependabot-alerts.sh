#!/bin/bash

# Script to dismiss Dependabot alerts using GitHub API
# Requires: GITHUB_TOKEN environment variable with security_events scope

set -e

OWNER="appsec-ai-initiative-dev"
REPO="unguard"
REASON="vulnerable_code_not_actually_used"
COMMENT="Library was not observed in the monitored environment by Dynatrace Runtime Vulnerability Analytics (RVA)"

# Alerts to dismiss based on Dynatrace analysis
ALERTS_TO_DISMISS=(44 88 86 102 129)

# Alert details for logging
declare -A ALERT_DETAILS
ALERT_DETAILS[44]="CVE-2023-41419 (gevent) - malicious-load-generator not deployed"
ALERT_DETAILS[88]="CVE-2022-1996 (go-restful) - not detected by Dynatrace RVA"
ALERT_DETAILS[86]="CVE-2022-40083 (echo/v4) - not detected by Dynatrace RVA"
ALERT_DETAILS[102]="CVE-2024-45337 (golang.org/x/crypto) - not detected by Dynatrace RVA"
ALERT_DETAILS[129]="CVE-2021-44906 (minimist) - not detected by Dynatrace RVA"

if [ -z "$GITHUB_TOKEN" ]; then
    echo "Error: GITHUB_TOKEN environment variable is required"
    echo "The token needs 'security_events' scope to dismiss Dependabot alerts"
    echo "Usage: GITHUB_TOKEN=your_token_here $0"
    exit 1
fi

echo "🔐 Dismissing Dependabot alerts not confirmed by Dynatrace RVA..."
echo "Repository: $OWNER/$REPO"
echo "Reason: $REASON"
echo ""

success_count=0

for alert_id in "${ALERTS_TO_DISMISS[@]}"; do
    echo "📝 Dismissing alert #$alert_id: ${ALERT_DETAILS[$alert_id]}"
    
    # GitHub API call to dismiss the alert
    response=$(curl -s -w "%{http_code}" -o /tmp/response_${alert_id}.json \
        -X PATCH \
        -H "Accept: application/vnd.github+json" \
        -H "Authorization: Bearer $GITHUB_TOKEN" \
        -H "X-GitHub-Api-Version: 2022-11-28" \
        "https://api.github.com/repos/$OWNER/$REPO/dependabot/alerts/$alert_id" \
        -d "{
            \"state\": \"dismissed\",
            \"dismissed_reason\": \"$REASON\",
            \"dismissed_comment\": \"$COMMENT\"
        }")
    
    # Extract HTTP status code
    http_code="${response: -3}"
    
    if [ "$http_code" = "200" ]; then
        echo "✅ Successfully dismissed alert #$alert_id"
        ((success_count++))
    else
        echo "❌ Failed to dismiss alert #$alert_id (HTTP $http_code)"
        if [ -f "/tmp/response_${alert_id}.json" ]; then
            echo "Response: $(cat /tmp/response_${alert_id}.json)"
        fi
    fi
    echo ""
done

echo "🎯 Summary: Successfully dismissed $success_count/${#ALERTS_TO_DISMISS[@]} alerts"
echo "These alerts were identified as non-applicable through Dynatrace Runtime Vulnerability Analytics"

# Clean up temporary files
rm -f /tmp/response_*.json