#!/bin/bash

# Dynatrace environment setup - using the correct domain
DT_ENV_URL="https://pia1134d.dev.dynatracelabs.com"
DT_API_TOKEN="${COPILOT2_MCP_DT_API_TOKEN}"

echo "=== Querying Dynatrace for Security Vulnerabilities ==="
echo "Environment: $DT_ENV_URL"
echo ""

# Query 1: Get current vulnerability state (deduplicated, open vulnerabilities)
echo "### Query 1: Current Open Vulnerabilities (Last 30 days) ###"
DQL_QUERY_1='fetch security.events, from:now() - 30d
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
  2>/dev/null | jq '.' > vuln_current_state.json

if [ -s vuln_current_state.json ]; then
  ERROR_CHECK=$(cat vuln_current_state.json | jq -r '.error // empty')
  if [ -z "$ERROR_CHECK" ]; then
    echo "✅ Query 1 completed successfully"
    RECORD_COUNT=$(cat vuln_current_state.json | jq '.records | length')
    echo "Found $RECORD_COUNT vulnerabilities"
    
    # Show summary
    cat vuln_current_state.json | jq -r '.records[] | "\(.vulnerability.external_vulnerability_id // "N/A") | \(.vulnerable_component.package_name) | \(.vulnerability.severity) | Davis: \(.davis.risk_level // "N/A")"'
  else
    echo "❌ Query returned error:"
    cat vuln_current_state.json | jq '.error'
  fi
else
  echo "❌ Query 1 failed"
fi

echo ""
echo ""

# Query 2: Full vulnerability details
echo "### Query 2: All Open Vulnerabilities with Full Details ###"
DQL_QUERY_2='fetch security.events, from:now() - 30d
| filter event.type == "VULNERABILITY_STATE_REPORT_EVENT"
| dedup {vulnerability.display_id, affected_entity.id}, sort: {timestamp desc}
| filter vulnerability.resolution_status == "OPEN"
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
    technology,
    vulnerable_component.package_name,
    vulnerable_component.version,
    vulnerable_component.file_name
| sort davis.security_score desc'

curl -X POST "${DT_ENV_URL}/api/v2/query/execute" \
  -H "Authorization: Api-Token ${DT_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"query\": $(echo "$DQL_QUERY_2" | jq -Rs .)}" \
  2>/dev/null | jq '.' > vuln_all.json

if [ -s vuln_all.json ]; then
  ERROR_CHECK=$(cat vuln_all.json | jq -r '.error // empty')
  if [ -z "$ERROR_CHECK" ]; then
    echo "✅ Query 2 completed successfully"
    
    # Check if we have records
    RECORD_COUNT=$(cat vuln_all.json | jq '.records | length')
    if [ "$RECORD_COUNT" -gt 0 ]; then
      echo "Processing $RECORD_COUNT vulnerabilities..."
      echo ""
      
      cat vuln_all.json | jq -r '.records[] | "
═══════════════════════════════════════════════════════════
CVE ID: \(.vulnerability.external_vulnerability_id // "N/A")
Vulnerability ID: \(.vulnerability.display_id)
Title: \(.vulnerability.title)
─────────────────────────────────────────────────────────
SEVERITY: \(.vulnerability.severity)
Davis Risk Level: \(.davis.risk_level // "N/A")
Davis Security Score: \(.davis.security_score // "N/A")
─────────────────────────────────────────────────────────
TECHNOLOGY: \(.technology // "N/A")
PACKAGE: \(.vulnerable_component.package_name)
VERSION: \(.vulnerable_component.version)
FILE: \(.vulnerable_component.file_name // "N/A")
─────────────────────────────────────────────────────────
DAVIS ASSESSMENTS:
  • Vulnerable Function In Use: \(.davis.assessment.davis_vulnerable_function_in_use // "N/A")
    📋 \(.davis.assessment.davis_vulnerable_function_in_use_insight // "N/A")
  
  • Public Exploit Available: \(.davis.assessment.davis_public_exploit // "N/A")
    📋 \(.davis.assessment.davis_public_exploit_insight // "N/A")
  
  • Data Assets at Risk: \(.davis.assessment.davis_data_assets // "N/A")
    📋 \(.davis.assessment.davis_data_assets_insight // "N/A")
─────────────────────────────────────────────────────────
AFFECTED ENTITY: \(.affected_entity.name)
ENTITY ID: \(.affected_entity.id)
═══════════════════════════════════════════════════════════
"'
    else
      echo "No vulnerability records found in the last 30 days"
    fi
  else
    echo "❌ Query returned error:"
    cat vuln_all.json | jq '.error'
  fi
else
  echo "❌ Query 2 failed"
fi

echo ""
echo "=== Query Complete ==="
