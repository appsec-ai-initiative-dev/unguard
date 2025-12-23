# Dynatrace Integration Guide

This guide explains how to use Dynatrace with Unguard to query and analyze security vulnerabilities in real-time.

## Overview

Unguard integrates with Dynatrace Runtime Vulnerability Analytics (RVA) to provide comprehensive security analysis of running applications. This integration allows you to:

- Query real-time vulnerability data from monitored applications
- Verify Dependabot and GitHub Advanced Security alerts against runtime behavior
- Assess actual risk using Davis AI-powered analysis
- Automate security scanning in CI/CD pipelines
- Generate security reports and track remediation

## Getting Started

### Prerequisites

1. **Dynatrace Environment**: Access to a Dynatrace SaaS or Managed environment
2. **API Token**: A Dynatrace API token with the following permissions:
   - `securityEvents.read` - Read security events
   - `dql.query.execute` - Execute DQL queries
3. **OneAgent Monitoring**: Unguard application monitored by Dynatrace OneAgent
4. **Runtime Vulnerability Analytics**: RVA enabled in your Dynatrace environment

### Setup

1. **Configure Environment Variables**

   ```bash
   export DT_ENVIRONMENT="https://your-environment.live.dynatrace.com"
   export DT_API_TOKEN="your-api-token"
   ```

2. **Verify Setup**

   Test your configuration by running a simple query:

   ```bash
   cd scripts/dynatrace
   ./query_vulnerabilities.sh --format summary
   ```

## Querying Vulnerabilities

### Using the Shell Script

The shell script provides a quick way to query vulnerabilities:

```bash
# Query all open vulnerabilities
./scripts/dynatrace/query_vulnerabilities.sh

# Query critical vulnerabilities only
./scripts/dynatrace/query_vulnerabilities.sh --severity CRITICAL

# Get JSON output for processing
./scripts/dynatrace/query_vulnerabilities.sh --format json
```

### Using the Python Script

The Python script offers more advanced filtering options:

```bash
# Query vulnerabilities with function in use
python3 scripts/dynatrace/query_vulnerabilities.py --function-in-use

# Query specific CVE
python3 scripts/dynatrace/query_vulnerabilities.py --cve CVE-2024-21508

# Look back 30 days
python3 scripts/dynatrace/query_vulnerabilities.py --days 30
```

## Understanding Davis Assessment

Dynatrace's Davis AI provides context-aware risk assessment for each vulnerability:

### Risk Factors

1. **Vulnerable Function In Use**
   - `IN_USE`: The vulnerable code path is executed in runtime → **High Priority**
   - `NOT_IN_USE`: The vulnerable code is not executed → **Lower Priority**

2. **Public Exploit Available**
   - `AVAILABLE`: Public exploit code exists → **Increased Risk**
   - `NOT_AVAILABLE`: No known public exploits → **Lower Risk**

3. **Public Internet Exposure**
   - `PUBLIC_NETWORK`: Service accessible from internet → **Critical**
   - `PRIVATE_NETWORK`: Internal service only → **Lower Risk**

4. **Data Assets Within Reach**
   - `REACHABLE`: Sensitive data accessible → **High Impact**
   - `NOT_REACHABLE`: No sensitive data in reach → **Lower Impact**

### Risk Prioritization

Focus on vulnerabilities with:
✅ Function IN_USE + Public Exploit + Public Exposure = **Immediate Action Required**
⚠️ Function IN_USE + Public Exploit = **High Priority**
ℹ️ Function NOT_IN_USE = **Lower Priority / Consider Suppression**

## Verifying Dependabot Alerts

When you receive a Dependabot alert, verify it against Dynatrace runtime data:

### Step 1: Query by CVE

```bash
python3 scripts/dynatrace/query_vulnerabilities.py --cve CVE-2024-21508
```

### Step 2: Analyze Results

**Scenario A: CVE Found + Function IN_USE**
- ✅ **Status**: CONFIRMED
- 🚨 **Action**: Fix immediately - vulnerable code is running
- 📝 **Comment**: Add Dynatrace details to the Dependabot alert

**Scenario B: CVE Found + Function NOT_IN_USE**
- ⚠️ **Status**: NOT CONFIRMED
- 📊 **Action**: Lower priority - vulnerable code is not executed
- 📝 **Comment**: Consider deferring or suppressing

**Scenario C: CVE Not Found**
- ❌ **Status**: NOT DETECTED
- 📝 **Action**: Dismiss Dependabot alert with reason: "Not observed in runtime environment by Dynatrace"

### Example Verification Workflow

```bash
# 1. Get the CVE from Dependabot alert
CVE="CVE-2024-21508"

# 2. Query Dynatrace
python3 scripts/dynatrace/query_vulnerabilities.py --cve $CVE --format json > cve_check.json

# 3. Check if found and in use
FOUND=$(jq 'length' cve_check.json)
if [ "$FOUND" -gt 0 ]; then
  IN_USE=$(jq -r '.[0]["vulnerability.davis_assessment.vulnerable_function_status"]' cve_check.json)
  
  if [ "$IN_USE" = "IN_USE" ]; then
    echo "🚨 CONFIRMED: Vulnerability is in runtime and function is in use!"
    echo "Priority: CRITICAL - Fix immediately"
  else
    echo "⚠️ NOT CONFIRMED: Vulnerability detected but function not in use"
    echo "Priority: LOW - Consider deferring"
  fi
else
  echo "❌ NOT DETECTED: Vulnerability not observed in runtime"
  echo "Action: Dismiss Dependabot alert"
fi
```

## CI/CD Integration

### GitHub Actions

An example workflow is provided at `.github/workflows/dynatrace-security-scan.yml.example`:

```bash
# Rename to activate
mv .github/workflows/dynatrace-security-scan.yml.example \
   .github/workflows/dynatrace-security-scan.yml
```

The workflow:
- ✅ Runs on every PR and push to main
- 📊 Queries vulnerabilities by severity
- 🚨 Fails builds if critical vulnerabilities are found
- 📝 Comments results on PRs
- 🎫 Creates GitHub issues for critical findings

### Key Features

1. **Pre-Deployment Gate**: Blocks deployments if critical vulnerabilities exist
2. **Automated Reporting**: Generates vulnerability reports as artifacts
3. **Issue Creation**: Automatically creates GitHub issues for tracking
4. **PR Comments**: Posts scan results directly on pull requests

### Customization

Adjust thresholds in the workflow:

```yaml
# Fail if critical vulnerabilities found
if [ "$CRITICAL_COUNT" -gt 0 ]; then
  exit 1
fi

# Warn if more than 5 active vulnerabilities
if [ "$ACTIVE_COUNT" -gt 5 ]; then
  echo "⚠️ WARNING"
fi
```

## Daily Security Monitoring

### Automated Daily Report

Create a scheduled job to monitor vulnerabilities:

```bash
#!/bin/bash
# daily_security_report.sh

DATE=$(date +%Y-%m-%d)
REPORT_DIR="security_reports"
mkdir -p "$REPORT_DIR"

echo "Generating daily security report for $DATE..."

# Get all vulnerabilities
python3 scripts/dynatrace/query_vulnerabilities.py \
  --format json > "$REPORT_DIR/report_${DATE}.json"

# Get summary
python3 scripts/dynatrace/query_vulnerabilities.py \
  --format summary > "$REPORT_DIR/summary_${DATE}.txt"

# Check for critical issues
CRITICAL=$(python3 scripts/dynatrace/query_vulnerabilities.py \
  --severity CRITICAL \
  --format json | jq 'length')

if [ "$CRITICAL" -gt 0 ]; then
  echo "🚨 ALERT: $CRITICAL critical vulnerabilities detected!"
  # Send notification (email, Slack, etc.)
fi

echo "Report saved to $REPORT_DIR/"
```

### Cron Job Setup

```bash
# Add to crontab (runs daily at 8 AM)
0 8 * * * /path/to/daily_security_report.sh
```

## DQL Query Reference

### Quick Queries

These DQL queries can be run directly in the Dynatrace UI:

#### All Open Vulnerabilities (Last 7 Days)
```dql
fetch security.events, from:now()-7d
| filter event.provider=="Dynatrace"
     AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
| dedup {vulnerability.display_id, affected_entity.id}, sort:{timestamp desc}
| filter vulnerability.resolution.status == "OPEN"
| summarize count(), by: {vulnerability.risk.level}
```

#### Critical Vulnerabilities with Function In Use
```dql
fetch security.events, from:now()-7d
| filter event.provider=="Dynatrace"
     AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
| dedup {vulnerability.display_id, affected_entity.id}, sort:{timestamp desc}
| filter vulnerability.resolution.status == "OPEN"
     AND vulnerability.davis_assessment.vulnerable_function_status == "IN_USE"
| summarize vulnerability.risk.score=takeMax(vulnerability.risk.score),
            by: {vulnerability.display_id}
| filter vulnerability.risk.score >= 9
```

For comprehensive query examples, see [DYNATRACE-SECURITY-QUERIES.md](DYNATRACE-SECURITY-QUERIES.md).

## Best Practices

### 1. Regular Scanning
- Run scans on every PR
- Schedule daily automated scans
- Monitor for new vulnerabilities continuously

### 2. Prioritization
- Focus on vulnerabilities with function IN_USE first
- Prioritize publicly exposed services
- Consider exploit availability in risk assessment

### 3. Verification Workflow
- Always verify Dependabot alerts against Dynatrace
- Document verification results in alerts
- Suppress false positives with proper justification

### 4. Remediation Tracking
- Create GitHub issues for confirmed vulnerabilities
- Link issues to Dynatrace vulnerability IDs
- Track remediation progress in your issue tracker

### 5. Documentation
- Document all suppressions with reasons
- Keep audit trail of security decisions
- Update security documentation regularly

## Troubleshooting

### No Vulnerabilities Returned

**Possible Causes:**
1. Runtime Vulnerability Analytics not enabled
2. Application not actively monitored
3. No vulnerabilities detected (unlikely in Unguard)
4. Time range too short

**Solutions:**
```bash
# Try longer time range
python3 scripts/dynatrace/query_vulnerabilities.py --days 30

# Verify monitoring
# Check Dynatrace UI → Applications & Microservices
```

### Authentication Errors

**Error:** `401 Unauthorized`

**Solutions:**
1. Verify API token is correct
2. Check token permissions (securityEvents.read, dql.query.execute)
3. Ensure token hasn't expired

### Query Errors

**Error:** `DQL syntax error`

**Solutions:**
1. Verify DQL query syntax
2. Check field names in semantic dictionary
3. Ensure time range is valid

## Additional Resources

- [Dynatrace Security Queries Documentation](DYNATRACE-SECURITY-QUERIES.md) - Comprehensive DQL query guide
- [Scripts README](../scripts/dynatrace/README.md) - Detailed script usage
- [Dynatrace API Documentation](https://docs.dynatrace.com/docs/dynatrace-api)
- [DQL Reference](https://docs.dynatrace.com/docs/observe-and-explore/query-data/dynatrace-query-language)
- [Runtime Vulnerability Analytics](https://docs.dynatrace.com/docs/security/runtime-application-protection/runtime-vulnerability-analytics)

## Support

For issues or questions:
1. Check the [FAQ](FAQ.md)
2. Review [Troubleshooting](#troubleshooting) section
3. Open an issue in the repository

---

**Note**: This integration is designed for the Unguard demo application. Adapt the queries and scripts for your specific use case and environment.
