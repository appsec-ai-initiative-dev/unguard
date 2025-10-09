# Dynatrace DQL Query Examples for Unguard

This document provides practical examples of using the DQL queries from the MCP validation with the Unguard application.

## Query 1: Open Vulnerabilities Count (Original)

```dql
fetch security.events
| filter dt.system.bucket=="default_securityevents_builtin"
     AND event.provider=="Dynatrace"
     AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
     AND event.level=="ENTITY"
| dedup {vulnerability.display_id, affected_entity.id}, sort:{timestamp desc}
| filter vulnerability.resolution.status=="OPEN"
     AND vulnerability.parent.mute.status!="MUTED"
     AND vulnerability.mute.status!="MUTED"
| summarize {`Open vulnerabilities`=countDistinctExact(vulnerability.display_id)}
```

**Use Case**: Get a quick count of open vulnerabilities across all Unguard services.

## Query 2: Critical Vulnerabilities with Internet Exposure

```dql
fetch security.events
| filter dt.system.bucket=="default_securityevents_builtin"
     AND event.provider=="Dynatrace"
     AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
     AND event.level=="ENTITY"
| dedup {vulnerability.display_id, affected_entity.id}, sort:{timestamp desc}
| filter vulnerability.resolution.status == "OPEN"
     AND vulnerability.parent.mute.status != "MUTED"
     AND vulnerability.mute.status != "MUTED"
     AND vulnerability.risk.score >= 9.0
     AND vulnerability.davis_assessment.exposure_status == "PUBLIC_NETWORK"
| summarize {
    vulnerability.risk.score=round(takeMax(vulnerability.risk.score), decimals:1),
    vulnerability.title=takeFirst(vulnerability.title),
    vulnerability.references.cve=takeFirst(vulnerability.references.cve),
    last_detected=coalesce(takeMax(vulnerability.resolution.change_date), takeMax(vulnerability.parent.first_seen)),
    affected_entities=countDistinctExact(affected_entity.id),
    vulnerable_function_in_use=if(in("IN_USE", collectArray(vulnerability.davis_assessment.vulnerable_function_status)), true, else:false),
    public_exploit_available=if(in("AVAILABLE", collectArray(vulnerability.davis_assessment.exploit_status)), true, else:false),
    data_assets_within_reach=if(in("REACHABLE", collectArray(vulnerability.davis_assessment.data_assets_status)), true, else:false),
    affected_entity_names=collectArray(affected_entity.name)
}, by: {vulnerability.display_id}
| fieldsAdd vulnerability.risk.level="CRITICAL"
| sort {vulnerability.risk.score, direction:"descending"}, {affected_entities, direction:"descending"}
```

**Use Case**: Identify the most critical vulnerabilities that pose immediate risk due to internet exposure.

## Query 3: Unguard-Specific Vulnerability Analysis

```dql
fetch security.events
| filter dt.system.bucket=="default_securityevents_builtin"
     AND event.provider=="Dynatrace"
     AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
     AND event.level=="ENTITY"
| dedup {vulnerability.display_id, affected_entity.id}, sort:{timestamp desc}
| filter vulnerability.resolution.status == "OPEN"
     AND vulnerability.parent.mute.status != "MUTED"
     AND vulnerability.mute.status != "MUTED"
     AND (contains(affected_entity.name, "unguard") 
          OR contains(affected_entity.name, "microblog")
          OR contains(affected_entity.name, "user-auth")
          OR contains(affected_entity.name, "profile")
          OR contains(affected_entity.name, "membership")
          OR contains(affected_entity.name, "like-service")
          OR contains(affected_entity.name, "proxy")
          OR contains(affected_entity.name, "ad-service")
          OR contains(affected_entity.name, "payment")
          OR contains(affected_entity.name, "status"))
| summarize {
    vulnerability.risk.score=round(takeMax(vulnerability.risk.score), decimals:1),
    vulnerability.title=takeFirst(vulnerability.title),
    vulnerability.references.cve=takeFirst(vulnerability.references.cve),
    service_name=takeFirst(affected_entity.name),
    vulnerable_function_in_use=if(in("IN_USE", collectArray(vulnerability.davis_assessment.vulnerable_function_status)), true, else:false),
    public_internet_exposure=if(in("PUBLIC_NETWORK", collectArray(vulnerability.davis_assessment.exposure_status)), true, else:false),
    public_exploit_available=if(in("AVAILABLE", collectArray(vulnerability.davis_assessment.exploit_status)), true, else:false),
    data_assets_within_reach=if(in("REACHABLE", collectArray(vulnerability.davis_assessment.data_assets_status)), true, else:false)
}, by: {vulnerability.display_id, affected_entity.name}
| fieldsAdd vulnerability.risk.level=if(vulnerability.risk.score>=9,"CRITICAL",
                                     else:if(vulnerability.risk.score>=7,"HIGH",
                                     else:if(vulnerability.risk.score>=4,"MEDIUM",
                                     else:if(vulnerability.risk.score>=0.1,"LOW",
                                     else:"NONE"))))
| sort {vulnerability.risk.score, direction:"descending"}, service_name
```

**Use Case**: Focus specifically on vulnerabilities affecting Unguard microservices.

## Query 4: Runtime Entity Discovery for Unguard

```dql
fetch dt.entity.container_group_instance
| filter contains(toLowerString(entity.name), "unguard")
     OR contains(toLowerString(containerImageName), "unguard")
     OR contains(toLowerString(containerImageName), "microblog")
     OR contains(toLowerString(containerImageName), "user-auth")
     OR contains(toLowerString(containerImageName), "profile")
     OR contains(toLowerString(containerImageName), "membership")
     OR contains(toLowerString(containerImageName), "like-service")
     OR contains(toLowerString(containerImageName), "proxy")
     OR contains(toLowerString(containerImageName), "ad-service")
     OR contains(toLowerString(containerImageName), "payment")
     OR contains(toLowerString(containerImageName), "status")
| fieldsAdd {
    entity_name = entity.name,
    entity_id = entity.id,
    container_image = containerImageName,
    kubernetes_namespace = kubernetesNamespace
}
| sort entity_name
```

**Use Case**: Discover all running Unguard container instances for vulnerability correlation.

## Query 5: Dependabot Vulnerability Verification Template

```dql
fetch security.events
| filter dt.system.bucket=="default_securityevents_builtin"
     AND event.provider=="Dynatrace"
     AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
     AND event.level=="ENTITY"
| dedup {vulnerability.display_id, affected_entity.id}, sort:{timestamp desc}
| filter in("<CVE-ID>", vulnerability.references.cve)
| filter vulnerability.parent.mute.status != "MUTED"
     AND vulnerability.mute.status != "MUTED"
| fieldsAdd {
    entity_name = affected_entity.name,
    entity_id = affected_entity.id,
    vulnerability_title = vulnerability.title,
    risk_score = vulnerability.risk.score,
    risk_level = if(vulnerability.risk.score>=9,"CRITICAL",
                 else:if(vulnerability.risk.score>=7,"HIGH",
                 else:if(vulnerability.risk.score>=4,"MEDIUM",
                 else:if(vulnerability.risk.score>=0.1,"LOW",
                 else:"NONE")))),
    resolution_status = vulnerability.resolution.status,
    vulnerable_function_status = vulnerability.davis_assessment.vulnerable_function_status,
    exposure_status = vulnerability.davis_assessment.exposure_status,
    exploit_status = vulnerability.davis_assessment.exploit_status,
    data_assets_status = vulnerability.davis_assessment.data_assets_status
}
```

**Use Case**: Replace `<CVE-ID>` with specific CVE to verify Dependabot findings.

## Expected Unguard Services in Results

When running these queries against a deployed Unguard environment, you should expect to see entities related to:

1. **Frontend Services**:
   - `unguard-frontend` (Next.js)
   - `unguard-envoy-proxy`

2. **Backend Services**:
   - `unguard-microblog-service` (Java Spring)
   - `unguard-user-auth-service` (Node.js)
   - `unguard-profile-service` (Java Spring)
   - `unguard-membership-service` (.NET)
   - `unguard-like-service` (PHP)
   - `unguard-proxy-service` (Java Spring)
   - `unguard-ad-service` (.NET)
   - `unguard-payment-service` (Python Flask)
   - `unguard-status-service` (Go)

3. **Support Services**:
   - `unguard-user-simulator` (Node.js Puppeteer)
   - `unguard-malicious-load-generator`

## Common Vulnerability Types Expected

Based on the Unguard architecture, these queries may identify vulnerabilities in:

- **Java Dependencies**: Jackson, Spring Framework, H2 Database
- **Node.js Dependencies**: Express, JWT libraries, npm packages
- **Python Dependencies**: Flask, pip packages
- **.NET Dependencies**: NuGet packages, Entity Framework
- **PHP Dependencies**: Composer packages
- **Container Base Images**: Alpine, Ubuntu, etc.

## Usage Tips

1. **Time Range**: Add time filters for recent vulnerabilities:
   ```dql
   | filter timestamp >= now() - 24h
   ```

2. **Severity Focus**: Adjust risk score thresholds:
   ```dql
   | filter vulnerability.risk.score >= 7.0  // HIGH and CRITICAL only
   ```

3. **Environment Filtering**: Add environment-specific filters:
   ```dql
   | filter contains(affected_entity.name, "prod") OR contains(affected_entity.name, "staging")
   ```

## Validation Results Format

Each query should return structured data suitable for:
- Security dashboards
- Automated alerting
- Compliance reporting
- Vulnerability prioritization

This enables the MCP to provide actionable security intelligence for the Unguard application.