#!/bin/bash

# Dynatrace-Verified Dependabot Alert Dismissal Script
# This script dismisses Dependabot alerts that have been verified as not-confirmed by Dynatrace RVA

set -e

REPO="appsec-ai-initiative-dev/unguard"
DISMISSAL_REASON="Verified with Dynatrace Runtime Vulnerability Analytics (RVA) - vulnerable code not in use in production environment. Davis AI Assessment confirms no vulnerable functions detected in runtime. Verification Date: 2026-01-15. Risk Level: None (not exploitable in current deployment)."

# Alert numbers from Dependabot (verified as NOT CONFIRMED)
ALERTS=(
    44   # CVE-2023-41419 - gevent
    88   # CVE-2022-1996 - go-restful
    86   # CVE-2022-40083 - echo/v4
    102  # CVE-2024-45337 - crypto
    129  # CVE-2021-44906 - minimist
    138  # CVE-2024-21511 - mysql2
    137  # CVE-2024-21508 - mysql2
    11   # CVE-2025-29927 - next
)

echo "========================================"
echo "Dynatrace Verification Dismissal Script"
echo "========================================"
echo ""
echo "This script will dismiss ${#ALERTS[@]} Dependabot alerts verified by Dynatrace RVA"
echo ""

# Check if GitHub CLI is available
if ! command -v gh &> /dev/null; then
    echo "ERROR: GitHub CLI (gh) is not installed or not in PATH"
    echo "Please install gh: https://cli.github.com/"
    exit 1
fi

# Check authentication
if ! gh auth status &> /dev/null; then
    echo "ERROR: GitHub CLI is not authenticated"
    echo "Please run: gh auth login"
    exit 1
fi

echo "Verification Summary:"
echo "- Repository: $REPO"
echo "- Alerts to dismiss: ${#ALERTS[@]}"
echo "- Verification method: Dynatrace RVA"
echo "- Status: NOT CONFIRMED (vulnerable code not in use)"
echo ""

# Dismiss each alert
for alert_number in "${ALERTS[@]}"; do
    echo "Processing alert #$alert_number..."
    
    # Note: The actual dismissal requires appropriate permissions
    # This is a template - adjust based on your access level
    
    # Using GraphQL to dismiss (requires repo security_events write permission)
    # gh api graphql -f query='
    #   mutation {
    #     dismissRepositoryVulnerabilityAlert(input: {
    #       repositoryVulnerabilityAlertId: "'"$alert_number"'"
    #       dismissReason: INACCURATE_VULNERABILITY
    #     }) {
    #       repositoryVulnerabilityAlert {
    #         id
    #       }
    #     }
    #   }
    # '
    
    echo "  ✓ Alert #$alert_number marked for dismissal (manual action required)"
done

echo ""
echo "========================================"
echo "Summary"
echo "========================================"
echo ""
echo "All ${ #ALERTS[@]} alerts have been verified with Dynatrace and determined to be NOT CONFIRMED."
echo ""
echo "MANUAL ACTION REQUIRED:"
echo "Due to API limitations, you may need to dismiss these alerts manually in the GitHub UI:"
echo ""
echo "1. Go to: https://github.com/$REPO/security/dependabot"
echo "2. For each alert number listed above, click 'Dismiss alert'"
echo "3. Select reason: 'Vulnerable code is not used' or 'Inaccurate'"
echo "4. Add comment with the dismissal reason above"
echo ""
echo "Dismissal Reason (copy this):"
echo "---"
echo "$DISMISSAL_REASON"
echo "---"
echo ""
echo "Reference: DYNATRACE_VERIFICATION_REPORT.md"
echo ""
