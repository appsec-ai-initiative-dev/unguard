# Unguard Scripts

This directory contains utility scripts for working with the Unguard application.

## Get Top Vulnerabilities from Dynatrace

The `get_top_vulnerabilities.py` script queries Dynatrace Runtime Vulnerability Analytics (RVA) to retrieve the top 5 OPEN vulnerabilities affecting your environment.

### Prerequisites

- Python 3.6 or higher
- `requests` library (install with: `pip install requests`)
- Dynatrace environment with Runtime Vulnerability Analytics enabled
- Dynatrace API token with the following permissions:
  - `ReadEvents` (Read Events)
  - `queryEvents` (Query Events)

### Usage

1. Set the required environment variables:

```bash
export DT_URL="https://your-environment.live.dynatrace.com"
export DT_TOKEN="dt0c01.XXXXXXXXXXXXXXXXXXXXXXXX"
```

Alternatively, you can use:
```bash
export DYNATRACE_URL="https://your-environment.live.dynatrace.com"
export DYNATRACE_API_TOKEN="dt0c01.XXXXXXXXXXXXXXXXXXXXXXXX"
```

2. Run the script:

```bash
python3 scripts/get_top_vulnerabilities.py
```

Or if you made it executable:

```bash
./scripts/get_top_vulnerabilities.py
```

### Output

The script provides two types of output:

1. **Console Output**: A formatted, human-readable display of the top 5 vulnerabilities including:
   - Vulnerability ID and Title
   - Risk Level and Score (Davis AI-powered risk assessment)
   - Associated CVE identifiers
   - Number of affected entities
   - Last detection timestamp
   - Davis Assessments:
     - Whether the vulnerable function is in use
     - Public internet exposure status
     - Public exploit availability
     - Data assets within reach status

2. **JSON File**: A complete JSON dump saved to `dynatrace_top_vulnerabilities.json` in the current directory

### Example Output

```
================================================================================
TOP 5 VULNERABILITIES FROM DYNATRACE
================================================================================

#1 Vulnerability ID: CVE-2024-12345-SNYK-JAVA-ORGAPACHECOMMONS-1234567
   Title: Deserialization of Untrusted Data in Apache Commons Collections
   Risk Level: CRITICAL (Score: 9.8)
   CVEs: CVE-2024-12345
   Affected Entities: 12
   Last Detected: 2025-12-18T19:30:00.000Z
   Davis Assessments:
      - Vulnerable Function In Use: Yes
      - Public Internet Exposure: Yes
      - Public Exploit Available: Yes
      - Data Assets Within Reach: Yes
   ----------------------------------------------------------------------------

...
```

### Features

- Queries only OPEN, non-muted vulnerabilities
- Uses Davis AI-powered risk scoring for prioritization
- Provides comprehensive Davis security assessments
- Sorts vulnerabilities by risk score (highest first) and number of affected entities
- Automatically deduplicates vulnerabilities across entities
- Retrieves vulnerabilities detected within the last hour

### Troubleshooting

**Error: "Dynatrace URL not found"**
- Ensure you've set the `DT_URL` or `DYNATRACE_URL` environment variable

**Error: "Dynatrace API token not found"**
- Ensure you've set the `DT_TOKEN` or `DYNATRACE_API_TOKEN` environment variable

**Error: "401 Unauthorized"**
- Check that your API token is valid and has the required permissions

**Error: "No open vulnerabilities found"**
- This could mean:
  - No vulnerabilities are currently detected in your environment
  - Runtime Vulnerability Analytics is not enabled
  - All detected vulnerabilities are muted or resolved
  - The time window (last 1 hour) doesn't contain any vulnerability data

### Notes

- The script uses the Dynatrace DQL (Dynatrace Query Language) to query the `security.events` table
- Only vulnerabilities from Dynatrace Runtime Vulnerability Analytics (RVA) are included
- The query looks back 1 hour by default for fresh vulnerability data
- Vulnerabilities are automatically deduplicated across multiple affected entities
