# Dynatrace Vulnerability Query Examples

This document provides practical examples of how to retrieve and analyze vulnerabilities from Dynatrace using the provided tools.

## Quick Start

### Prerequisites

1. **Set up environment variables:**
   ```bash
   export DT_TENANT="https://abc12345.live.dynatrace.com"
   export DT_API_TOKEN="dt0c01.XXXXXXXXXXXXXXXXXXXXXXXX"
   ```

2. **Install Python dependencies (for Python script):**
   ```bash
   pip install requests
   ```

## Using the Shell Script (Recommended)

The shell script provides convenient presets for common use cases.

### Example 1: Get All Vulnerabilities

```bash
./get-vulnerabilities.sh all
```

**Output:** JSON list of all vulnerabilities

### Example 2: Get Critical and High Severity Only

```bash
./get-vulnerabilities.sh critical --format csv --output critical-vulns.csv
```

**Output:** CSV file with CRITICAL and HIGH severity vulnerabilities

### Example 3: Get High-Priority Vulnerabilities (Function In Use)

```bash
./get-vulnerabilities.sh priority --format markdown
```

**Output:** Markdown report with vulnerabilities where vulnerable function is in use

**Why this matters:** These are the vulnerabilities that pose real runtime risk because the vulnerable code is actually being executed.

### Example 4: Generate Summary Report

```bash
./get-vulnerabilities.sh summary --output vulnerability-report.md
```

**Output:** Markdown file with summary statistics and detailed vulnerability table

### Example 5: Check Recent Vulnerabilities (Last 24 Hours)

```bash
./get-vulnerabilities.sh recent
```

**Output:** JSON list of vulnerabilities detected in the last 24 hours

### Example 6: Get Exploitable Vulnerabilities

```bash
./get-vulnerabilities.sh exploitable --format markdown --output exploitable.md
```

**Output:** Markdown report of CRITICAL/HIGH vulnerabilities with function in use

## Using the Python Script Directly

For more control and custom filtering.

### Example 1: Basic Retrieval

```bash
python3 get_vulnerabilities.py
```

### Example 2: Filter by Specific CVE

```bash
python3 get_vulnerabilities.py --cve CVE-2024-38816
```

**Use case:** Cross-reference Dependabot alerts with Dynatrace runtime analysis

### Example 3: Get Vulnerabilities for Specific Entity

```bash
python3 get_vulnerabilities.py --entity PROCESS_GROUP-ABCD1234EFGH5678
```

### Example 4: Last 30 Days with High Severity

```bash
python3 get_vulnerabilities.py --days 30 --severity HIGH,CRITICAL --format csv
```

### Example 5: Function In Use + Public Exploits Available

```bash
python3 get_vulnerabilities.py \
  --function-in-use \
  --severity CRITICAL,HIGH \
  --format markdown \
  --output priority-vulnerabilities.md
```

**Use case:** Generate a report for security team showing only the most critical vulnerabilities

## Using DQL Directly in Dynatrace

Copy these queries into Dynatrace Notebooks or use them via the API.

### Example 1: Basic Vulnerability Query

```dql
fetch security.events, from:now() - 7d
| filter event.type == "VULNERABILITY_STATE_REPORT_EVENT"
| dedup {vulnerability.display_id, affected_entity.id}, sort: {timestamp desc}
| filter vulnerability.resolution_status == "OPEN"
| fieldsAdd 
    vuln_id = vulnerability.display_id,
    entity_name = entityName(affected_entity.id),
    severity = vulnerability.severity,
    davis_score = davis.assessment.risk_score
| fields vuln_id, entity_name, severity, davis_score
| sort davis_score desc
```

### Example 2: Vulnerability Summary by Severity

```dql
fetch security.events, from:now() - 7d
| filter event.type == "VULNERABILITY_STATE_REPORT_EVENT"
| dedup {vulnerability.display_id, affected_entity.id}, sort: {timestamp desc}
| filter vulnerability.resolution_status == "OPEN"
| summarize 
    total = count(),
    function_in_use = countIf(davis.assessment.vulnerable_function_in_use == true),
    public_exploits = countIf(davis.assessment.public_exploit_available == true),
    by: {severity = vulnerability.severity}
| sort severity asc
```

**Sample Output:**
| severity | total | function_in_use | public_exploits |
|----------|-------|-----------------|-----------------|
| CRITICAL | 5     | 2               | 1               |
| HIGH     | 23    | 8               | 4               |
| MEDIUM   | 67    | 15              | 2               |
| LOW      | 102   | 5               | 0               |

### Example 3: Top Vulnerable Components

```dql
fetch security.events, from:now() - 7d
| filter event.type == "VULNERABILITY_STATE_REPORT_EVENT"
| dedup {vulnerability.display_id, affected_entity.id}, sort: {timestamp desc}
| filter vulnerability.resolution_status == "OPEN"
| summarize 
    vuln_count = count(),
    critical_count = countIf(vulnerability.severity == "CRITICAL"),
    function_in_use = countIf(davis.assessment.vulnerable_function_in_use == true),
    by: {component = vulnerability.vulnerable_component}
| sort critical_count desc, vuln_count desc
| limit 10
```

**Use case:** Identify which libraries/dependencies have the most vulnerabilities

### Example 4: Cross-Reference with Dependabot CVE

```dql
fetch security.events, from:now() - 7d
| filter event.type == "VULNERABILITY_STATE_REPORT_EVENT"
| dedup {vulnerability.display_id, affected_entity.id}, sort: {timestamp desc}
| filter vulnerability.resolution_status == "OPEN"
| expand vulnerability.references.cve
| filter vulnerability.references.cve == "CVE-2024-38816"
| fieldsAdd 
    entity_name = entityName(affected_entity.id),
    severity = vulnerability.severity,
    function_in_use = davis.assessment.vulnerable_function_in_use,
    component = vulnerability.vulnerable_component,
    davis_score = davis.assessment.risk_score
| fields entity_name, severity, function_in_use, component, davis_score
```

**Use case:** Dependabot raised CVE-2024-38816, verify if it's actually exploitable in runtime

### Example 5: Vulnerabilities by Technology Stack

```dql
fetch security.events, from:now() - 7d
| filter event.type == "VULNERABILITY_STATE_REPORT_EVENT"
| dedup {vulnerability.display_id, affected_entity.id}, sort: {timestamp desc}
| filter vulnerability.resolution_status == "OPEN"
| summarize 
    total = count(),
    critical = countIf(vulnerability.severity == "CRITICAL"),
    high = countIf(vulnerability.severity == "HIGH"),
    function_in_use = countIf(davis.assessment.vulnerable_function_in_use == true),
    by: {technology = vulnerability.technology}
| sort critical desc, high desc
```

**Sample Output:**
| technology | total | critical | high | function_in_use |
|------------|-------|----------|------|-----------------|
| JAVA       | 45    | 3        | 12   | 8               |
| NODEJS     | 32    | 1        | 8    | 5               |
| PYTHON     | 28    | 2        | 6    | 4               |

### Example 6: Entity Vulnerability Assessment

```dql
fetch security.events, from:now() - 7d
| filter event.type == "VULNERABILITY_STATE_REPORT_EVENT"
| dedup {vulnerability.display_id, affected_entity.id}, sort: {timestamp desc}
| filter vulnerability.resolution_status == "OPEN"
| summarize 
    total_vulns = count(),
    critical_vulns = countIf(vulnerability.severity == "CRITICAL"),
    high_vulns = countIf(vulnerability.severity == "HIGH"),
    function_in_use_count = countIf(davis.assessment.vulnerable_function_in_use == true),
    max_davis_score = max(davis.assessment.risk_score),
    by: {
        entity_name = entityName(affected_entity.id),
        entity_type = affected_entity.type
    }
| sort critical_vulns desc, high_vulns desc
| limit 20
```

**Use case:** Identify which services/processes have the most critical vulnerabilities

## Real-World Workflows

### Workflow 1: Daily Security Report

**Goal:** Generate daily security report for team

```bash
#!/bin/bash
# Generate daily vulnerability report

DATE=$(date +%Y-%m-%d)
REPORT_DIR="./reports"
mkdir -p "$REPORT_DIR"

echo "Generating daily vulnerability report for $DATE..."

# Get summary report
./get-vulnerabilities.sh summary --output "$REPORT_DIR/daily-summary-$DATE.md"

# Get critical vulnerabilities
./get-vulnerabilities.sh critical --format csv --output "$REPORT_DIR/critical-vulns-$DATE.csv"

# Get high-priority (function in use)
./get-vulnerabilities.sh priority --format json --output "$REPORT_DIR/priority-vulns-$DATE.json"

echo "Reports generated in $REPORT_DIR/"
```

### Workflow 2: Dependabot Integration

**Goal:** Verify Dependabot alerts with Dynatrace runtime data

```bash
#!/bin/bash
# Check if Dependabot CVE is actually exploitable

CVE="$1"

if [ -z "$CVE" ]; then
    echo "Usage: $0 CVE-YYYY-NNNNN"
    exit 1
fi

echo "Checking Dynatrace for $CVE..."

python3 get_vulnerabilities.py \
  --cve "$CVE" \
  --format markdown

# If function_in_use == true: High priority, create P1 issue
# If function_in_use == false: Lower priority, can be scheduled
```

### Workflow 3: Pre-Deployment Security Check

**Goal:** Block deployment if critical vulnerabilities with function in use exist

```bash
#!/bin/bash
# Pre-deployment security gate

echo "Running pre-deployment security check..."

CRITICAL_COUNT=$(python3 get_vulnerabilities.py \
  --severity CRITICAL \
  --function-in-use \
  --format json | jq '. | length')

echo "Found $CRITICAL_COUNT critical vulnerabilities with function in use"

if [ "$CRITICAL_COUNT" -gt 0 ]; then
    echo "❌ DEPLOYMENT BLOCKED: Critical vulnerabilities detected"
    python3 get_vulnerabilities.py \
      --severity CRITICAL \
      --function-in-use \
      --format markdown
    exit 1
else
    echo "✅ Security check passed"
    exit 0
fi
```

### Workflow 4: Weekly Security Dashboard

**Goal:** Generate comprehensive weekly security metrics

```bash
#!/bin/bash
# Weekly security dashboard

WEEK=$(date +%Y-W%U)
OUTPUT="security-dashboard-$WEEK.md"

cat > "$OUTPUT" << 'EOF'
# Weekly Security Dashboard
EOF

echo "## Generated: $(date)" >> "$OUTPUT"
echo "" >> "$OUTPUT"

# Get summary
./get-vulnerabilities.sh summary >> "$OUTPUT"

echo "" >> "$OUTPUT"
echo "## Critical Vulnerabilities (Function In Use)" >> "$OUTPUT"
./get-vulnerabilities.sh priority --format markdown >> "$OUTPUT"

echo "Dashboard generated: $OUTPUT"
```

## API Integration Examples

### Using curl with Dynatrace API

```bash
#!/bin/bash
# Execute DQL query via API

DQL_QUERY='fetch security.events, from:now() - 7d
| filter event.type == "VULNERABILITY_STATE_REPORT_EVENT"
| dedup {vulnerability.display_id, affected_entity.id}, sort: {timestamp desc}
| filter vulnerability.resolution_status == "OPEN"
| summarize count()'

curl -X POST "$DT_TENANT/api/v2/query/execute" \
  -H "Authorization: Api-Token $DT_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"$DQL_QUERY\"}" | jq
```

### Using Python requests

```python
import requests
import os

def query_dynatrace(dql_query):
    tenant_url = os.getenv('DT_TENANT')
    api_token = os.getenv('DT_API_TOKEN')
    
    response = requests.post(
        f"{tenant_url}/api/v2/query/execute",
        headers={
            "Authorization": f"Api-Token {api_token}",
            "Content-Type": "application/json"
        },
        json={"query": dql_query}
    )
    
    return response.json()

# Example query
query = """
fetch security.events, from:now() - 7d
| filter event.type == "VULNERABILITY_STATE_REPORT_EVENT"
| dedup {vulnerability.display_id, affected_entity.id}, sort: {timestamp desc}
| filter vulnerability.resolution_status == "OPEN"
| filter davis.assessment.vulnerable_function_in_use == true
| summarize count()
"""

result = query_dynatrace(query)
print(result)
```

## Troubleshooting

### Issue: "No vulnerabilities found"

**Possible causes:**
1. Timeframe too narrow - try increasing `--days` value
2. Filters too restrictive - remove filters like `--function-in-use`
3. No vulnerability scans have run yet - check Dynatrace security settings

### Issue: "Authentication failed"

**Solution:**
1. Verify `DT_TENANT` URL is correct (include https://)
2. Verify `DT_API_TOKEN` has `storage:events:read` scope
3. Check token hasn't expired

### Issue: "Field not found" errors

**Solution:**
- Some fields may not be present in older Dynatrace versions
- Remove optional fields from queries
- Check Dynatrace documentation for field availability

## Additional Resources

- [Dynatrace Security Events Documentation](https://docs.dynatrace.com/docs/shortlink/security-events)
- [DQL Documentation](https://docs.dynatrace.com/docs/platform/grail/dynatrace-query-language)
- [Vulnerability Analytics](https://docs.dynatrace.com/docs/platform-modules/application-security/vulnerability-analytics)

## Support

For issues or questions:
1. Check the main [README.md](./README.md) for detailed field reference
2. Review [get-vulnerabilities.dql](./get-vulnerabilities.dql) for query examples
3. Create an issue in the repository
