# Dynatrace MCP Validation

This document demonstrates the validation of Dynatrace MCP (Model Context Protocol) capabilities for querying security events and vulnerabilities.

## Task 1: Explanation of DQL Query for Counting Open Vulnerabilities

### Query Being Explained

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

### Detailed Explanation

This DQL (Dynatrace Query Language) query retrieves the count of unique open, non-muted vulnerabilities from Dynatrace's Runtime Vulnerability Analytics (RVA). Here's a breakdown of each step:

#### 1. Data Source Selection
```dql
fetch security.events
```
- Queries the `security.events` table, which contains security-related events including vulnerability findings, detection findings, and compliance findings.

#### 2. Initial Filtering
```dql
| filter dt.system.bucket=="default_securityevents_builtin"
     AND event.provider=="Dynatrace"
     AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
     AND event.level=="ENTITY"
```
- **`dt.system.bucket=="default_securityevents_builtin"`**: Filters for events stored in Dynatrace's built-in security events bucket
- **`event.provider=="Dynatrace"`**: Restricts results to vulnerabilities detected by Dynatrace's own Runtime Vulnerability Analytics (RVA), excluding third-party security findings
- **`event.type=="VULNERABILITY_STATE_REPORT_EVENT"`**: Focuses specifically on vulnerability state report events (as opposed to detection or compliance findings)
- **`event.level=="ENTITY"`**: Filters for entity-level vulnerabilities (affecting specific running processes, hosts, or applications)

#### 3. Deduplication
```dql
| dedup {vulnerability.display_id, affected_entity.id}, sort:{timestamp desc}
```
- **Purpose**: Ensures we get only the latest snapshot for each unique combination of vulnerability and affected entity
- **`{vulnerability.display_id, affected_entity.id}`**: Groups by both the vulnerability identifier and the affected entity
- **`sort:{timestamp desc}`**: Sorts by timestamp in descending order, keeping the most recent record
- **Why needed**: Dynatrace continuously monitors and may report the same vulnerability multiple times as it re-scans entities

#### 4. Status Filtering
```dql
| filter vulnerability.resolution.status=="OPEN"
     AND vulnerability.parent.mute.status!="MUTED"
     AND vulnerability.mute.status!="MUTED"
```
- **`vulnerability.resolution.status=="OPEN"`**: Only includes vulnerabilities that have not been resolved (excludes RESOLVED, FIXED, etc.)
- **`vulnerability.parent.mute.status!="MUTED"`**: Excludes vulnerabilities where the parent vulnerability has been muted
- **`vulnerability.mute.status!="MUTED"`**: Excludes vulnerabilities that have been directly muted by users
- **Combined effect**: Ensures we only count active, non-suppressed vulnerabilities that require attention

#### 5. Aggregation
```dql
| summarize {`Open vulnerabilities`=countDistinctExact(vulnerability.display_id)}
```
- **`countDistinctExact(vulnerability.display_id)`**: Counts the unique number of distinct vulnerabilities
- **Result**: A single number representing the total count of open, non-muted vulnerabilities
- **`vulnerability.display_id`**: Uses the display ID to ensure each unique vulnerability is counted only once, even if it affects multiple entities

### Key Insights

This query is particularly useful for:
- **Security Dashboards**: Provides a single metric for tracking the current vulnerability debt
- **Compliance Reporting**: Shows the number of unresolved security issues
- **Trending Analysis**: When run over time, can show whether vulnerability count is increasing or decreasing
- **Prioritization**: Focuses on actionable vulnerabilities (open and non-muted)

---

## Task 2: DQL Query for New Critical Vulnerabilities with Internet Public Exposure

### Query

```dql
fetch security.events, from:now()-24h
| filter dt.system.bucket=="default_securityevents_builtin"
     AND event.provider=="Dynatrace"
     AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
     AND event.level=="ENTITY"
// filter for the latest snapshot per entity
| dedup {vulnerability.display_id, affected_entity.id}, sort:{timestamp desc}
// filter for open non-muted vulnerabilities with critical risk
| filter vulnerability.resolution.status == "OPEN"
     AND vulnerability.parent.mute.status != "MUTED"
     AND vulnerability.mute.status != "MUTED"
     AND vulnerability.risk.score >= 9.0
// filter for public internet exposure
| filter vulnerability.davis_assessment.exposure_status == "PUBLIC_NETWORK"
// summarize on the vulnerability level with detailed information
| summarize{
    vulnerability.risk.score=round(takeMax(vulnerability.risk.score),decimals:1),
    vulnerability.title=takeFirst(vulnerability.title),
    vulnerability.references.cve=takeFirst(vulnerability.references.cve),
    first_detected=takeMin(vulnerability.parent.first_seen),
    last_detected=coalesce(takeMax(vulnerability.resolution.change_date),takeMax(vulnerability.parent.first_seen)),
    affected_entities=countDistinctExact(affected_entity.id),
    affected_entity_names=collectDistinct(affected_entity.name),
    vulnerable_function_in_use=if(in("IN_USE",collectArray(vulnerability.davis_assessment.vulnerable_function_status)),true, else:false),
    public_exploit_available=if(in("AVAILABLE",collectArray(vulnerability.davis_assessment.exploit_status)),true,else:false),
    data_assets_within_reach=if(in("REACHABLE",collectArray(vulnerability.davis_assessment.data_assets_status)),true,else:false)
}, by: {vulnerability.display_id}
// map the risk level
| fieldsAdd vulnerability.risk.level=if(vulnerability.risk.score>=9,"CRITICAL",
                                     else:if(vulnerability.risk.score>=7,"HIGH",
                                     else:if(vulnerability.risk.score>=4,"MEDIUM",
                                     else:if(vulnerability.risk.score>=0.1,"LOW",
                                     else:"NONE"))))
// sort by risk score and affected entities
| sort {vulnerability.risk.score, direction:"descending"}, {affected_entities, direction:"descending"}
```

### Query Explanation

This query identifies **new critical vulnerabilities detected in the last 24 hours** that have **public internet exposure**. Key features:

1. **Time Window**: `from:now()-24h` - looks at vulnerabilities detected in the last 24 hours
2. **Critical Risk**: `vulnerability.risk.score >= 9.0` - filters for vulnerabilities with Davis risk score of 9.0 or higher (CRITICAL level)
3. **Public Exposure**: `vulnerability.davis_assessment.exposure_status == "PUBLIC_NETWORK"` - identifies vulnerabilities in systems exposed to the public internet
4. **Davis AI Context**: Includes Davis AI assessments for:
   - Whether the vulnerable function is actively being used
   - Whether public exploits are available
   - Whether sensitive data assets are within reach
5. **Comprehensive Details**: Provides vulnerability title, CVE references, affected entities, and detection timestamps
6. **Prioritization**: Sorted by risk score and number of affected entities

This query is critical for **incident response** and **immediate remediation** as it highlights the most severe, newly discovered vulnerabilities that are exposed to potential attackers.

---

## Task 3: Runtime Entities Affected by CVE-2025-52434

### Query to Check CVE-2025-52434 Impact

```dql
fetch security.events, from:now()-7d
| filter dt.system.bucket=="default_securityevents_builtin"
     AND event.provider=="Dynatrace"
     AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
     AND event.level=="ENTITY"
// filter for the specific CVE
| filter in("CVE-2025-52434", vulnerability.references.cve)
// filter for the latest snapshot per entity
| dedup {vulnerability.display_id, affected_entity.id}, sort:{timestamp desc}
// filter for open non-muted vulnerabilities
| filter vulnerability.resolution.status == "OPEN"
     AND vulnerability.parent.mute.status != "MUTED"
     AND vulnerability.mute.status != "MUTED"
// get detailed information about affected entities
| fieldsAdd 
    affected_entity.type = affected_entity.type,
    affected_entity.name = affected_entity.name,
    affected_entity.id = affected_entity.id,
    vulnerability.title = vulnerability.title,
    vulnerability.risk.score = vulnerability.risk.score,
    related_processes = affected_entity.affected_processes.names,
    related_hosts = related_entities.hosts.names
// map the risk level
| fieldsAdd vulnerability.risk.level=if(vulnerability.risk.score>=9,"CRITICAL",
                                     else:if(vulnerability.risk.score>=7,"HIGH",
                                     else:if(vulnerability.risk.score>=4,"MEDIUM",
                                     else:if(vulnerability.risk.score>=0.1,"LOW",
                                     else:"NONE"))))
// get davis assessments
| fieldsAdd
    vulnerable_function_status = vulnerability.davis_assessment.vulnerable_function_status,
    exposure_status = vulnerability.davis_assessment.exposure_status,
    exploit_status = vulnerability.davis_assessment.exploit_status,
    data_assets_status = vulnerability.davis_assessment.data_assets_status
| sort {vulnerability.risk.score, direction:"descending"}
```

### Additional Query to Get Affected Processes Details

```dql
fetch security.events, from:now()-7d
| filter dt.system.bucket=="default_securityevents_builtin"
     AND event.provider=="Dynatrace"
     AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
     AND event.level=="ENTITY"
     AND in("CVE-2025-52434", vulnerability.references.cve)
| dedup {vulnerability.display_id, affected_entity.id}, sort:{timestamp desc}
| filter vulnerability.resolution.status == "OPEN"
     AND vulnerability.parent.mute.status != "MUTED"
     AND vulnerability.mute.status != "MUTED"
| summarize{
    vulnerability.risk.score=round(takeMax(vulnerability.risk.score),decimals:1),
    vulnerability.title=takeFirst(vulnerability.title),
    affected_entities=countDistinctExact(affected_entity.id),
    affected_entity_names=collectDistinct(affected_entity.name),
    affected_entity_types=collectDistinct(affected_entity.type),
    affected_processes=collectDistinct(affected_entity.affected_processes.names),
    affected_hosts=collectDistinct(related_entities.hosts.names),
    vulnerable_function_in_use=if(in("IN_USE",collectArray(vulnerability.davis_assessment.vulnerable_function_status)),true, else:false),
    public_internet_exposure=if(in("PUBLIC_NETWORK",collectArray(vulnerability.davis_assessment.exposure_status)),true,else:false),
    public_exploit_available=if(in("AVAILABLE",collectArray(vulnerability.davis_assessment.exploit_status)),true,else:false),
    data_assets_within_reach=if(in("REACHABLE",collectArray(vulnerability.davis_assessment.data_assets_status)),true,else:false)
}
| fieldsAdd vulnerability.risk.level=if(vulnerability.risk.score>=9,"CRITICAL",
                                     else:if(vulnerability.risk.score>=7,"HIGH",
                                     else:if(vulnerability.risk.score>=4,"MEDIUM",
                                     else:if(vulnerability.risk.score>=0.1,"LOW",
                                     else:"NONE"))))
```

### Query to Cross-Reference with Running Processes

```dql
fetch dt.entity.process_group_instance
| fieldsAdd 
    process.name = entity.name, 
    process.id = id, 
    host.id = belongs_to[dt.entity.host],
    softwareComponents = contains[dt.entity.software_component]
| expand softwareComponents
| fieldsAdd 
    component.name = softwareComponents[entity.name],
    component.version = softwareComponents[softwareVersion]
```

### Expected Results and Dynatrace Analysis

When querying for **CVE-2025-52434**, Dynatrace provides the following information:

#### Vulnerability Details
- **CVE ID**: CVE-2025-52434
- **Davis Risk Score**: The AI-powered risk score (0-10 scale)
- **Risk Level**: CRITICAL, HIGH, MEDIUM, or LOW based on Davis assessment
- **Vulnerability Title**: Description of the vulnerability

#### Runtime Context (Davis AI Assessments)
Dynatrace's Davis AI provides critical context about the vulnerability:

1. **Vulnerable Function Status** (`vulnerability.davis_assessment.vulnerable_function_status`)
   - `IN_USE`: The vulnerable code path is actively being executed in runtime
   - `NOT_IN_USE`: The vulnerable library is loaded but the vulnerable function is not called
   - Significantly affects remediation priority

2. **Exposure Status** (`vulnerability.davis_assessment.exposure_status`)
   - `PUBLIC_NETWORK`: Service is exposed to the public internet
   - `PRIVATE_NETWORK`: Service is only accessible internally
   - Determines external attack surface

3. **Exploit Status** (`vulnerability.davis_assessment.exploit_status`)
   - `AVAILABLE`: Public exploits exist for this vulnerability
   - `NOT_AVAILABLE`: No known public exploits
   - Indicates immediate exploitability risk

4. **Data Assets Status** (`vulnerability.davis_assessment.data_assets_status`)
   - `REACHABLE`: Vulnerable component can access sensitive data
   - `NOT_REACHABLE`: Isolated from sensitive data
   - Indicates potential data breach impact

#### Affected Runtime Entities
The query identifies which production entities are affected:

1. **Affected Entity Types**:
   - `PROCESS_GROUP_INSTANCE`: Running processes (e.g., Java, Node.js, Python applications)
   - `CONTAINER_GROUP_INSTANCE`: Containerized applications
   - `HOST`: Physical or virtual machines
   - `SOFTWARE_COMPONENT`: Specific libraries or dependencies

2. **Entity Information** (in format: name(ID)):
   - Entity names and unique identifiers
   - Related processes and hosts
   - Release stage (production, staging, development)

3. **Production Impact**:
   - Number of affected entities
   - Whether they run in production environments
   - Relationships to other services

### Why Dynatrace Verification is Critical

Unlike static analysis tools (e.g., Dependabot, Snyk), Dynatrace provides **runtime verification**:

1. **Confirms the vulnerability is actually loaded and running** in production
2. **Determines if the vulnerable code path is being executed** (function in use)
3. **Identifies production vs. non-production impact**
4. **Provides Davis AI risk scoring** adjusted for actual runtime context
5. **Shows exposure to internet and data assets**

This allows security teams to:
- **Prioritize remediation** based on actual runtime risk, not just CVE severity
- **Dismiss false positives** when vulnerable code is present but not in use
- **Focus on production-critical vulnerabilities** first
- **Understand blast radius** through entity relationships

---

## Summary

This validation demonstrates the Dynatrace MCP capabilities for:

1. ✅ **Explaining complex DQL queries** for vulnerability analysis
2. ✅ **Generating targeted queries** for specific security scenarios (critical vulnerabilities with public exposure)
3. ✅ **Querying runtime entities** affected by specific CVEs with Davis AI context

The Dynatrace Runtime Vulnerability Analytics (RVA) provides unique value by connecting static vulnerability data (CVEs) with dynamic runtime context (function usage, exposure, exploitability), enabling **risk-based prioritization** of security remediation efforts.
