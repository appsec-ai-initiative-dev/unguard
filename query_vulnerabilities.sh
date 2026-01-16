#!/bin/bash

# Dynatrace environment setup
DT_ENV_URL="${DT_TENANT_URL}"
DT_API_TOKEN="${DT_API_TOKEN}"

echo "=== Querying Dynatrace for Security Vulnerabilities ==="
echo "Environment: $DT_ENV_URL"
echo ""

# Query 1: Get current vulnerability state (deduplicated, open vulnerabilities)
echo "### Query 1: Current Open Vulnerabilities (Last 7 days) ###"
DQL_QUERY_1='fetch security.events, from:now() - 7d
| filter event.type == "VULNERABILITY_STATE_REPORT_EVENT"
| dedup {vulnerability.display_id, affected_entity.id}, sort: {timestamp desc}
| filter vulnerability.resolution_status == "OPEN"
| fields 
    timestamp,
    vulnerability.display_id,
    vulnerability.external_vulnerability_id,
    vulnerability.title,
    vulnerability.severity,
    davis.security_score,
    davis.risk_level,
    davis.assessment.davis_vulnerable_function_in_use,
    davis.assessment.davis_vulnerable_function_in_use_insight,
    davis.assessment.davis_public_exploit,
    davis.assessment.davis_public_exploit_insight,
    affected_entity.id,
    affected_entity.name,
    technology,
    vulnerable_component.file_name,
    vulnerable_component.package_name,
    vulnerable_component.version
| sort davis.security_score desc'

curl -X POST "${DT_ENV_URL}/api/v2/query/execute" \
  -H "Authorization: Api-Token ${DT_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"query\": $(echo "$DQL_QUERY_1" | jq -Rs .)}" \
  | jq '.' > vuln_current_state.json

echo "Results saved to vuln_current_state.json"
cat vuln_current_state.json | jq '.records[] | {
  vulnerability_id: .vulnerability.display_id,
  cve: .vulnerability.external_vulnerability_id,
  title: .vulnerability.title,
  severity: .vulnerability.severity,
  davis_score: .davis.security_score,
  davis_risk: .davis.risk_level,
  function_in_use: .davis.assessment.davis_vulnerable_function_in_use,
  package: .vulnerable_component.package_name,
  version: .vulnerable_component.version,
  affected_entity: .affected_entity.name,
  entity_id: .affected_entity.id,
  technology: .technology
}'

echo ""
echo ""

# Query 2: Filter for npm/JavaScript specific vulnerabilities
echo "### Query 2: NPM/JavaScript Vulnerabilities Only ###"
DQL_QUERY_2='fetch security.events, from:now() - 7d
| filter event.type == "VULNERABILITY_STATE_REPORT_EVENT"
| dedup {vulnerability.display_id, affected_entity.id}, sort: {timestamp desc}
| filter vulnerability.resolution_status == "OPEN"
| filter technology == "NODE_JS" or technology == "JAVASCRIPT" or contains(vulnerable_component.package_name, "npm") or contains(vulnerable_component.file_name, "package.json")
| fields 
    vulnerability.display_id,
    vulnerability.external_vulnerability_id,
    vulnerability.title,
    vulnerability.severity,
    davis.security_score,
    davis.risk_level,
    davis.assessment.davis_vulnerable_function_in_use,
    davis.assessment.davis_vulnerable_function_in_use_insight,
    davis.assessment.davis_public_exploit,
    davis.assessment.davis_public_exploit_insight,
    davis.assessment.davis_data_assets,
    davis.assessment.davis_data_assets_insight,
    affected_entity.id,
    affected_entity.name,
    vulnerable_component.package_name,
    vulnerable_component.version,
    vulnerable_component.file_name
| sort davis.security_score desc'

curl -X POST "${DT_ENV_URL}/api/v2/query/execute" \
  -H "Authorization: Api-Token ${DT_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"query\": $(echo "$DQL_QUERY_2" | jq -Rs .)}" \
  | jq '.' > vuln_npm_only.json

echo "Results saved to vuln_npm_only.json"
cat vuln_npm_only.json | jq -r '.records[] | "
═══════════════════════════════════════════════════════════
CVE ID: \(.vulnerability.external_vulnerability_id // "N/A")
Vulnerability ID: \(.vulnerability.display_id)
Title: \(.vulnerability.title)
─────────────────────────────────────────────────────────
SEVERITY: \(.vulnerability.severity)
Davis Risk Level: \(.davis.risk_level // "N/A")
Davis Security Score: \(.davis.security_score // "N/A")
─────────────────────────────────────────────────────────
PACKAGE: \(.vulnerable_component.package_name)
VERSION: \(.vulnerable_component.version)
FILE: \(.vulnerable_component.file_name // "N/A")
─────────────────────────────────────────────────────────
DAVIS ASSESSMENTS:
  • Vulnerable Function In Use: \(.davis.assessment.davis_vulnerable_function_in_use // "N/A")
    Insight: \(.davis.assessment.davis_vulnerable_function_in_use_insight // "N/A")
  
  • Public Exploit Available: \(.davis.assessment.davis_public_exploit // "N/A")
    Insight: \(.davis.assessment.davis_public_exploit_insight // "N/A")
  
  • Data Assets at Risk: \(.davis.assessment.davis_data_assets // "N/A")
    Insight: \(.davis.assessment.davis_data_assets_insight // "N/A")
─────────────────────────────────────────────────────────
AFFECTED ENTITY: \(.affected_entity.name)
ENTITY ID: \(.affected_entity.id)
═══════════════════════════════════════════════════════════
"'

echo ""
echo ""

# Query 3: Summary count by severity
echo "### Query 3: Vulnerability Summary by Severity ###"
DQL_QUERY_3='fetch security.events, from:now() - 7d
| filter event.type == "VULNERABILITY_STATE_REPORT_EVENT"
| dedup {vulnerability.display_id, affected_entity.id}, sort: {timestamp desc}
| filter vulnerability.resolution_status == "OPEN"
| summarize vuln_count = count(), by: {vulnerability.severity, davis.risk_level}
| sort vuln_count desc'

curl -X POST "${DT_ENV_URL}/api/v2/query/execute" \
  -H "Authorization: Api-Token ${DT_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"query\": $(echo "$DQL_QUERY_3" | jq -Rs .)}" \
  | jq '.'

echo ""
echo "=== Query Complete ==="
