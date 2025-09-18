# Dynatrace MCP Verification

This directory contains tools and documentation for verifying Dynatrace MCP (Model Context Protocol) connection and demonstrating DQL query capabilities for vulnerability analysis.

## 📋 Issue Requirements Addressed

This implementation addresses the three main requirements from issue #8:

1. **✅ Explain Dynatrace Query**: Comprehensive explanation of the provided DQL query for open vulnerabilities
2. **✅ Generate DQL Query**: New DQL query for critical vulnerabilities with internet public exposure  
3. **✅ CVE-2025-52434 Check**: Query to check runtime entities affected by specific CVE (demonstrated with hypothetical CVE)

## 🔧 Files

- **`dynatrace-mcp-verification.md`** - Comprehensive documentation explaining all DQL queries and MCP verification process
- **`verify-dynatrace-mcp.py`** - Python script demonstrating query execution and result analysis

## 🚀 Usage

### Quick Start

Run the verification script:

```bash
cd /home/runner/work/unguard/unguard
python3 scripts/verify-dynatrace-mcp.py
```

### Manual Query Execution

For live environments with MCP access, use these DQL queries:

#### 1. Count Open Vulnerabilities
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

#### 2. Critical Internet-Exposed Vulnerabilities
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

#### 3. Specific CVE Check (replace CVE-ID)
```dql
fetch security.events
| filter dt.system.bucket=="default_securityevents_builtin"
     AND event.provider=="Dynatrace"
     AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
     AND event.level=="ENTITY"
| filter vulnerability.display_id == "CVE-YYYY-NNNNN"
     OR matchesValue(vulnerability.references.cve, "CVE-YYYY-NNNNN")
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

## 📊 MCP Connection Verification

The script verifies MCP connectivity by:

1. **Connection Test**: Basic query to validate MCP server access
2. **Data Access**: Confirming ability to query security.events table
3. **Query Parsing**: Validating DQL syntax interpretation
4. **Result Processing**: Ensuring proper data retrieval and formatting

## 🎯 Key Features

- **Entity Reporting**: Follows MCP guidelines with `name(ID)` format
- **Davis Assessment**: Includes Davis risk scoring and assessments
- **Function Usage Analysis**: Identifies vulnerabilities in active code paths
- **Exposure Assessment**: Prioritizes internet-facing vulnerabilities
- **Comprehensive Analysis**: Provides detailed vulnerability impact assessment

## 📖 Related Documentation

- [Dynatrace Monaco Configuration](MONACO.md)
- [GitHub Copilot Instructions](../.github/copilot-instructions.md)
- [Dynatrace Security Events Examples](https://docs.dynatrace.com/docs/shortlink/security-events-examples)

## 🔍 Notes

- CVE-2025-52434 is used as a hypothetical example (future CVE number)
- Queries are designed for environments with Dynatrace Runtime Application Protection enabled
- Results depend on actual vulnerability data present in the monitored environment
- MCP connection requires proper authentication and permissions