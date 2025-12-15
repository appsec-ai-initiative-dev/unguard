# Dynatrace Security Query Scripts

This directory contains scripts for querying Dynatrace Runtime Vulnerability Analytics (RVA) and other security features.

## Overview

These scripts help you programmatically query Dynatrace for security vulnerabilities, detections, and compliance findings. They leverage the Dynatrace API and DQL (Dynatrace Query Language) to retrieve and format security data.

## Prerequisites

### Environment Variables

Set the following environment variables before running the scripts:

```bash
export DT_ENVIRONMENT="https://your-environment.live.dynatrace.com"
export DT_API_TOKEN="your-api-token"
```

### API Token Permissions

Your Dynatrace API token must have the following permissions:
- **Read security events** (`securityEvents.read`)
- **Execute DQL queries** (`dql.query.execute`)

To create a token:
1. Navigate to **Settings > Access tokens** in your Dynatrace environment
2. Click **Generate new token**
3. Add a descriptive name (e.g., "Security Query Script")
4. Enable the required permissions listed above
5. Click **Generate token** and copy it

### Dependencies

#### For Shell Script (`query_vulnerabilities.sh`)
- `bash` (version 4.0+)
- `curl`
- `python3` (for JSON formatting)

#### For Python Script (`query_vulnerabilities.py`)
- Python 3.7 or higher
- `requests` library

Install Python dependencies:
```bash
pip3 install requests
```

## Scripts

### 1. `query_vulnerabilities.py`

A comprehensive Python script for querying Dynatrace vulnerabilities with advanced filtering and formatting options.

#### Usage

```bash
python3 query_vulnerabilities.py [OPTIONS]
```

#### Options

- `--environment URL`: Dynatrace environment URL (or set `DT_ENVIRONMENT` env var)
- `--token TOKEN`: Dynatrace API token (or set `DT_API_TOKEN` env var)
- `--severity LEVEL`: Filter by severity level (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`)
- `--function-in-use`: Show only vulnerabilities where the vulnerable function is in use
- `--cve CVE-XXXX-XXXX`: Look up a specific CVE
- `--days N`: Number of days to look back (default: 7)
- `--format FORMAT`: Output format - `table`, `json`, or `summary` (default: `table`)

#### Examples

Query all open vulnerabilities:
```bash
python3 query_vulnerabilities.py
```

Query only CRITICAL vulnerabilities:
```bash
python3 query_vulnerabilities.py --severity CRITICAL
```

Query vulnerabilities with function in use:
```bash
python3 query_vulnerabilities.py --function-in-use
```

Query specific CVE:
```bash
python3 query_vulnerabilities.py --cve CVE-2024-21508
```

Get JSON output:
```bash
python3 query_vulnerabilities.py --format json
```

Get summary only:
```bash
python3 query_vulnerabilities.py --format summary
```

Look back 30 days:
```bash
python3 query_vulnerabilities.py --days 30
```

### 2. `query_vulnerabilities.sh`

A shell script wrapper that can use either `curl` directly or delegate to the Python script for advanced queries.

#### Usage

```bash
./query_vulnerabilities.sh [OPTIONS]
```

#### Options

- `--use-python`: Use Python script instead of curl
- `--severity LEVEL`: Filter by severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`)
- `--days N`: Look back N days (default: 7)
- `--function-in-use`: Show only vulnerabilities with function in use (requires `--use-python`)
- `--cve CVE-XXXX-XXXX`: Look up specific CVE (requires `--use-python`)
- `--format FORMAT`: Output format - `table`, `json`, or `summary` (default: `table`)
- `--help, -h`: Show help message

#### Examples

Query all vulnerabilities using curl:
```bash
./query_vulnerabilities.sh
```

Query CRITICAL vulnerabilities:
```bash
./query_vulnerabilities.sh --severity CRITICAL
```

Use Python script for advanced query:
```bash
./query_vulnerabilities.sh --use-python --function-in-use
```

Get JSON output:
```bash
./query_vulnerabilities.sh --format json
```

## Output Format

### Table Format (Default)

Displays vulnerabilities in a human-readable table format with:
- Vulnerability Display ID
- Title
- CVE identifier(s)
- Risk level and score
- Number of affected entities
- Davis Assessment details:
  - Vulnerable Function In Use
  - Public Exploit Available
  - Public Internet Exposure
  - Data Assets Within Reach

Example:
```
================================================================================
DYNATRACE RUNTIME VULNERABILITY ANALYTICS - LATEST VULNERABILITIES
================================================================================

[1] SNYK-JS-NEXT-123456
    Title: Authorization Bypass in Next.js Middleware
    CVE: CVE-2024-21508
    Risk: CRITICAL (Score: 9.5)
    Affected Entities: 3
    Davis Assessment:
      - Vulnerable Function In Use: ✓ YES
      - Public Exploit Available: ✓ YES
      - Public Internet Exposure: ✓ YES
      - Data Assets Within Reach: ✓ YES

================================================================================
Total: 1 vulnerabilities
================================================================================
```

### JSON Format

Returns raw JSON data from the Dynatrace API, suitable for further processing or integration with other tools.

### Summary Format

Provides a high-level overview with counts by severity level:

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

## Understanding Davis Assessment

Dynatrace uses AI-powered Davis assessment to evaluate the actual risk of each vulnerability:

- **Vulnerable Function In Use**: Whether the vulnerable code path is actually executed in runtime
  - `IN_USE`: High priority - vulnerable code is being executed
  - `NOT_IN_USE`: Lower priority - vulnerable code is not executed

- **Public Exploit Available**: Whether public exploits exist for this vulnerability
  - `AVAILABLE`: Exploit code is publicly available
  - `NOT_AVAILABLE`: No known public exploits

- **Public Internet Exposure**: Whether the affected service is accessible from the internet
  - `PUBLIC_NETWORK`: Service is exposed to the internet
  - `PRIVATE_NETWORK`: Service is only accessible internally

- **Data Assets Within Reach**: Whether sensitive data is accessible from the vulnerable component
  - `REACHABLE`: Sensitive data can be accessed
  - `NOT_REACHABLE`: No sensitive data in reach

## Risk Level Mapping

Dynatrace maps vulnerability risk scores to severity levels:

| Risk Score | Severity Level |
|------------|----------------|
| 9.0 - 10.0 | CRITICAL       |
| 7.0 - 8.9  | HIGH           |
| 4.0 - 6.9  | MEDIUM         |
| 0.1 - 3.9  | LOW            |
| < 0.1      | NONE           |

## Integration Examples

### CI/CD Pipeline

Add vulnerability checks to your CI/CD pipeline:

```yaml
# GitHub Actions example
- name: Check for Critical Vulnerabilities
  env:
    DT_ENVIRONMENT: ${{ secrets.DT_ENVIRONMENT }}
    DT_API_TOKEN: ${{ secrets.DT_API_TOKEN }}
  run: |
    CRITICAL_COUNT=$(python3 scripts/dynatrace/query_vulnerabilities.py \
      --severity CRITICAL \
      --format json | jq 'length')
    
    if [ "$CRITICAL_COUNT" -gt 0 ]; then
      echo "❌ Found $CRITICAL_COUNT critical vulnerabilities!"
      python3 scripts/dynatrace/query_vulnerabilities.py --severity CRITICAL
      exit 1
    fi
    echo "✅ No critical vulnerabilities found"
```

### Daily Security Report

Generate daily vulnerability reports:

```bash
#!/bin/bash
# daily_vulnerability_report.sh

DATE=$(date +%Y-%m-%d)
REPORT_FILE="vulnerability_report_${DATE}.json"

echo "Generating vulnerability report for $DATE..."

python3 scripts/dynatrace/query_vulnerabilities.py \
  --format json > "$REPORT_FILE"

# Send report via email or Slack
# ... your notification logic here ...

echo "Report saved to $REPORT_FILE"
```

### Monitoring Script

Continuously monitor for new critical vulnerabilities:

```bash
#!/bin/bash
# monitor_vulnerabilities.sh

while true; do
  echo "Checking for critical vulnerabilities..."
  
  CRITICAL=$(python3 scripts/dynatrace/query_vulnerabilities.py \
    --severity CRITICAL \
    --format summary | grep "CRITICAL:" | awk '{print $2}')
  
  if [ "$CRITICAL" -gt 0 ]; then
    echo "⚠️  WARNING: $CRITICAL critical vulnerabilities detected!"
    # Send alert
    # ... your alerting logic here ...
  else
    echo "✅ No critical vulnerabilities"
  fi
  
  # Check every hour
  sleep 3600
done
```

## Troubleshooting

### Common Issues

1. **Authentication Error**
   ```
   Error executing DQL query: 401 Unauthorized
   ```
   - Verify your `DT_API_TOKEN` is correct
   - Check that the token has required permissions
   - Ensure the token hasn't expired

2. **Invalid Environment URL**
   ```
   Error executing DQL query: Connection refused
   ```
   - Verify `DT_ENVIRONMENT` is set correctly
   - Ensure URL format: `https://your-env.live.dynatrace.com` (no trailing slash)
   - Check network connectivity

3. **No Data Returned**
   - Increase the `--days` parameter to look further back
   - Verify that Runtime Vulnerability Analytics is enabled in your Dynatrace environment
   - Check that applications are being monitored

4. **Python Import Error**
   ```
   ModuleNotFoundError: No module named 'requests'
   ```
   - Install the requests library: `pip3 install requests`

## Additional Resources

- [Dynatrace Security Queries Documentation](../../docs/DYNATRACE-SECURITY-QUERIES.md)
- [Dynatrace API Documentation](https://docs.dynatrace.com/docs/dynatrace-api)
- [DQL Reference](https://docs.dynatrace.com/docs/observe-and-explore/query-data/dynatrace-query-language)
- [Runtime Vulnerability Analytics](https://docs.dynatrace.com/docs/security/runtime-application-protection/runtime-vulnerability-analytics)

## Contributing

When adding new scripts or modifying existing ones:
1. Follow the existing code style and structure
2. Update this README with usage examples
3. Add comprehensive comments and documentation
4. Test with different Dynatrace environments
5. Handle errors gracefully

## License

Copyright 2023 Dynatrace LLC

Licensed under the Apache License, Version 2.0. See LICENSE.txt in the repository root for details.
