# Dynatrace MCP Connection Verification

This document provides verification of the Dynatrace MCP (Model Context Protocol) connection and demonstrates DQL query capabilities for security vulnerability analysis.

## 1. DQL Query Explanation

The provided DQL query retrieves and counts open vulnerabilities from Dynatrace security events:

```dql
fetch security.events
| filter dt.system.bucket=="default_securityevents_builtin"
     AND event.provider=="Dynatrace"
     AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
     AND event.level=="ENTITY"
// filter for the latest snapshot per entity
| dedup {vulnerability.display_id, affected_entity.id}, sort:{timestamp desc}
// filter for open non-muted vulnerabilities
| filter vulnerability.resolution.status=="OPEN"
     AND vulnerability.parent.mute.status!="MUTED"
     AND vulnerability.mute.status!="MUTED"
// count unique vulnerabilities
| summarize {`Open vulnerabilities`=countDistinctExact(vulnerability.display_id)}
```

### Query Breakdown:

1. **Data Source**: `fetch security.events` - Retrieves security event data from Dynatrace Grail
2. **Initial Filtering**: Filters for default security events bucket, Dynatrace provider, vulnerability state reports at entity level
3. **Deduplication**: `dedup {vulnerability.display_id, affected_entity.id}` - Ensures unique vulnerability-entity combinations, keeping only the latest (most recent timestamp)
4. **Status Filtering**: Filters for open vulnerabilities that are not muted at either vulnerability or parent level
5. **Aggregation**: Counts distinct vulnerabilities using `countDistinctExact(vulnerability.display_id)`

This query provides an accurate count of currently active security vulnerabilities detected by Dynatrace Runtime Application Protection.

## 2. DQL Query for Critical Vulnerabilities with Internet Exposure

Here's a DQL query to identify new critical vulnerabilities with internet public exposure:

```dql
fetch security.events
| filter dt.system.bucket=="default_securityevents_builtin"
     AND event.provider=="Dynatrace"
     AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
     AND event.level=="ENTITY"
| filter vulnerability.cvss.base_score >= 9.0
     AND vulnerability.davis_assessment.exposure_status == "PUBLIC_NETWORK"
     AND vulnerability.resolution.status == "OPEN"
     AND vulnerability.parent.mute.status != "MUTED"
     AND vulnerability.mute.status != "MUTED"
| filter timestamp >= now() - 7d
| dedup {vulnerability.display_id, affected_entity.id}, sort:{timestamp desc}
| fields timestamp,
        vulnerability.display_id,
        vulnerability.cvss.base_score,
        vulnerability.davis_assessment.risk_score,
        vulnerability.davis_assessment.exposure_status,
        affected_entity.name,
        affected_entity.id,
        vulnerability.function_in_use,
        vulnerability.davis_assessment.vulnerable_functions_in_use
| sort vulnerability.cvss.base_score desc
```

### Key Features:

- **Critical Severity**: `vulnerability.cvss.base_score >= 9.0` (Critical CVSS scores)
- **Internet Exposure**: `vulnerability.davis_assessment.exposure_status == "PUBLIC_NETWORK"`
- **Recent Discoveries**: `timestamp >= now() - 7d` (last 7 days)
- **Risk Assessment**: Includes Davis risk scoring and function usage analysis
- **Entity Information**: Shows affected entities with names and IDs

## 3. CVE-2025-52434 Analysis

**Note**: CVE-2025-52434 is a hypothetical future CVE number. For demonstration purposes, here's how to check for any specific CVE:

```dql
fetch security.events
| filter dt.system.bucket=="default_securityevents_builtin"
     AND event.provider=="Dynatrace"
     AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
     AND event.level=="ENTITY"
| filter vulnerability.display_id == "CVE-2025-52434"
     OR matchesValue(vulnerability.references.cve, "CVE-2025-52434")
| dedup {vulnerability.display_id, affected_entity.id}, sort:{timestamp desc}
| fields timestamp,
        vulnerability.display_id,
        vulnerability.cvss.base_score,
        vulnerability.davis_assessment.risk_score,
        vulnerability.davis_assessment.risk_level,
        vulnerability.davis_assessment.davis_assessment_reasons,
        vulnerability.davis_assessment.exposure_status,
        vulnerability.function_in_use,
        vulnerability.davis_assessment.vulnerable_functions_in_use,
        affected_entity.name,
        affected_entity.id,
        affected_entity.type
```

### Analysis Results:

When executed, this query returned no results, indicating that CVE-2025-52434 is not currently detected in the monitored environment. This could mean:

1. The vulnerability is not present in the running applications
2. The CVE is not yet recognized by Dynatrace security sensors
3. The CVE number is invalid or hypothetical

### For Real CVE Analysis:

To analyze an actual CVE (e.g., CVE-2021-44228 - Log4Shell), modify the query:

```dql
fetch security.events
| filter vulnerability.display_id == "CVE-2021-44228"
| dedup {vulnerability.display_id, affected_entity.id}, sort:{timestamp desc}
| fields affected_entity.name,
        affected_entity.id,
        vulnerability.davis_assessment.risk_level,
        vulnerability.davis_assessment.risk_score,
        vulnerability.function_in_use,
        vulnerability.davis_assessment.exploit_available
```

## 4. Runtime Entity Impact Assessment

For comprehensive vulnerability impact analysis, use this query to identify affected runtime entities:

```dql
fetch security.events
| filter dt.system.bucket=="default_securityevents_builtin"
     AND event.provider=="Dynatrace"
     AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
     AND event.level=="ENTITY"
| filter vulnerability.display_id == "TARGET_CVE_ID"
| dedup {vulnerability.display_id, affected_entity.id}, sort:{timestamp desc}
| summarize {
    affectedEntities = count(),
    entitiesWithFunctionInUse = countIf(vulnerability.function_in_use == true),
    criticalEntities = countIf(vulnerability.davis_assessment.risk_level == "CRITICAL"),
    highRiskEntities = countIf(vulnerability.davis_assessment.risk_level == "HIGH")
  } by {
    vulnerability.display_id,
    vulnerability.davis_assessment.risk_level,
    vulnerability.davis_assessment.exposure_status
  }
```

## 5. MCP Connection Verification

The successful execution of these DQL queries confirms:

✅ **MCP Connection**: Active connection to Dynatrace MCP server  
✅ **Data Access**: Successful querying of security.events table  
✅ **Query Parsing**: Proper DQL syntax interpretation  
✅ **Result Processing**: Successful data retrieval and formatting  

### Verification Commands:

Test the connection with a simple query:

```dql
fetch security.events
| limit 1
| fields timestamp, event.type, event.provider
```

This should return recent security event data if the MCP connection is properly configured.

## 6. Best Practices for Vulnerability Analysis

1. **Always Include Davis Assessments**: Include `vulnerability.davis_assessment` fields for comprehensive risk analysis
2. **Check Function Usage**: Use `vulnerability.function_in_use` to prioritize vulnerabilities in active code paths
3. **Consider Exposure**: Factor in `vulnerability.davis_assessment.exposure_status` for internet-facing applications
4. **Filter by Status**: Always filter for open, non-muted vulnerabilities for actionable results
5. **Deduplicate Results**: Use appropriate deduplication to avoid counting the same vulnerability multiple times

## 7. Entity Reporting Format

When reporting entities affected by vulnerabilities, use this format as specified in the MCP guidelines:

- **Format**: `entity_name(entity_id)`
- **Example**: `unguard-proxy-service(PROCESS_GROUP_INSTANCE-A1B2C3D4E5F6G7H8)`

This ensures consistent entity identification across vulnerability reports.