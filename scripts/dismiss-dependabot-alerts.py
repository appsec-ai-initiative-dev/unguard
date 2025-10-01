#!/usr/bin/env python3
"""
Script to dismiss Dependabot security alerts using GitHub API
Requires: github token with security_events scope

Usage:
    export GITHUB_TOKEN="your_token_here"
    python3 dismiss-dependabot-alerts.py
"""

import os
import sys
import requests
import json

# Configuration
OWNER = "appsec-ai-initiative-dev"
REPO = "unguard"
REASON = "vulnerable_code_not_actually_used"
COMMENT = "Library was not observed in the monitored environment by Dynatrace Runtime Vulnerability Analytics (RVA)"

# Alerts to dismiss based on Dynatrace analysis
ALERTS_TO_DISMISS = [
    {
        "id": 44,
        "description": "CVE-2023-41419 (gevent) - malicious-load-generator not deployed"
    },
    {
        "id": 88,
        "description": "CVE-2022-1996 (go-restful) - not detected by Dynatrace RVA"
    },
    {
        "id": 86,
        "description": "CVE-2022-40083 (echo/v4) - not detected by Dynatrace RVA"
    },
    {
        "id": 102,
        "description": "CVE-2024-45337 (golang.org/x/crypto) - not detected by Dynatrace RVA"
    },
    {
        "id": 129,
        "description": "CVE-2021-44906 (minimist) - not detected by Dynatrace RVA"
    }
]

def dismiss_alert(token, alert_id, description):
    """Dismiss a single Dependabot alert"""
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/dependabot/alerts/{alert_id}"
    
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    data = {
        "state": "dismissed",
        "dismissed_reason": REASON,
        "dismissed_comment": COMMENT
    }
    
    print(f"📝 Dismissing alert #{alert_id}: {description}")
    
    try:
        response = requests.patch(url, headers=headers, json=data)
        
        if response.status_code == 200:
            print(f"✅ Successfully dismissed alert #{alert_id}")
            return True
        else:
            print(f"❌ Failed to dismiss alert #{alert_id} (HTTP {response.status_code})")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error dismissing alert #{alert_id}: {str(e)}")
        return False

def main():
    """Main function to dismiss all non-applicable alerts"""
    token = os.environ.get("GITHUB_TOKEN")
    
    if not token:
        print("Error: GITHUB_TOKEN environment variable is required")
        print("The token needs 'security_events' scope to dismiss Dependabot alerts")
        print("Usage: GITHUB_TOKEN=your_token_here python3 dismiss-dependabot-alerts.py")
        sys.exit(1)
    
    print("🔐 Dismissing Dependabot alerts not confirmed by Dynatrace RVA...")
    print(f"Repository: {OWNER}/{REPO}")
    print(f"Reason: {REASON}")
    print("")
    
    success_count = 0
    
    for alert in ALERTS_TO_DISMISS:
        if dismiss_alert(token, alert["id"], alert["description"]):
            success_count += 1
        print("")
    
    print(f"🎯 Summary: Successfully dismissed {success_count}/{len(ALERTS_TO_DISMISS)} alerts")
    print("These alerts were identified as non-applicable through Dynatrace Runtime Vulnerability Analytics")

if __name__ == "__main__":
    main()