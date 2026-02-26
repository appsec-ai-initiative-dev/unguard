# Dynatrace Security Queries Guide

This document provides explanations and examples of Dynatrace DQL (Dynatrace Query Language) queries for security analysis, vulnerability management, and runtime verification.

## Table of Contents
1. [Query Explanation: Counting Open Vulnerabilities](#1-query-explanation-counting-open-vulnerabilities)
2. [Query: New Critical Vulnerabilities with Public Internet Exposure](#2-query-new-critical-vulnerabilities-with-public-internet-exposure)
3. [Runtime Entity Analysis for CVE-2025-52434](#3-runtime-entity-analysis-for-cve-2025-52434)

---

## 1. Query Explanation: Counting Open Vulnerabilities

### Query
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

### Explanation

This DQL query retrieves and counts all **open, non-muted vulnerabilities** detected by Dynatrace Runtime Vulnerability Analytics (RVA). Here's a breakdown of each section:

#### 1. Data Source Selection
```dql
fetch security.events
```
- Fetches data from the `security.events` table, which contains security-related events including vulnerabilities, detections, and compliance findings.

#### 2. Initial Filtering
```dql
| filter dt.system.bucket=="default_securityevents_builtin"
     AND event.provider=="Dynatrace"
     AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
     AND event.level=="ENTITY"
```
- **`dt.system.bucket=="default_securityevents_builtin"`**: Filters for Dynatrace's built-in security events bucket
- **`event.provider=="Dynatrace"`**: Ensures we only get vulnerabilities detected by Dynatrace RVA (not from external sources like GitHub Advanced Security, AWS Security Hub, etc.)
- **`event.type=="VULNERABILITY_STATE_REPORT_EVENT"`**: Filters specifically for vulnerability state reports (not detections or compliance findings)
- **`event.level=="ENTITY"`**: Focuses on entity-level vulnerability reports

#### 3. Deduplication
```dql
| dedup {vulnerability.display_id, affected_entity.id}, sort:{timestamp desc}
```
- Removes duplicate records for the same vulnerability on the same entity
- Uses the most recent record (sorted by timestamp in descending order)
- This ensures each unique vulnerability-entity pair appears only once with its latest state

#### 4. Status Filtering
```dql
| filter vulnerability.resolution.status=="OPEN"
     AND vulnerability.parent.mute.status!="MUTED"
     AND vulnerability.mute.status!="MUTED"
```
- **`vulnerability.resolution.status=="OPEN"`**: Only includes vulnerabilities that are currently open (not resolved or closed)
- **`vulnerability.parent.mute.status!="MUTED"`**: Excludes parent vulnerabilities that have been muted
- **`vulnerability.mute.status!="MUTED"`**: Excludes individual vulnerability instances that have been muted

#### 5. Aggregation
```dql
| summarize {`Open vulnerabilities`=countDistinctExact(vulnerability.display_id)}
```
- Counts the distinct number of unique vulnerabilities (by `vulnerability.display_id`)
- Returns a single number representing the total count of open, non-muted vulnerabilities across all affected entities

### Use Case
This query is useful for:
- Getting a quick overview of the current vulnerability landscape
- Tracking the total number of active security issues
- Monitoring security posture over time
- Creating dashboards or alerts based on vulnerability counts

---

## 2. Query: New Critical Vulnerabilities with Public Internet Exposure

### Query
```dql
fetch security.events, from:now()-24h
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
// summarize on the vulnerability level
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
// filter for CRITICAL vulnerabilities with public internet exposure
| filter vulnerability.risk.level == "CRITICAL"
     AND public_internet_exposure == true
| sort {vulnerability.risk.score, direction:"descending"}, {affected_entities, direction:"descending"}
```

### Explanation

This query identifies **new critical vulnerabilities** (detected in the last 24 hours) that have **public internet exposure**, which represents the highest priority security risks.

#### Key Features:
1. **Time Range**: `from:now()-24h` - Looks at vulnerabilities detected in the last 24 hours
2. **Critical Severity**: Filters for vulnerabilities with risk score >= 9
3. **Public Internet Exposure**: Uses Davis assessment to identify vulnerabilities exposed to public networks
4. **Davis Security Intelligence**: Includes multiple AI-powered security context factors:
   - Vulnerable function usage status
   - Public network exposure
   - Public exploit availability
   - Data asset reachability

#### Output Fields:
- `vulnerability.display_id`: Unique vulnerability identifier
- `vulnerability.risk.score`: Davis AI-calculated risk score (0-10)
- `vulnerability.risk.level`: Risk level (CRITICAL, HIGH, MEDIUM, LOW, NONE)
- `vulnerability.title`: Human-readable vulnerability name
- `vulnerability.references.cve`: Associated CVE identifiers
- `last_detected`: When the vulnerability was last detected
- `affected_entities`: Count of affected entities
- `vulnerable_function_in_use`: Whether the vulnerable code is actively executed
- `public_internet_exposure`: Whether the vulnerability is exposed to the internet
- `public_exploit_available`: Whether a public exploit exists
- `data_assets_within_reach`: Whether the vulnerability can access sensitive data

### Use Case
This query helps security teams:
- **Prioritize remediation**: Focus on the most critical and exposed vulnerabilities first
- **Rapid response**: Identify newly discovered critical exposures within 24 hours
- **Risk assessment**: Understand the full security context with Davis AI assessments
- **Incident response**: Quickly identify vulnerabilities that pose immediate threats

---

## 3. Runtime Entity Analysis for CVE-2025-52434

### Overview
CVE-2025-52434 is a vulnerability that requires runtime verification to determine if it affects production systems. This section provides the approach and queries to analyze this vulnerability in the Dynatrace environment.

### Step 1: Check if CVE Exists in Dynatrace RVA

```dql
fetch security.events
| filter event.provider=="Dynatrace"
     AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
| filter in("CVE-2025-52434", vulnerability.references.cve)
| summarize{
    vulnerability.risk.score=round(takeMax(vulnerability.risk.score),decimals:1),
    vulnerability.title=takeFirst(vulnerability.title),
    last_detected=takeMax(timestamp),
    affected_entities=countDistinctExact(affected_entity.id),
    vulnerable_function_in_use=if(in("IN_USE",collectArray(vulnerability.davis_assessment.vulnerable_function_status)),true, else:false),
    public_internet_exposure=if(in("PUBLIC_NETWORK",collectArray(vulnerability.davis_assessment.exposure_status)),true,else:false),
    public_exploit_available=if(in("AVAILABLE",collectArray(vulnerability.davis_assessment.exploit_status)),true,else:false)
}, by: {vulnerability.display_id}
| fieldsAdd vulnerability.risk.level=if(vulnerability.risk.score>=9,"CRITICAL",
                                     else:if(vulnerability.risk.score>=7,"HIGH",
                                     else:if(vulnerability.risk.score>=4,"MEDIUM",
                                     else:if(vulnerability.risk.score>=0.1,"LOW",
                                     else:"NONE"))))
```

### Step 2: Get Detailed Information About Affected Entities

If the CVE is found, use this query to get detailed information about which entities are affected:

```dql
fetch security.events
| filter event.provider=="Dynatrace"
     AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
     AND event.level=="ENTITY"
| filter in("CVE-2025-52434", vulnerability.references.cve)
| dedup {vulnerability.display_id, affected_entity.id}, sort:{timestamp desc}
| filter vulnerability.resolution.status == "OPEN"
     AND vulnerability.parent.mute.status != "MUTED"
     AND vulnerability.mute.status != "MUTED"
| fields affected_entity.id, 
         affected_entity.name, 
         affected_entity.type,
         vulnerability.display_id,
         vulnerability.title,
         vulnerability.risk.score,
         vulnerability.davis_assessment.vulnerable_function_status,
         vulnerability.davis_assessment.exposure_status,
         vulnerability.davis_assessment.exploit_status,
         vulnerability.davis_assessment.data_assets_status,
         related_entities.hosts.names,
         related_entities.hosts.ids,
         affected_entity.affected_processes.ids
```

### Step 3: Get Process and Application Context

To understand which applications and processes are affected:

```dql
fetch dt.entity.process_group_instance
| filter in(id, array("PROCESS_GROUP_INSTANCE-ID-1", "PROCESS_GROUP_INSTANCE-ID-2"))
| fieldsAdd process.name=entity.name, 
           process.id=id, 
           host.id=belongs_to[dt.entity.host],
           releasesProduct,
           releasesStage,
           softwareComponents=contains[dt.entity.software_component]
```
**Note**: Replace the process IDs in the array with actual IDs from Step 2's `affected_entity.affected_processes.ids` field.

### Step 4: Get Software Components (Vulnerable Libraries)

To verify if the vulnerable library is loaded in runtime:

```dql
fetch dt.entity.software_component
| filter in(id, array("SOFTWARE_COMPONENT-ID-1", "SOFTWARE_COMPONENT-ID-2"))
| fieldsAdd component.name=entity.name,
           component.id=id,
           softwareTechnologies,
           softwareTypes
```
**Note**: Replace the component IDs with actual IDs from Step 3's `softwareComponents` field.

### Verification Process for CVE-2025-52434

Based on the agent instructions, the verification should follow these steps:

1. **Check if CVE exists in Dynatrace RVA**:
   - If NOT found: The vulnerability is not detected in the running environment
   - If FOUND: Proceed to next steps

2. **Analyze Davis Assessments**:
   - **Davis Risk Score**: Dynatrace's AI-calculated risk (0-10 scale)
   - **Vulnerable Function Status**: Is the vulnerable code actually executed?
     - `IN_USE`: High priority - vulnerable code is actively running
     - `NOT_IN_USE`: Lower priority - vulnerable code exists but isn't executed
   - **Exposure Status**: Is it reachable from the internet?
     - `PUBLIC_NETWORK`: Exposed to the internet - highest priority
     - `INTERNAL_NETWORK`: Only internal access
   - **Exploit Status**: Is there a public exploit available?
     - `AVAILABLE`: Public exploits exist - increases urgency
   - **Data Assets Status**: Can it access sensitive data?
     - `REACHABLE`: Can access data assets - increases impact

3. **Review Affected Entities**:
   - Identify which processes, hosts, and applications are affected
   - Check if production applications are impacted (look for `releasesStage` containing "prod" or "production")

4. **Make Verification Decision**:

   **CONFIRMED** if:
   - CVE is found in Dynatrace security events
   - Vulnerable function is `IN_USE`
   - Production applications are affected

   **NOT CONFIRMED** if:
   - CVE is not found in Dynatrace security events, OR
   - CVE is found but vulnerable function is `NOT_IN_USE`, OR
   - CVE is found but vulnerable library is not loaded in runtime, OR
   - No production applications are affected

### Expected Output Format

When reporting findings for CVE-2025-52434, include:

1. **Vulnerability Status**: Found/Not Found in Dynatrace RVA
2. **Davis Risk Assessment**:
   - Risk Score: [X.X]
   - Risk Level: [CRITICAL/HIGH/MEDIUM/LOW]
3. **Davis Security Context**:
   - Vulnerable Function in Use: [Yes/No]
   - Public Internet Exposure: [Yes/No]
   - Public Exploit Available: [Yes/No]
   - Data Assets Within Reach: [Yes/No]
4. **Affected Entities**:
   - Total Count: [N]
   - Entity List: [name(ID), name(ID), ...]
5. **Production Impact**: [Yes/No with explanation]
6. **Verification Result**: [CONFIRMED / NOT CONFIRMED]
7. **Recommended Action**: [Based on verification result]

---

## Additional Resources

- [Dynatrace Security Events Documentation](https://docs.dynatrace.com/docs/shortlink/security-events-examples)
- [Dynatrace Query Language (DQL) Reference](https://docs.dynatrace.com/docs/platform/grail/dynatrace-query-language)
- [Davis Security Intelligence](https://docs.dynatrace.com/docs/platform-modules/application-security/vulnerability-analytics)

---

## Notes

- All queries use the `security.events` table which is part of Dynatrace's security event management
- Davis AI assessments provide intelligent context beyond basic CVE severity scores
- Runtime verification with Dynatrace confirms whether vulnerabilities are actually exploitable in production
- The `vulnerable_function_in_use` assessment is particularly important as it indicates whether the vulnerable code path is actively executed
