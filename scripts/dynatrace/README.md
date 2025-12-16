# Dynatrace Vulnerability Query Scripts

This directory contains DQL (Dynatrace Query Language) scripts for retrieving and analyzing security vulnerabilities from Dynatrace.

## Overview

Dynatrace provides runtime vulnerability analysis with Davis AI-powered risk assessments. These scripts help you query, filter, and prioritize vulnerabilities based on real-world risk factors.

## Files

- **`get-vulnerabilities.dql`** - Comprehensive DQL queries for vulnerability retrieval
- **`README.md`** - This documentation file

## Quick Start

### 1. Basic Vulnerability Query

Copy this query into Dynatrace Notebooks or execute via API:

```dql
fetch security.events, from:now() - 7d
| filter event.type == "VULNERABILITY_STATE_REPORT_EVENT"
| dedup {vulnerability.display_id, affected_entity.id}, sort: {timestamp desc}
| filter vulnerability.resolution_status == "OPEN"
| fieldsAdd 
    vuln_id = vulnerability.display_id,
    entity_name = entityName(affected_entity.id),
    severity = vulnerability.severity,
    cvss_score = vulnerability.cvss_score,
    davis_score = davis.assessment.risk_score,
    function_in_use = davis.assessment.vulnerable_function_in_use
| fields vuln_id, entity_name, severity, cvss_score, davis_score, function_in_use
| sort davis_score desc
```

### 2. High-Priority Vulnerabilities (Function In Use)

Get vulnerabilities where the vulnerable function is actually being executed:

```dql
fetch security.events, from:now() - 7d
| filter event.type == "VULNERABILITY_STATE_REPORT_EVENT"
| dedup {vulnerability.display_id, affected_entity.id}, sort: {timestamp desc}
| filter vulnerability.resolution_status == "OPEN"
| filter davis.assessment.vulnerable_function_in_use == true
| filter vulnerability.severity in ["CRITICAL", "HIGH"]
| fieldsAdd 
    vuln_id = vulnerability.display_id,
    entity_name = entityName(affected_entity.id),
    severity = vulnerability.severity,
    davis_score = davis.assessment.risk_score,
    public_exploit = davis.assessment.public_exploit_available,
    cve_ids = vulnerability.references.cve
| fields vuln_id, entity_name, severity, davis_score, public_exploit, cve_ids
| sort davis_score desc
```

## Key Concepts

### 1. Deduplication (CRITICAL)

Always use deduplication to get the current state of vulnerabilities:

```dql
| dedup {vulnerability.display_id, affected_entity.id}, sort: {timestamp desc}
```

**Why?** Dynatrace creates multiple events over time for the same vulnerability. Without deduplication, you'll count the same vulnerability multiple times.

### 2. Davis AI Assessments

Dynatrace's Davis AI provides runtime assessments that are **more important than CVSS scores** for prioritization:

| Field | Description | Priority Impact |
|-------|-------------|-----------------|
| `davis.assessment.vulnerable_function_in_use` | Is the vulnerable code actually executed? | 🔴 CRITICAL - If false, vulnerability may not be exploitable |
| `davis.assessment.public_exploit_available` | Are public exploits available? | 🔴 HIGH - Increases real-world risk |
| `davis.assessment.risk_score` | Davis-calculated risk (0-10) | 🔴 HIGH - Runtime-aware scoring |
| `davis.assessment.risk_level` | Davis risk level | 🟡 MEDIUM - Simplified categorization |
| `davis.assessment.reachable_data_asset` | Can access sensitive data? | 🟡 MEDIUM - Data exposure risk |

### 3. Prioritization Logic

Recommended priority order:

1. **P1 (CRITICAL):** `function_in_use == true` AND `public_exploit == true`
2. **P2 (HIGH):** `function_in_use == true` AND `severity in ["CRITICAL", "HIGH"]`
3. **P3 (MEDIUM):** `davis.assessment.risk_score > 7.0`
4. **P4 (LOW):** `severity in ["CRITICAL", "HIGH"]` (but function not in use)

### 4. Query Timeframes

Choose appropriate timeframes based on scan frequency:

- **7 days:** Standard for regular vulnerability scans
- **30 days:** For cloud compliance or infrequent scans
- **24 hours:** For recent/new vulnerability discovery

```dql
fetch security.events, from:now() - 7d  // Standard
fetch security.events, from:now() - 30d // Cloud compliance
fetch security.events, from:now() - 24h // Recent only
```

## Common Use Cases

### Use Case 1: Dependency Vulnerability Audit

Get all vulnerabilities grouped by vulnerable component:

```dql
fetch security.events, from:now() - 7d
| filter event.type == "VULNERABILITY_STATE_REPORT_EVENT"
| dedup {vulnerability.display_id, affected_entity.id}, sort: {timestamp desc}
| filter vulnerability.resolution_status == "OPEN"
| summarize 
    total_vulns = count(),
    critical_count = countIf(vulnerability.severity == "CRITICAL"),
    function_in_use_count = countIf(davis.assessment.vulnerable_function_in_use == true),
    affected_entities = countDistinct(affected_entity.id),
    by: {
        component = vulnerability.vulnerable_component,
        severity = vulnerability.severity
    }
| sort critical_count desc, total_vulns desc
```

### Use Case 2: CVE Cross-Reference

Match vulnerabilities with specific CVEs (useful for Dependabot integration):

```dql
fetch security.events, from:now() - 7d
| filter event.type == "VULNERABILITY_STATE_REPORT_EVENT"
| dedup {vulnerability.display_id, affected_entity.id}, sort: {timestamp desc}
| filter vulnerability.resolution_status == "OPEN"
| expand vulnerability.references.cve
| filter vulnerability.references.cve == "CVE-2024-12345"  // Replace with target CVE
| fieldsAdd 
    entity_name = entityName(affected_entity.id),
    vuln_id = vulnerability.display_id,
    severity = vulnerability.severity,
    function_in_use = davis.assessment.vulnerable_function_in_use,
    component = vulnerability.vulnerable_component
| fields entity_name, vuln_id, severity, function_in_use, component
```

### Use Case 3: Entity-Specific Vulnerabilities

Get all vulnerabilities for a specific service or process group:

```dql
fetch security.events, from:now() - 7d
| filter event.type == "VULNERABILITY_STATE_REPORT_EVENT"
| filter affected_entity.id == "PROCESS_GROUP-XXXXXXXXXXXXX"  // Replace with entity ID
| dedup {vulnerability.display_id, affected_entity.id}, sort: {timestamp desc}
| filter vulnerability.resolution_status == "OPEN"
| fieldsAdd 
    vuln_id = vulnerability.display_id,
    title = vulnerability.title,
    severity = vulnerability.severity,
    cvss_score = vulnerability.cvss_score,
    davis_score = davis.assessment.risk_score,
    function_in_use = davis.assessment.vulnerable_function_in_use,
    cve_ids = vulnerability.references.cve
| fields vuln_id, title, severity, cvss_score, davis_score, function_in_use, cve_ids
| sort davis_score desc
```

### Use Case 4: Technology-Specific Analysis

Analyze vulnerabilities by technology stack:

```dql
fetch security.events, from:now() - 7d
| filter event.type == "VULNERABILITY_STATE_REPORT_EVENT"
| dedup {vulnerability.display_id, affected_entity.id}, sort: {timestamp desc}
| filter vulnerability.resolution_status == "OPEN"
| summarize 
    total_vulns = count(),
    critical_count = countIf(vulnerability.severity == "CRITICAL"),
    high_count = countIf(vulnerability.severity == "HIGH"),
    function_in_use = countIf(davis.assessment.vulnerable_function_in_use == true),
    affected_entities = countDistinct(affected_entity.id),
    by: {technology = vulnerability.technology}
| sort critical_count desc, high_count desc
```

## Field Reference

### Core Vulnerability Fields

| Field | Type | Description |
|-------|------|-------------|
| `vulnerability.display_id` | String | Unique vulnerability identifier |
| `vulnerability.title` | String | Human-readable vulnerability name |
| `vulnerability.severity` | Enum | CRITICAL, HIGH, MEDIUM, LOW |
| `vulnerability.cvss_score` | Number | CVSS score (0-10) |
| `vulnerability.technology` | String | JAVA, PYTHON, NODEJS, DOTNET, GO, etc. |
| `vulnerability.vulnerable_component` | String | Package/library with version |
| `vulnerability.resolution_status` | Enum | OPEN, RESOLVED, INVALID |
| `vulnerability.muted` | Boolean | Is vulnerability muted? |
| `vulnerability.first_seen_timestamp` | Timestamp | When first detected |
| `vulnerability.references.cve` | Array | CVE IDs (e.g., ["CVE-2023-12345"]) |

### Davis Assessment Fields

| Field | Type | Description |
|-------|------|-------------|
| `davis.assessment.risk_level` | String | Davis-adjusted risk level |
| `davis.assessment.risk_score` | Number | Davis risk score (0-10) |
| `davis.assessment.vulnerable_function_in_use` | Boolean | Is vulnerable code executed? |
| `davis.assessment.public_exploit_available` | Boolean | Is public exploit known? |
| `davis.assessment.reachable_data_asset` | Boolean | Can access sensitive data? |

### Affected Entity Fields

| Field | Type | Description |
|-------|------|-------------|
| `affected_entity.id` | String | Dynatrace entity ID (PROCESS_GROUP-XXX) |
| `affected_entity.type` | String | Entity type (PROCESS_GROUP, SERVICE, etc.) |
| `entityName(affected_entity.id)` | String | Human-readable entity name |

## Best Practices

### ✅ DO

1. **Always deduplicate** to get current state:
   ```dql
   | dedup {vulnerability.display_id, affected_entity.id}, sort: {timestamp desc}
   ```

2. **Prioritize by Davis assessments**, not just CVSS:
   ```dql
   | sort davis.assessment.risk_score desc, vulnerability.cvss_score desc
   ```

3. **Use appropriate timeframes** (7d standard, 30d for cloud):
   ```dql
   fetch security.events, from:now() - 7d
   ```

4. **Include human-readable entity names**:
   ```dql
   | fieldsAdd entity_name = entityName(affected_entity.id)
   ```

5. **Filter for function-in-use for true risk**:
   ```dql
   | filter davis.assessment.vulnerable_function_in_use == true
   ```

### ❌ DON'T

1. **Don't aggregate over time without dedup** (will count duplicates)
2. **Don't ignore Davis assessments** (they provide runtime context)
3. **Don't query only by CVSS** (vulnerable_function_in_use is critical)
4. **Don't use generic timeframes for all queries** (adjust based on scan frequency)
5. **Don't forget to filter for OPEN status** (unless you want resolved vulnerabilities)

## Integration Examples

### GitHub Actions Integration

Use these queries in GitHub Actions workflows to fail builds on critical vulnerabilities:

```yaml
- name: Check Critical Vulnerabilities
  run: |
    # Query Dynatrace API with DQL
    # Fail if any CRITICAL vulnerabilities with function_in_use == true
```

### Dependabot Cross-Reference

Match Dependabot alerts with Dynatrace vulnerabilities:

```dql
fetch security.events, from:now() - 7d
| filter event.type == "VULNERABILITY_STATE_REPORT_EVENT"
| dedup {vulnerability.display_id, affected_entity.id}, sort: {timestamp desc}
| filter vulnerability.resolution_status == "OPEN"
| expand vulnerability.references.cve
| filter vulnerability.references.cve in ["CVE-2024-1234", "CVE-2024-5678"]
| fieldsAdd 
    entity_name = entityName(affected_entity.id),
    function_in_use = davis.assessment.vulnerable_function_in_use
| fields entity_name, vulnerability.references.cve, function_in_use
```

### Security Dashboard

Create a summary for security dashboards:

```dql
fetch security.events, from:now() - 7d
| filter event.type == "VULNERABILITY_STATE_REPORT_EVENT"
| dedup {vulnerability.display_id, affected_entity.id}, sort: {timestamp desc}
| filter vulnerability.resolution_status == "OPEN"
| summarize 
    total = count(),
    critical = countIf(vulnerability.severity == "CRITICAL"),
    high = countIf(vulnerability.severity == "HIGH"),
    medium = countIf(vulnerability.severity == "MEDIUM"),
    low = countIf(vulnerability.severity == "LOW"),
    function_in_use = countIf(davis.assessment.vulnerable_function_in_use == true),
    public_exploits = countIf(davis.assessment.public_exploit_available == true)
```

## Additional Resources

- [Dynatrace DQL Documentation](https://docs.dynatrace.com/docs/platform/grail/dynatrace-query-language)
- [Security Events Reference](https://docs.dynatrace.com/docs/shortlink/security-events)
- [Davis Security Assessments](https://docs.dynatrace.com/docs/platform-modules/application-security/vulnerability-analytics)

## Support

For issues or questions:
1. Check the `get-vulnerabilities.dql` file for inline examples
2. Review Dynatrace documentation
3. Create an issue in this repository

## License

This project follows the same license as the unguard repository.
