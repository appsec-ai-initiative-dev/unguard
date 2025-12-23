# Dynatrace Security Queries - Quick Start Guide

Get started with querying Dynatrace for security vulnerabilities in 5 minutes.

## Prerequisites

- Dynatrace environment with Runtime Vulnerability Analytics (RVA) enabled
- API token with `securityEvents.read` and `dql.query.execute` permissions
- Unguard application monitored by Dynatrace OneAgent

## Step 1: Configure Environment Variables

```bash
export DT_ENVIRONMENT="https://your-environment.live.dynatrace.com"
export DT_API_TOKEN="your-api-token"
```

💡 **Tip**: Add these to your `~/.bashrc` or `~/.zshrc` for persistence.

## Step 2: Quick Test

Test your setup with a simple query:

```bash
cd scripts/dynatrace
./query_vulnerabilities.sh --format summary
```

Expected output:
```
================================================================================
VULNERABILITY SUMMARY
================================================================================
Total vulnerabilities found: 25

By Severity:
  CRITICAL: 3
  HIGH: 8
  MEDIUM: 12
  LOW: 2
```

## Step 3: Query All Vulnerabilities

Get detailed information about all open vulnerabilities:

```bash
./query_vulnerabilities.sh
```

You'll see output like:
```
[1] SNYK-JS-NEXT-123456
    Title: Authorization Bypass in Next.js Middleware
    CVE: CVE-2025-29927
    Risk: CRITICAL (Score: 9.5)
    Affected Entities: 3
    Davis Assessment:
      - Vulnerable Function In Use: ✓ YES
      - Public Exploit Available: ✓ YES
      - Public Internet Exposure: ✓ YES
      - Data Assets Within Reach: ✓ YES
```

## Step 4: Filter by Severity

Focus on critical issues:

```bash
./query_vulnerabilities.sh --severity CRITICAL
```

Or check high-severity issues:

```bash
./query_vulnerabilities.sh --severity HIGH
```

## Step 5: Check Active Vulnerabilities

See vulnerabilities where the vulnerable code is actually running:

```bash
./query_vulnerabilities.sh --use-python --function-in-use
```

This shows vulnerabilities with **top priority** because the vulnerable function is **IN_USE**.

## Step 6: Verify a Specific CVE

When you get a Dependabot alert, verify it against runtime:

```bash
python3 scripts/dynatrace/query_vulnerabilities.py --cve CVE-2024-21508
```

**Interpretation:**
- ✅ **Found + Function IN_USE** → Fix immediately
- ⚠️ **Found + Function NOT_IN_USE** → Lower priority
- ❌ **Not Found** → Can dismiss the alert

## Common Use Cases

### Use Case 1: Daily Security Check

Run this every morning:

```bash
# Get summary of all vulnerabilities
./query_vulnerabilities.sh --format summary

# Check for any new critical issues
./query_vulnerabilities.sh --severity CRITICAL
```

### Use Case 2: Pre-Deployment Validation

Before deploying to production:

```bash
# Check for blocking issues
CRITICAL_COUNT=$(python3 scripts/dynatrace/query_vulnerabilities.py \
  --severity CRITICAL --format json | python3 -c "import sys, json; print(len(json.load(sys.stdin)))")

if [ "$CRITICAL_COUNT" -gt 0 ]; then
  echo "❌ Deployment blocked: $CRITICAL_COUNT critical vulnerabilities found"
  exit 1
fi

echo "✅ No blocking vulnerabilities - safe to deploy"
```

### Use Case 3: Dependabot Alert Verification

When you receive a Dependabot alert for CVE-2024-21508:

```bash
# 1. Query Dynatrace
python3 scripts/dynatrace/query_vulnerabilities.py \
  --cve CVE-2024-21508 \
  --format json > cve_check.json

# 2. Check result
if [ -s cve_check.json ]; then
  echo "✅ Vulnerability confirmed in runtime - prioritize fix"
else
  echo "❌ Vulnerability not detected in runtime - can dismiss alert"
fi
```

### Use Case 4: Security Report for Management

Generate a weekly security report:

```bash
# Generate report
./query_vulnerabilities.sh > weekly_security_report.txt

# Or get JSON for further processing
./query_vulnerabilities.sh --format json > weekly_security_report.json
```

## Output Formats

### Table Format (Default)
Human-readable with all details:
```bash
./query_vulnerabilities.sh
```

### JSON Format
Machine-readable for automation:
```bash
./query_vulnerabilities.sh --format json
```

### Summary Format
Quick overview:
```bash
./query_vulnerabilities.sh --format summary
```

## Advanced Options

### Look Back Further in Time

Default is 7 days. To look back 30 days:

```bash
python3 scripts/dynatrace/query_vulnerabilities.py --days 30
```

### Export to File

```bash
# Export all vulnerabilities to JSON
python3 scripts/dynatrace/query_vulnerabilities.py \
  --format json > vulnerabilities_$(date +%Y%m%d).json

# Export critical vulnerabilities to text report
./query_vulnerabilities.sh --severity CRITICAL > critical_vulns.txt
```

### Combine with Other Tools

```bash
# Count critical vulnerabilities
CRITICAL=$(python3 scripts/dynatrace/query_vulnerabilities.py \
  --severity CRITICAL --format json | jq 'length')
echo "Critical vulnerabilities: $CRITICAL"

# Get list of CVEs
python3 scripts/dynatrace/query_vulnerabilities.py \
  --format json | jq -r '.[]["vulnerability.references.cve"][]' | sort -u
```

## Understanding the Results

### Risk Levels

| Level | Score | Priority | Action |
|-------|-------|----------|--------|
| CRITICAL | 9.0-10.0 | 🔴 Immediate | Fix within 24h |
| HIGH | 7.0-8.9 | 🟠 Urgent | Fix within 1 week |
| MEDIUM | 4.0-6.9 | 🟡 Important | Fix within 1 month |
| LOW | 0.1-3.9 | 🔵 Minor | Fix when possible |

### Davis Assessment Flags

**High Priority Combination:**
- ✓ Vulnerable Function IN_USE
- ✓ Public Exploit Available
- ✓ Public Internet Exposure
- ✓ Data Assets Within Reach

**Lower Priority:**
- ✗ Vulnerable Function NOT_IN_USE
- ✗ No Public Exploit
- ✗ Private Network Only
- ✗ No Sensitive Data

## Troubleshooting

### Problem: No vulnerabilities returned

**Solution 1**: Check longer time range
```bash
python3 scripts/dynatrace/query_vulnerabilities.py --days 30
```

**Solution 2**: Verify RVA is enabled in Dynatrace UI

**Solution 3**: Ensure application is monitored
```bash
# Check in Dynatrace UI:
# Applications & Microservices → [Your App] → Security
```

### Problem: Authentication error

**Error**: `401 Unauthorized`

**Solution**: Check your API token
```bash
# Verify token is set
echo $DT_API_TOKEN

# Verify environment URL
echo $DT_ENVIRONMENT

# Test API connectivity
curl -H "Authorization: Api-Token $DT_API_TOKEN" \
  "$DT_ENVIRONMENT/api/v2/entities?entitySelector=type(APPLICATION)"
```

### Problem: Python module not found

**Error**: `ModuleNotFoundError: No module named 'requests'`

**Solution**: Install required dependencies
```bash
pip3 install requests
```

## Next Steps

1. **Set up CI/CD Integration**
   - See [GitHub Actions example](.github/workflows/dynatrace-security-scan.yml.example)
   - Integrate into your deployment pipeline

2. **Automate Daily Reports**
   - Schedule cron job for daily vulnerability checks
   - Send reports via email or Slack

3. **Learn DQL Queries**
   - Read [DYNATRACE-SECURITY-QUERIES.md](DYNATRACE-SECURITY-QUERIES.md)
   - Customize queries for your needs
   - Run queries directly in Dynatrace UI

4. **Integrate with Issue Tracking**
   - Automatically create GitHub issues for critical vulnerabilities
   - Link vulnerabilities to JIRA tickets

## Additional Resources

- [Dynatrace Integration Guide](DYNATRACE-INTEGRATION.md) - Comprehensive setup guide
- [Security Query Documentation](DYNATRACE-SECURITY-QUERIES.md) - All DQL query patterns
- [Scripts README](../scripts/dynatrace/README.md) - Detailed script documentation
- [Dynatrace Documentation](https://docs.dynatrace.com/docs/security/runtime-application-protection)

## Quick Reference Commands

```bash
# All vulnerabilities
./query_vulnerabilities.sh

# Critical only
./query_vulnerabilities.sh --severity CRITICAL

# Function in use
./query_vulnerabilities.sh --use-python --function-in-use

# Specific CVE
python3 query_vulnerabilities.py --cve CVE-2024-XXXXX

# JSON output
./query_vulnerabilities.sh --format json

# Summary
./query_vulnerabilities.sh --format summary

# 30 days back
python3 query_vulnerabilities.py --days 30
```

---

**Need help?** Check the [Troubleshooting](#troubleshooting) section or open an issue in the repository.
