# Dynatrace Security Queries Guide

This document provides comprehensive DQL query examples and explanations for querying Dynatrace security events, specifically focusing on vulnerability analysis using Runtime Vulnerability Analytics (RVA).

## Table of Contents

1. [Overview](#overview)
2. [Querying Latest Vulnerabilities](#querying-latest-vulnerabilities)
3. [Vulnerability Verification and Assessment](#vulnerability-verification-and-assessment)
4. [Advanced Vulnerability Queries](#advanced-vulnerability-queries)
5. [Best Practices](#best-practices)

## Overview

Dynatrace Runtime Vulnerability Analytics (RVA) provides real-time vulnerability detection and assessment for running applications. All security findings are stored in the `security.events` table and can be queried using DQL (Dynatrace Query Language).

### Key Concepts

- **Security Events**: Stored in `security.events` table
- **Event Types**: 
  - `VULNERABILITY_STATE_REPORT_EVENT` - Vulnerability findings
  - `DETECTION_FINDING` - Runtime Attack Protection detections
  - `COMPLIANCE_FINDING` - Compliance violations
- **Davis Assessment**: AI-powered risk assessment including:
  - `vulnerable_function_in_use` - Whether vulnerable code is actually executed
  - `public_exploit_available` - Availability of public exploits
  - `public_internet_exposure` - Public network exposure
  - `data_assets_within_reach` - Sensitive data accessibility

## Querying Latest Vulnerabilities

### 1. Get All OPEN Vulnerabilities (Last 7 Days)

This query retrieves all open, non-muted vulnerabilities detected by Dynatrace RVA in the last 7 days:

```dql
fetch security.events, from:now()-7d
| filter dt.system.bucket=="default_securityevents_builtin"
     AND event.provider=="Dynatrace"
     AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
     AND event.level=="ENTITY"
// filter for the latest snapshot per entity
| dedup {vulnerability.display_id, affected_entity.id}, sort:{timestamp desc}
// filter for open non-muted vulnerabilities
| filter vulnerability.resolution.status == "OPEN"
     AND vulnerability.parent.mute.status != "MUTED"
     AND vulnerability.mute.status != "MUTED"
// now summarize on the vulnerability level
| summarize{
    vulnerability.risk.score=round(takeMax(vulnerability.risk.score),decimals:1),
    vulnerability.title=takeFirst(vulnerability.title),
    vulnerability.references.cve=takeFirst(vulnerability.references.cve),
    last_detected=coalesce(takeMax(vulnerability.resolution.change_date),takeMax(vulnerability.parent.first_seen)),
    affected_entities=countDistinctExact(affected_entity.id),
    vulnerable_function_in_use=if(in("IN_USE",collectArray(vulnerability.davis_assessment.vulnerable_function_status)),true, else:false),
    public_internet_exposure=if(in("PUBLIC_NETWORK",collectArray(vulnerability.davis_assessment.exposure_status)),true,else:false),
    public_exploit_available=if(in("AVAILABLE",collectArray(vulnerability.davis_assessment.exploit_status)),true,else:false),
    data_assets_within_reach=if(in("REACHABLE",collectArray(vulnerability.davis_assessment.data_assets_status)),true,else:false)
}, by: {vulnerability.display_id}
// map the risk level
| fieldsAdd vulnerability.risk.level=if(vulnerability.risk.score>=9,"CRITICAL",
                                     else:if(vulnerability.risk.score>=7,"HIGH",
                                     else:if(vulnerability.risk.score>=4,"MEDIUM",
                                     else:if(vulnerability.risk.score>=0.1,"LOW",
                                     else:"NONE"))))
| sort {vulnerability.risk.score, direction:"descending"}, {affected_entities, direction:"descending"}
```

### 2. Get CRITICAL and HIGH Vulnerabilities Only

Filter for the most severe vulnerabilities:

```dql
fetch security.events, from:now()-7d
| filter dt.system.bucket=="default_securityevents_builtin"
     AND event.provider=="Dynatrace"
     AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
     AND event.level=="ENTITY"
| dedup {vulnerability.display_id, affected_entity.id}, sort:{timestamp desc}
| filter vulnerability.resolution.status == "OPEN"
     AND vulnerability.parent.mute.status != "MUTED"
     AND vulnerability.mute.status != "MUTED"
| summarize{
    vulnerability.risk.score=round(takeMax(vulnerability.risk.score),decimals:1),
    vulnerability.title=takeFirst(vulnerability.title),
    vulnerability.references.cve=takeFirst(vulnerability.references.cve),
    last_detected=coalesce(takeMax(vulnerability.resolution.change_date),takeMax(vulnerability.parent.first_seen)),
    affected_entities=countDistinctExact(affected_entity.id),
    vulnerable_function_in_use=if(in("IN_USE",collectArray(vulnerability.davis_assessment.vulnerable_function_status)),true, else:false),
    public_internet_exposure=if(in("PUBLIC_NETWORK",collectArray(vulnerability.davis_assessment.exposure_status)),true,else:false),
    public_exploit_available=if(in("AVAILABLE",collectArray(vulnerability.davis_assessment.exploit_status)),true,else:false),
    data_assets_within_reach=if(in("REACHABLE",collectArray(vulnerability.davis_assessment.data_assets_status)),true,else:false)
}, by: {vulnerability.display_id}
| fieldsAdd vulnerability.risk.level=if(vulnerability.risk.score>=9,"CRITICAL",
                                     else:if(vulnerability.risk.score>=7,"HIGH",
                                     else:if(vulnerability.risk.score>=4,"MEDIUM",
                                     else:if(vulnerability.risk.score>=0.1,"LOW",
                                     else:"NONE"))))
// Filter for CRITICAL and HIGH only
| filter vulnerability.risk.level in ["CRITICAL", "HIGH"]
| sort {vulnerability.risk.score, direction:"descending"}, {affected_entities, direction:"descending"}
```

### 3. Get Vulnerabilities with Functions In Use

Focus on vulnerabilities where the vulnerable code is actually being executed:

```dql
fetch security.events, from:now()-7d
| filter dt.system.bucket=="default_securityevents_builtin"
     AND event.provider=="Dynatrace"
     AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
     AND event.level=="ENTITY"
| dedup {vulnerability.display_id, affected_entity.id}, sort:{timestamp desc}
| filter vulnerability.resolution.status == "OPEN"
     AND vulnerability.parent.mute.status != "MUTED"
     AND vulnerability.mute.status != "MUTED"
     AND vulnerability.davis_assessment.vulnerable_function_status == "IN_USE"
| summarize{
    vulnerability.risk.score=round(takeMax(vulnerability.risk.score),decimals:1),
    vulnerability.title=takeFirst(vulnerability.title),
    vulnerability.references.cve=takeFirst(vulnerability.references.cve),
    last_detected=coalesce(takeMax(vulnerability.resolution.change_date),takeMax(vulnerability.parent.first_seen)),
    affected_entities=countDistinctExact(affected_entity.id),
    public_internet_exposure=if(in("PUBLIC_NETWORK",collectArray(vulnerability.davis_assessment.exposure_status)),true,else:false),
    public_exploit_available=if(in("AVAILABLE",collectArray(vulnerability.davis_assessment.exploit_status)),true,else:false),
    data_assets_within_reach=if(in("REACHABLE",collectArray(vulnerability.davis_assessment.data_assets_status)),true,else:false)
}, by: {vulnerability.display_id}
| fieldsAdd vulnerability.risk.level=if(vulnerability.risk.score>=9,"CRITICAL",
                                     else:if(vulnerability.risk.score>=7,"HIGH",
                                     else:if(vulnerability.risk.score>=4,"MEDIUM",
                                     else:if(vulnerability.risk.score>=0.1,"LOW",
                                     else:"NONE"))))
| sort {vulnerability.risk.score, direction:"descending"}
```

## Vulnerability Verification and Assessment

### 4. Query Specific CVE Across All Vulnerabilities

Look up a specific CVE to see if it exists in your environment:

```dql
fetch security.events, from:now()-7d
| filter event.provider=="Dynatrace"
     AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
| filter in("CVE-2024-21508", vulnerability.references.cve)
| dedup {vulnerability.display_id, affected_entity.id}, sort:{timestamp desc}
| filter vulnerability.resolution.status == "OPEN"
| fields vulnerability.display_id, vulnerability.title, vulnerability.references.cve, 
         vulnerability.davis_assessment.vulnerable_function_status,
         vulnerability.risk.score, affected_entity.id, affected_entity.name
```

### 5. Get Vulnerabilities for Specific Process or Service

Filter vulnerabilities affecting specific process group instances:

```dql
fetch security.events, from:now()-7d
| filter dt.system.bucket=="default_securityevents_builtin"
     AND event.provider=="Dynatrace"
     AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
     AND event.level=="ENTITY"
| dedup {vulnerability.display_id, affected_entity.id}, sort:{timestamp desc}
| filter vulnerability.resolution.status == "OPEN"
     AND vulnerability.parent.mute.status != "MUTED"
     AND vulnerability.mute.status != "MUTED"
     // Replace with actual process IDs
     AND (in({"PROCESS_GROUP_INSTANCE-123","PROCESS_GROUP_INSTANCE-456"},affected_entity.affected_processes.ids) 
          OR in(affected_entity.affected_processes.ids,{"PROCESS_GROUP_INSTANCE-123", "PROCESS_GROUP_INSTANCE-456"}))
| summarize{
    vulnerability.risk.score=round(takeMax(vulnerability.risk.score),decimals:1),
    vulnerability.title=takeFirst(vulnerability.title),
    vulnerability.references.cve=takeFirst(vulnerability.references.cve),
    last_detected=coalesce(takeMax(vulnerability.resolution.change_date),takeMax(vulnerability.parent.first_seen)),
    affected_entities=countDistinctExact(affected_entity.id),
    vulnerable_function_in_use=if(in("IN_USE",collectArray(vulnerability.davis_assessment.vulnerable_function_status)),true, else:false),
    public_internet_exposure=if(in("PUBLIC_NETWORK",collectArray(vulnerability.davis_assessment.exposure_status)),true,else:false),
    public_exploit_available=if(in("AVAILABLE",collectArray(vulnerability.davis_assessment.exploit_status)),true,else:false),
    data_assets_within_reach=if(in("REACHABLE",collectArray(vulnerability.davis_assessment.data_assets_status)),true,else:false)
}, by: {vulnerability.display_id}
| fieldsAdd vulnerability.risk.level=if(vulnerability.risk.score>=9,"CRITICAL",
                                     else:if(vulnerability.risk.score>=7,"HIGH",
                                     else:if(vulnerability.risk.score>=4,"MEDIUM",
                                     else:if(vulnerability.risk.score>=0.1,"LOW",
                                     else:"NONE"))))
| sort {vulnerability.risk.score, direction:"descending"}
```

### 6. Get Vulnerabilities Affecting a Specific Host

Find vulnerabilities directly or indirectly affecting a specific host:

```dql
fetch security.events, from:now()-7d
| filter dt.system.bucket=="default_securityevents_builtin"
     AND event.provider=="Dynatrace"
     AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
     AND event.level=="ENTITY"
| dedup {vulnerability.display_id, affected_entity.id}, sort:{timestamp desc}
| filter vulnerability.resolution.status == "OPEN"
     AND vulnerability.parent.mute.status != "MUTED"
     AND vulnerability.mute.status != "MUTED"
     // Replace 'your-host-name' with actual host name
     AND (in("your-host-name",related_entities.hosts.names) OR affected_entity.name=="your-host-name")
| summarize{
    vulnerability.risk.score=round(takeMax(vulnerability.risk.score),decimals:1),
    vulnerability.title=takeFirst(vulnerability.title),
    vulnerability.references.cve=takeFirst(vulnerability.references.cve),
    last_detected=coalesce(takeMax(vulnerability.resolution.change_date),takeMax(vulnerability.parent.first_seen)),
    affected_entities=countDistinctExact(affected_entity.id),
    vulnerable_function_in_use=if(in("IN_USE",collectArray(vulnerability.davis_assessment.vulnerable_function_status)),true, else:false),
    public_internet_exposure=if(in("PUBLIC_NETWORK",collectArray(vulnerability.davis_assessment.exposure_status)),true,else:false),
    public_exploit_available=if(in("AVAILABLE",collectArray(vulnerability.davis_assessment.exploit_status)),true,else:false),
    data_assets_within_reach=if(in("REACHABLE",collectArray(vulnerability.davis_assessment.data_assets_status)),true,else:false)
}, by: {vulnerability.display_id}
| fieldsAdd vulnerability.risk.level=if(vulnerability.risk.score>=9,"CRITICAL",
                                     else:if(vulnerability.risk.score>=7,"HIGH",
                                     else:if(vulnerability.risk.score>=4,"MEDIUM",
                                     else:if(vulnerability.risk.score>=0.1,"LOW",
                                     else:"NONE"))))
| sort {vulnerability.risk.score, direction:"descending"}
```

## Advanced Vulnerability Queries

### 7. Vulnerability Summary by Severity Level

Get a count of vulnerabilities grouped by severity:

```dql
fetch security.events, from:now()-7d
| filter dt.system.bucket=="default_securityevents_builtin"
     AND event.provider=="Dynatrace"
     AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
     AND event.level=="ENTITY"
| dedup {vulnerability.display_id, affected_entity.id}, sort:{timestamp desc}
| filter vulnerability.resolution.status == "OPEN"
     AND vulnerability.parent.mute.status != "MUTED"
     AND vulnerability.mute.status != "MUTED"
| summarize{
    vulnerability.risk.score=round(takeMax(vulnerability.risk.score),decimals:1),
    affected_entities=countDistinctExact(affected_entity.id)
}, by: {vulnerability.display_id}
| fieldsAdd vulnerability.risk.level=if(vulnerability.risk.score>=9,"CRITICAL",
                                     else:if(vulnerability.risk.score>=7,"HIGH",
                                     else:if(vulnerability.risk.score>=4,"MEDIUM",
                                     else:if(vulnerability.risk.score>=0.1,"LOW",
                                     else:"NONE"))))
| summarize 
    vulnerability_count=count(),
    total_affected_entities=sum(affected_entities),
    by: {vulnerability.risk.level}
| sort vulnerability.risk.level
```

### 8. Vulnerabilities with Public Exploit Available

Focus on vulnerabilities with known public exploits:

```dql
fetch security.events, from:now()-7d
| filter dt.system.bucket=="default_securityevents_builtin"
     AND event.provider=="Dynatrace"
     AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
     AND event.level=="ENTITY"
| dedup {vulnerability.display_id, affected_entity.id}, sort:{timestamp desc}
| filter vulnerability.resolution.status == "OPEN"
     AND vulnerability.parent.mute.status != "MUTED"
     AND vulnerability.mute.status != "MUTED"
     AND vulnerability.davis_assessment.exploit_status == "AVAILABLE"
| summarize{
    vulnerability.risk.score=round(takeMax(vulnerability.risk.score),decimals:1),
    vulnerability.title=takeFirst(vulnerability.title),
    vulnerability.references.cve=takeFirst(vulnerability.references.cve),
    last_detected=coalesce(takeMax(vulnerability.resolution.change_date),takeMax(vulnerability.parent.first_seen)),
    affected_entities=countDistinctExact(affected_entity.id),
    vulnerable_function_in_use=if(in("IN_USE",collectArray(vulnerability.davis_assessment.vulnerable_function_status)),true, else:false),
    public_internet_exposure=if(in("PUBLIC_NETWORK",collectArray(vulnerability.davis_assessment.exposure_status)),true,else:false),
    data_assets_within_reach=if(in("REACHABLE",collectArray(vulnerability.davis_assessment.data_assets_status)),true,else:false)
}, by: {vulnerability.display_id}
| fieldsAdd vulnerability.risk.level=if(vulnerability.risk.score>=9,"CRITICAL",
                                     else:if(vulnerability.risk.score>=7,"HIGH",
                                     else:if(vulnerability.risk.score>=4,"MEDIUM",
                                     else:if(vulnerability.risk.score>=0.1,"LOW",
                                     else:"NONE"))))
| sort {vulnerability.risk.score, direction:"descending"}
```

### 9. Publicly Exposed Vulnerabilities

Identify vulnerabilities in publicly accessible services:

```dql
fetch security.events, from:now()-7d
| filter dt.system.bucket=="default_securityevents_builtin"
     AND event.provider=="Dynatrace"
     AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
     AND event.level=="ENTITY"
| dedup {vulnerability.display_id, affected_entity.id}, sort:{timestamp desc}
| filter vulnerability.resolution.status == "OPEN"
     AND vulnerability.parent.mute.status != "MUTED"
     AND vulnerability.mute.status != "MUTED"
     AND vulnerability.davis_assessment.exposure_status == "PUBLIC_NETWORK"
| summarize{
    vulnerability.risk.score=round(takeMax(vulnerability.risk.score),decimals:1),
    vulnerability.title=takeFirst(vulnerability.title),
    vulnerability.references.cve=takeFirst(vulnerability.references.cve),
    last_detected=coalesce(takeMax(vulnerability.resolution.change_date),takeMax(vulnerability.parent.first_seen)),
    affected_entities=countDistinctExact(affected_entity.id),
    vulnerable_function_in_use=if(in("IN_USE",collectArray(vulnerability.davis_assessment.vulnerable_function_status)),true, else:false),
    public_exploit_available=if(in("AVAILABLE",collectArray(vulnerability.davis_assessment.exploit_status)),true,else:false),
    data_assets_within_reach=if(in("REACHABLE",collectArray(vulnerability.davis_assessment.data_assets_status)),true,else:false)
}, by: {vulnerability.display_id}
| fieldsAdd vulnerability.risk.level=if(vulnerability.risk.score>=9,"CRITICAL",
                                     else:if(vulnerability.risk.score>=7,"HIGH",
                                     else:if(vulnerability.risk.score>=4,"MEDIUM",
                                     else:if(vulnerability.risk.score>=0.1,"LOW",
                                     else:"NONE"))))
| sort {vulnerability.risk.score, direction:"descending"}
```

### 10. High-Risk Vulnerabilities (Multiple Risk Factors)

Find vulnerabilities with multiple risk factors (function in use + public exploit + public exposure):

```dql
fetch security.events, from:now()-7d
| filter dt.system.bucket=="default_securityevents_builtin"
     AND event.provider=="Dynatrace"
     AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
     AND event.level=="ENTITY"
| dedup {vulnerability.display_id, affected_entity.id}, sort:{timestamp desc}
| filter vulnerability.resolution.status == "OPEN"
     AND vulnerability.parent.mute.status != "MUTED"
     AND vulnerability.mute.status != "MUTED"
| summarize{
    vulnerability.risk.score=round(takeMax(vulnerability.risk.score),decimals:1),
    vulnerability.title=takeFirst(vulnerability.title),
    vulnerability.references.cve=takeFirst(vulnerability.references.cve),
    last_detected=coalesce(takeMax(vulnerability.resolution.change_date),takeMax(vulnerability.parent.first_seen)),
    affected_entities=countDistinctExact(affected_entity.id),
    vulnerable_function_in_use=if(in("IN_USE",collectArray(vulnerability.davis_assessment.vulnerable_function_status)),true, else:false),
    public_internet_exposure=if(in("PUBLIC_NETWORK",collectArray(vulnerability.davis_assessment.exposure_status)),true,else:false),
    public_exploit_available=if(in("AVAILABLE",collectArray(vulnerability.davis_assessment.exploit_status)),true,else:false),
    data_assets_within_reach=if(in("REACHABLE",collectArray(vulnerability.davis_assessment.data_assets_status)),true,else:false)
}, by: {vulnerability.display_id}
| fieldsAdd vulnerability.risk.level=if(vulnerability.risk.score>=9,"CRITICAL",
                                     else:if(vulnerability.risk.score>=7,"HIGH",
                                     else:if(vulnerability.risk.score>=4,"MEDIUM",
                                     else:if(vulnerability.risk.score>=0.1,"LOW",
                                     else:"NONE"))))
// Filter for high-risk combination
| filter vulnerable_function_in_use == true 
     AND public_exploit_available == true
     AND public_internet_exposure == true
| sort {vulnerability.risk.score, direction:"descending"}
```

## Best Practices

### 1. Always Use Deduplication

When querying vulnerability state reports, always use deduplication to get the latest snapshot per entity:

```dql
| dedup {vulnerability.display_id, affected_entity.id}, sort:{timestamp desc}
```

This ensures you're looking at the current state, not historical data.

### 2. Filter for Open Vulnerabilities

Always filter for open, non-muted vulnerabilities to focus on actionable items:

```dql
| filter vulnerability.resolution.status == "OPEN"
     AND vulnerability.parent.mute.status != "MUTED"
     AND vulnerability.mute.status != "MUTED"
```

### 3. Use Appropriate Time Ranges

- **7 days** - Standard for vulnerability analysis (weekly scans)
- **24 hours** - Recent vulnerabilities only
- **30 days** - Long-term trends and compliance analysis

### 4. Prioritize by Davis Assessment

Focus on vulnerabilities where:
- `vulnerable_function_in_use == true` - The vulnerable code is actually executed
- `public_exploit_available == true` - Public exploits exist
- `public_internet_exposure == true` - Service is publicly accessible
- `data_assets_within_reach == true` - Sensitive data is accessible

### 5. Risk Level Mapping

Dynatrace uses the following risk score to level mapping:
- **CRITICAL**: Score ≥ 9.0
- **HIGH**: Score ≥ 7.0
- **MEDIUM**: Score ≥ 4.0
- **LOW**: Score ≥ 0.1
- **NONE**: Score < 0.1

### 6. Verification Workflow for Dependabot/GHAS Alerts

When verifying alerts from external sources:

1. Query by CVE to check if Dynatrace detected it:
   ```dql
   | filter in("CVE-YYYY-NNNNN", vulnerability.references.cve)
   ```

2. Check if vulnerable function is in use:
   ```dql
   | fields vulnerability.davis_assessment.vulnerable_function_status
   ```

3. Decision criteria:
   - **Confirmed**: CVE found in Dynatrace + function IN_USE → Fix immediately
   - **Not Confirmed**: CVE found but function NOT_IN_USE → Lower priority
   - **Not Detected**: CVE not in Dynatrace → Dismiss with reason "Not observed in runtime"

### 7. Entity Reporting Format

When reporting affected entities, always use the format: `name(ID)`

Example: `unguard-proxy-service-* (PROCESS_GROUP-CE7F92ECB243E595)`

## Quick Reference

### Common Filters

```dql
// Provider and event type
| filter event.provider=="Dynatrace"
| filter event.type=="VULNERABILITY_STATE_REPORT_EVENT"

// Vulnerability status
| filter vulnerability.resolution.status == "OPEN"
| filter vulnerability.resolution.status == "RESOLVED"

// Davis assessments
| filter vulnerability.davis_assessment.vulnerable_function_status == "IN_USE"
| filter vulnerability.davis_assessment.exploit_status == "AVAILABLE"
| filter vulnerability.davis_assessment.exposure_status == "PUBLIC_NETWORK"
| filter vulnerability.davis_assessment.data_assets_status == "REACHABLE"

// Risk level (after mapping)
| filter vulnerability.risk.level in ["CRITICAL", "HIGH"]
```

### Key Fields

- `vulnerability.display_id` - Unique vulnerability identifier
- `vulnerability.title` - Human-readable title
- `vulnerability.references.cve` - CVE identifier(s)
- `vulnerability.risk.score` - Davis risk score (0-10)
- `vulnerability.resolution.status` - OPEN/RESOLVED/MUTED
- `affected_entity.id` - Entity ID affected by vulnerability
- `affected_entity.name` - Entity name
- `vulnerability.davis_assessment.*` - AI-powered risk assessments

## Additional Resources

- [Dynatrace Security Events Documentation](https://docs.dynatrace.com/docs/shortlink/security-events-examples)
- [DQL Reference Guide](https://docs.dynatrace.com/docs/observe-and-explore/query-data/dynatrace-query-language)
- [Runtime Vulnerability Analytics](https://docs.dynatrace.com/docs/security/runtime-application-protection/runtime-vulnerability-analytics)

---

**Note**: Replace placeholder values (like process IDs, host names, or CVE numbers) with actual values from your environment when using these queries.
