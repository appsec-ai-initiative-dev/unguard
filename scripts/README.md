# Dependabot Alert Management Scripts

This directory contains scripts to automatically dismiss Dependabot security alerts that have been verified as non-applicable through Dynatrace Runtime Vulnerability Analytics (RVA).

## Scripts

### dismiss-dependabot-alerts.sh
Bash script to dismiss Dependabot alerts using the GitHub API.

**Requirements:**
- `GITHUB_TOKEN` environment variable with `security_events` scope
- `curl` command available

**Usage:**
```bash
export GITHUB_TOKEN="your_personal_access_token_here"
./scripts/dismiss-dependabot-alerts.sh
```

### dismiss-dependabot-alerts.py
Python script to dismiss Dependabot alerts using the GitHub API.

**Requirements:**
- Python 3.6+
- `requests` library: `pip install requests`
- `GITHUB_TOKEN` environment variable with `security_events` scope

**Usage:**
```bash
export GITHUB_TOKEN="your_personal_access_token_here"
python3 scripts/dismiss-dependabot-alerts.py
```

## GitHub Token Requirements

The token used must have the following permissions:
- `security_events` scope for reading and dismissing Dependabot alerts
- Repository access to `appsec-ai-initiative-dev/unguard`

## Alerts Being Dismissed

Based on Dynatrace Runtime Vulnerability Analytics findings, the following alerts are marked for dismissal:

| Alert ID | CVE | Description | Reason |
|----------|-----|-------------|--------|
| 44 | CVE-2023-41419 | gevent vulnerability | malicious-load-generator not deployed |
| 88 | CVE-2022-1996 | go-restful vulnerability | Not detected by Dynatrace RVA |
| 86 | CVE-2022-40083 | echo/v4 vulnerability | Not detected by Dynatrace RVA |
| 102 | CVE-2024-45337 | golang.org/x/crypto vulnerability | Not detected by Dynatrace RVA |
| 129 | CVE-2021-44906 | minimist vulnerability | Not detected by Dynatrace RVA |

All dismissed alerts will be marked with:
- **Dismissed Reason:** "vulnerable_code_not_actually_used"
- **Comment:** "Library was not observed in the monitored environment by Dynatrace Runtime Vulnerability Analytics (RVA)"

## Verification

After running the scripts, you can verify the dismissals by:
1. Checking the GitHub Security tab of the repository
2. Confirming that the alerts show as "Dismissed" with the appropriate reason
3. Reviewing the dismissal comments for audit trail