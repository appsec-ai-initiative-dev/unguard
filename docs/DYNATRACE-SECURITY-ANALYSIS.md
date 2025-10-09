# Dynatrace Security Analysis with DQL

This document provides comprehensive guidance on using Dynatrace Query Language (DQL) for security vulnerability analysis within the Unguard application ecosystem.

## Overview

Dynatrace Runtime Vulnerability Analytics (RVA) provides real-time visibility into security vulnerabilities affecting running applications. This documentation covers DQL queries for analyzing security events, focusing on vulnerability detection, assessment, and prioritization.

## 1. Understanding the Basic Vulnerability Query

The following DQL query retrieves and counts open vulnerabilities from Dynatrace security events:

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

1. **Data Source**: `fetch security.events` - Retrieves data from the security events table
2. **Event Filtering**: 
   - `dt.system.bucket=="default_securityevents_builtin"` - Filters for built-in security events
   - `event.provider=="Dynatrace"` - Only Dynatrace-generated events
   - `event.type=="VULNERABILITY_STATE_REPORT_EVENT"` - Specifically vulnerability reports
   - `event.level=="ENTITY"` - Entity-level events only
3. **Deduplication**: `dedup {vulnerability.display_id, affected_entity.id}` - Ensures latest snapshot per vulnerability-entity combination
4. **Status Filtering**: Only open, non-muted vulnerabilities
5. **Aggregation**: Counts distinct vulnerabilities using `countDistinctExact()`

### Use Cases:
- Get a high-level count of active security issues
- Monitor vulnerability trends over time
- Establish baseline security metrics

## 2. DQL Query for Critical Vulnerabilities with Public Internet Exposure

To identify new critical vulnerabilities that have public internet exposure, use this enhanced query:

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
// filter for critical vulnerabilities with public exposure
| filter vulnerability.risk.score >= 9.0
     AND in("PUBLIC_NETWORK", vulnerability.davis_assessment.exposure_status)
// filter for recently detected vulnerabilities (last 7 days)
| filter vulnerability.parent.first_seen > now() - 7d
// summarize critical findings
| summarize {
    vulnerability.risk.score=round(takeMax(vulnerability.risk.score), decimals:1),
    vulnerability.title=takeFirst(vulnerability.title),
    vulnerability.references.cve=takeFirst(vulnerability.references.cve),
    first_detected=takeFirst(vulnerability.parent.first_seen),
    last_detected=coalesce(takeMax(vulnerability.resolution.change_date), takeMax(vulnerability.parent.first_seen)),
    affected_entities=countDistinctExact(affected_entity.id),
    vulnerable_function_in_use=if(in("IN_USE", collectArray(vulnerability.davis_assessment.vulnerable_function_status)), true, else:false),
    public_exploit_available=if(in("AVAILABLE", collectArray(vulnerability.davis_assessment.exploit_status)), true, else:false),
    data_assets_within_reach=if(in("REACHABLE", collectArray(vulnerability.davis_assessment.data_assets_status)), true, else:false),
    affected_entity_names=collectArray(affected_entity.name)
}, by: {vulnerability.display_id}
// add risk level mapping
| fieldsAdd vulnerability.risk.level="CRITICAL"
| sort {vulnerability.risk.score, direction:"descending"}, {first_detected, direction:"descending"}
```

### Key Features:
- **Critical Severity**: `vulnerability.risk.score >= 9.0` filters for CVSS scores of 9.0 and above
- **Public Exposure**: `in("PUBLIC_NETWORK", vulnerability.davis_assessment.exposure_status)` identifies internet-facing vulnerabilities
- **Recent Detection**: `vulnerability.parent.first_seen > now() - 7d` shows vulnerabilities discovered in the last 7 days
- **Davis Assessments**: Includes exploit availability, function usage, and data asset reachability
- **Entity Details**: Provides affected entity names and counts

### Business Impact:
This query helps prioritize the most critical security issues that pose immediate risk to public-facing applications.

## 3. CVE-2025-52434 Runtime Entity Analysis

To check which runtime entities are affected by the specific vulnerability CVE-2025-52434 and get Dynatrace's assessment:

```dql
fetch security.events
| filter dt.system.bucket=="default_securityevents_builtin"
     AND event.provider=="Dynatrace"
     AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
     AND event.level=="ENTITY"
// filter for the latest snapshot per entity
| dedup {vulnerability.display_id, affected_entity.id}, sort:{timestamp desc}
// filter for the specific CVE
| filter in("CVE-2025-52434", vulnerability.references.cve)
// include both open and resolved to get complete picture
| filter vulnerability.parent.mute.status!="MUTED"
     AND vulnerability.mute.status!="MUTED"
// get detailed information per affected entity
| fieldsAdd 
    entity_name = affected_entity.name,
    entity_id = affected_entity.id,
    entity_type = affected_entity.type,
    vulnerability_status = vulnerability.resolution.status,
    risk_score = round(vulnerability.risk.score, decimals:1),
    risk_level = if(vulnerability.risk.score>=9,"CRITICAL",
                 else:if(vulnerability.risk.score>=7,"HIGH",
                 else:if(vulnerability.risk.score>=4,"MEDIUM",
                 else:if(vulnerability.risk.score>=0.1,"LOW",
                 else:"NONE")))),
    function_in_use = vulnerability.davis_assessment.vulnerable_function_status,
    exposure_status = vulnerability.davis_assessment.exposure_status,
    exploit_available = vulnerability.davis_assessment.exploit_status,
    data_assets_status = vulnerability.davis_assessment.data_assets_status,
    first_seen = vulnerability.parent.first_seen,
    last_updated = coalesce(vulnerability.resolution.change_date, vulnerability.parent.first_seen)
// sort by risk and entity
| sort {risk_score, direction:"descending"}, {entity_name}
```

### Additional Context Query for CVE-2025-52434:

To get more context about the affected runtime entities, run this complementary query:

```dql
fetch dt.entity.container_group_instance, dt.entity.process_group_instance, dt.entity.software_component
| filter entityName != ""
// Add related entity information
| fieldsAdd 
    entity_type = if(entityId startsWith "CONTAINER_GROUP_INSTANCE", "Container",
                  else:if(entityId startsWith "PROCESS_GROUP_INSTANCE", "Process Group", 
                  else:if(entityId startsWith "SOFTWARE_COMPONENT", "Software Component", "Other"))),
    related_hosts = toString(contains[dt.entity.host]),
    related_services = toString(contains[dt.entity.service])
// Filter for entities that might be related to the vulnerability
| filter contains(entityName, "unguard") OR contains(entityName, "java") OR contains(entityName, "spring")
| sort entityName
```

### Query Insights:

1. **Entity Impact Assessment**: Shows exactly which containers, processes, or software components are affected
2. **Davis AI Analysis**: Provides Dynatrace AI's assessment of:
   - Whether vulnerable functions are actually in use
   - Network exposure status
   - Exploit availability
   - Data asset reachability
3. **Risk Prioritization**: Combines CVSS scores with runtime context
4. **Temporal Analysis**: Shows when vulnerabilities were first detected and last updated

### Interpretation Notes:

- **function_in_use = "IN_USE"**: High priority - vulnerable code is actively executing
- **function_in_use = "NOT_IN_USE"**: Lower priority - vulnerable code exists but isn't executed
- **exposure_status = "PUBLIC_NETWORK"**: Internet-facing, higher risk
- **exploit_available = "AVAILABLE"**: Public exploits exist, immediate attention needed
- **data_assets_status = "REACHABLE"**: Sensitive data potentially at risk

## Best Practices for Dynatrace Security Analysis

1. **Regular Monitoring**: Run vulnerability queries daily to track new threats
2. **Prioritization**: Focus on vulnerabilities with:
   - High CVSS scores (≥7.0)
   - Functions in use
   - Public network exposure
   - Available exploits
3. **Entity Context**: Always consider the runtime context when assessing impact
4. **Trend Analysis**: Monitor vulnerability trends over time to improve security posture
5. **Integration**: Combine Dynatrace findings with other security tools for comprehensive coverage

## Security Event Fields Reference

### Core Vulnerability Fields:
- `vulnerability.display_id`: Unique vulnerability identifier
- `vulnerability.title`: Human-readable vulnerability name
- `vulnerability.references.cve`: CVE identifier(s)
- `vulnerability.risk.score`: CVSS base score (0-10)
- `vulnerability.resolution.status`: OPEN, RESOLVED, etc.

### Davis Assessment Fields:
- `vulnerability.davis_assessment.vulnerable_function_status`: IN_USE, NOT_IN_USE
- `vulnerability.davis_assessment.exposure_status`: PUBLIC_NETWORK, PRIVATE_NETWORK
- `vulnerability.davis_assessment.exploit_status`: AVAILABLE, NOT_AVAILABLE
- `vulnerability.davis_assessment.data_assets_status`: REACHABLE, NOT_REACHABLE

### Entity Fields:
- `affected_entity.id`: Unique entity identifier
- `affected_entity.name`: Entity display name
- `affected_entity.type`: Entity type (HOST, PROCESS_GROUP, etc.)

This documentation provides the foundation for effective security vulnerability analysis using Dynatrace DQL queries within the Unguard application environment.