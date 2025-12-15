# Dynatrace Security Queries - Implementation Summary

This document summarizes the implementation of Dynatrace security query capabilities for the Unguard project.

## 📋 What Was Implemented

### 1. Comprehensive Documentation

#### Main Documentation Files

- **`docs/DYNATRACE-SECURITY-QUERIES.md`** (24KB)
  - Complete DQL query reference for security events
  - 10 ready-to-use vulnerability query patterns
  - Best practices for vulnerability analysis
  - Davis assessment interpretation guide
  - Verification workflow for Dependabot alerts

- **`docs/DYNATRACE-INTEGRATION.md`** (10KB)
  - Complete integration guide
  - Setup instructions
  - Verification workflow examples
  - CI/CD integration patterns
  - Troubleshooting guide

- **`docs/QUICK-START-DYNATRACE.md`** (8KB)
  - 5-minute quick start guide
  - Common use cases with examples
  - Quick reference commands
  - Troubleshooting tips

### 2. Query Scripts

#### Python Script: `scripts/dynatrace/query_vulnerabilities.py` (17KB)

**Features:**
- Complete Dynatrace API client implementation
- Multiple query modes:
  - All open vulnerabilities
  - Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)
  - Vulnerabilities with function in use
  - Lookup specific CVE
- Multiple output formats: table, JSON, summary
- Configurable time ranges (default: 7 days)
- Comprehensive error handling

**Usage Examples:**
```bash
# All vulnerabilities
python3 query_vulnerabilities.py

# Critical only
python3 query_vulnerabilities.py --severity CRITICAL

# Function in use
python3 query_vulnerabilities.py --function-in-use

# Specific CVE
python3 query_vulnerabilities.py --cve CVE-2024-21508

# JSON output
python3 query_vulnerabilities.py --format json
```

#### Shell Script: `scripts/dynatrace/query_vulnerabilities.sh` (10KB)

**Features:**
- Bash wrapper for easier use
- Direct curl-based queries for simple cases
- Automatic fallback to Python script for advanced queries
- Color-coded output
- Dependency checking and installation
- Help documentation

**Usage Examples:**
```bash
# Simple query
./query_vulnerabilities.sh

# Critical vulnerabilities
./query_vulnerabilities.sh --severity CRITICAL

# Use Python for advanced features
./query_vulnerabilities.sh --use-python --function-in-use
```

#### Scripts README: `scripts/dynatrace/README.md` (10KB)

**Content:**
- Prerequisites and setup
- Detailed usage instructions
- Output format explanations
- Integration examples
- CI/CD pipeline examples
- Monitoring script examples

### 3. CI/CD Integration

#### GitHub Actions Workflow: `.github/workflows/dynatrace-security-scan.yml.example` (11KB)

**Features:**
- Automated vulnerability scanning on PRs and pushes
- Multiple scan types:
  - All vulnerabilities
  - Critical vulnerabilities
  - High vulnerabilities
  - Vulnerabilities with function in use
- Automated reporting:
  - Generates vulnerability summary
  - Posts results as PR comments
  - Uploads artifacts
  - Creates GitHub issues for critical findings
- Deployment gates:
  - Blocks deployment if critical vulnerabilities found
  - Configurable thresholds
  - Customizable failure conditions

**Triggers:**
- Pull requests to main
- Push to main branch
- Manual workflow dispatch
- Scheduled daily runs (8 AM UTC)

### 4. README Updates

Updated main `README.md` with:
- New "Security Analysis with Dynatrace" section
- Links to all documentation
- Quick overview of capabilities

## 🎯 Key Capabilities

### 1. Real-Time Vulnerability Queries

Query Dynatrace for vulnerabilities detected in running applications:
- Filter by severity level
- Filter by Davis assessments (function in use, exploit available, etc.)
- Query specific CVEs
- Configurable time ranges

### 2. Davis AI Assessment

Leverage Dynatrace Davis AI for context-aware risk assessment:
- **Vulnerable Function In Use**: Is the vulnerable code actually executed?
- **Public Exploit Available**: Are public exploits available?
- **Public Internet Exposure**: Is the service publicly accessible?
- **Data Assets Within Reach**: Can sensitive data be accessed?

### 3. Dependabot Alert Verification

Verify GitHub Dependabot alerts against runtime behavior:
1. Query Dynatrace by CVE
2. Check if vulnerability is detected in runtime
3. Verify if vulnerable function is in use
4. Make informed decision: confirm, lower priority, or dismiss

### 4. CI/CD Integration

Automate security scanning in deployment pipelines:
- Pre-deployment security gates
- Automated vulnerability reporting
- GitHub issue creation for tracking
- PR comments with scan results

### 5. Multiple Output Formats

Choose the format that fits your needs:
- **Table**: Human-readable with full details
- **JSON**: Machine-readable for automation
- **Summary**: Quick overview with counts

## 📊 Query Examples

### Query All Open Vulnerabilities
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
```

### Query Critical Vulnerabilities with Function In Use
```dql
fetch security.events, from:now()-7d
| filter event.provider=="Dynatrace"
     AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
| dedup {vulnerability.display_id, affected_entity.id}, sort:{timestamp desc}
| filter vulnerability.resolution.status == "OPEN"
     AND vulnerability.davis_assessment.vulnerable_function_status == "IN_USE"
| filter vulnerability.risk.score >= 9
```

### Verify Specific CVE
```dql
fetch security.events, from:now()-7d
| filter event.provider=="Dynatrace"
     AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
| filter in("CVE-2024-21508", vulnerability.references.cve)
| dedup {vulnerability.display_id, affected_entity.id}, sort:{timestamp desc}
| filter vulnerability.resolution.status == "OPEN"
```

## 🚀 Usage Scenarios

### Scenario 1: Daily Security Monitoring
```bash
# Morning security check
./query_vulnerabilities.sh --format summary

# Review critical issues
./query_vulnerabilities.sh --severity CRITICAL
```

### Scenario 2: Pre-Deployment Validation
```bash
# Check for blocking vulnerabilities
CRITICAL=$(python3 query_vulnerabilities.py --severity CRITICAL --format json | jq 'length')
if [ "$CRITICAL" -gt 0 ]; then
  echo "Deployment blocked"
  exit 1
fi
```

### Scenario 3: Dependabot Alert Verification
```bash
# Verify CVE-2024-21508
python3 query_vulnerabilities.py --cve CVE-2024-21508

# Decision:
# - Found + IN_USE → Fix immediately
# - Found + NOT_IN_USE → Lower priority
# - Not found → Dismiss alert
```

### Scenario 4: Weekly Security Report
```bash
# Generate comprehensive report
python3 query_vulnerabilities.py --format json > weekly_report.json

# Generate summary for management
./query_vulnerabilities.sh --format summary > weekly_summary.txt
```

## 🔧 Technical Details

### API Requirements
- Dynatrace API token with permissions:
  - `securityEvents.read`
  - `dql.query.execute`

### Dependencies
- Python 3.7+
- `requests` library
- `curl` (for shell script)
- `jq` (optional, for JSON processing)

### Environment Variables
```bash
export DT_ENVIRONMENT="https://your-environment.live.dynatrace.com"
export DT_API_TOKEN="your-api-token"
```

## 📈 Benefits

### 1. Risk-Based Prioritization
- Focus on vulnerabilities that are actually exploitable
- Reduce alert fatigue from false positives
- Prioritize based on runtime context

### 2. Automated Verification
- Verify Dependabot alerts automatically
- Reduce manual security triage effort
- Make data-driven security decisions

### 3. CI/CD Integration
- Block deployments with critical vulnerabilities
- Automated reporting and tracking
- Continuous security monitoring

### 4. Improved Efficiency
- Ready-to-use scripts and queries
- Multiple output formats for different use cases
- Comprehensive documentation

## 🎓 Best Practices

1. **Regular Scanning**: Run scans on every PR and daily
2. **Prioritization**: Focus on function IN_USE + exploit available
3. **Verification**: Always verify external alerts against Dynatrace
4. **Documentation**: Document all suppressions with reasons
5. **Automation**: Integrate into CI/CD pipelines

## 📚 Documentation Structure

```
unguard/
├── README.md (updated with Dynatrace section)
├── DYNATRACE-QUERIES-SUMMARY.md (this file)
├── docs/
│   ├── DYNATRACE-SECURITY-QUERIES.md (comprehensive DQL reference)
│   ├── DYNATRACE-INTEGRATION.md (integration guide)
│   └── QUICK-START-DYNATRACE.md (quick start guide)
├── scripts/
│   └── dynatrace/
│       ├── README.md (scripts documentation)
│       ├── query_vulnerabilities.py (Python script)
│       └── query_vulnerabilities.sh (shell script)
└── .github/
    └── workflows/
        └── dynatrace-security-scan.yml.example (CI/CD workflow)
```

## 🔗 Quick Links

- [Quick Start Guide](docs/QUICK-START-DYNATRACE.md) - Get started in 5 minutes
- [Integration Guide](docs/DYNATRACE-INTEGRATION.md) - Complete setup and usage
- [DQL Query Reference](docs/DYNATRACE-SECURITY-QUERIES.md) - All query patterns
- [Scripts Documentation](scripts/dynatrace/README.md) - Script usage details
- [CI/CD Example](.github/workflows/dynatrace-security-scan.yml.example) - GitHub Actions workflow

## 🎉 Summary

This implementation provides a complete solution for querying and analyzing Dynatrace security vulnerabilities:

✅ Comprehensive documentation (3 guides + scripts README)
✅ Production-ready scripts (Python + Shell)
✅ CI/CD integration example (GitHub Actions)
✅ Multiple query modes and output formats
✅ Davis AI assessment interpretation
✅ Dependabot alert verification workflow
✅ Best practices and troubleshooting guides

The solution enables teams to:
- Query vulnerabilities programmatically
- Verify alerts against runtime behavior
- Automate security scanning in CI/CD
- Make risk-based security decisions
- Reduce false positives and alert fatigue

---

**Ready to use**: All scripts and documentation are production-ready and can be used immediately with a Dynatrace environment.
