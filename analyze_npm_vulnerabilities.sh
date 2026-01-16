#!/bin/bash

echo "═══════════════════════════════════════════════════════════"
echo "  NPM/JavaScript Vulnerability Analysis"
echo "  Dependabot Alerts for unguard application"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Filter for npm ecosystem only
cat dependabot_alerts_array.json | jq -r '.[] | select(.dependency.package.ecosystem == "npm") | {
  alert_number: .number,
  cve: .security_advisory.cve_id,
  ghsa: .security_advisory.ghsa_id,
  severity: .security_advisory.severity,
  cvss_score: .security_advisory.cvss.score,
  summary: .security_advisory.summary,
  package: .dependency.package.name,
  vulnerable_version: .security_vulnerability.vulnerable_version_range,
  first_patched: .security_vulnerability.first_patched_version,
  manifest: .dependency.manifest_path,
  scope: .dependency.scope
}' | jq -s 'sort_by(-.cvss_score)' > npm_vulnerabilities.json

echo "Found $(cat npm_vulnerabilities.json | jq 'length') npm/JavaScript vulnerabilities"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""

# Display detailed information
cat npm_vulnerabilities.json | jq -r '.[] | "
═══════════════════════════════════════════════════════════
🔴 DEPENDABOT ALERT #\(.alert_number)
═══════════════════════════════════════════════════════════

📋 CVE ID: \(.cve // "N/A")
📋 GHSA ID: \(.ghsa)
📊 Severity: \(.severity | ascii_upcase)
📊 CVSS Score: \(.cvss_score // "N/A")

───────────────────────────────────────────────────────────
📦 PACKAGE DETAILS
───────────────────────────────────────────────────────────
Package Name: \(.package)
Vulnerable Versions: \(.vulnerable_version)
First Patched Version: \(.first_patched // "N/A")
Manifest File: \(.manifest)
Dependency Scope: \(.scope // "N/A")

───────────────────────────────────────────────────────────
🔍 VULNERABILITY SUMMARY
───────────────────────────────────────────────────────────
\(.summary)

"'

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  SUMMARY BY SEVERITY"
echo "═══════════════════════════════════════════════════════════"
echo ""

cat npm_vulnerabilities.json | jq -r 'group_by(.severity) | .[] | "
\(.[0].severity | ascii_upcase): \(length) vulnerabilities"'

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  TOP 10 HIGHEST CVSS SCORES"
echo "═══════════════════════════════════════════════════════════"
echo ""

cat npm_vulnerabilities.json | jq -r '.[:10] | .[] | "
Alert #\(.alert_number): \(.package) - CVSS \(.cvss_score // "N/A") - \(.severity | ascii_upcase)
  CVE: \(.cve // "N/A")
  Summary: \(.summary)"'

