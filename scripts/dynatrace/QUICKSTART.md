# Dynatrace Vulnerability Tools - Quick Start Guide

Get up and running in 3 minutes! 🚀

## Step 1: Set Environment Variables

```bash
export DT_TENANT="https://abc12345.live.dynatrace.com"
export DT_API_TOKEN="dt0c01.XXXXXXXXXXXXXXXXXXXXXXXX"
```

**How to get these:**
- `DT_TENANT`: Your Dynatrace environment URL (found in browser when logged in)
- `DT_API_TOKEN`: Create in Settings → Access tokens → Generate token
  - Required scope: `storage:events:read`

## Step 2: Install Dependencies (Python only)

```bash
pip install requests
```

## Step 3: Run Your First Query

### Option A: Use Shell Script (Easiest)

```bash
cd scripts/dynatrace
./get-vulnerabilities.sh all
```

### Option B: Use Python Script

```bash
python3 get_vulnerabilities.py
```

### Option C: Use DQL in Dynatrace Notebooks

1. Open Dynatrace → Notebooks
2. Create new notebook
3. Add DQL tile
4. Copy query from `get-vulnerabilities.dql`
5. Run query

## Common Commands

### Get Critical Vulnerabilities

```bash
./get-vulnerabilities.sh critical --format markdown
```

### Get High-Priority (Function In Use)

```bash
./get-vulnerabilities.sh priority
```

### Generate Summary Report

```bash
./get-vulnerabilities.sh summary --output report.md
```

### Check Specific CVE

```bash
python3 get_vulnerabilities.py --cve CVE-2024-38816
```

## Sample Output

See `sample-output.json` for example output format.

**Key Fields:**
- `vuln_id`: Unique vulnerability identifier
- `severity`: CRITICAL, HIGH, MEDIUM, LOW
- `davis_risk_score`: Davis AI calculated risk (0-10)
- `function_in_use`: **CRITICAL** - Is vulnerable code executed?
- `public_exploit`: Are public exploits available?
- `cve_ids`: CVE identifiers
- `entity_name`: Affected service/process

## Understanding Davis Assessments

Davis AI provides runtime risk assessment that's more accurate than CVSS alone:

| Field | What It Means | Priority |
|-------|---------------|----------|
| `function_in_use = true` | Vulnerable code IS executed | 🔴 HIGH |
| `function_in_use = false` | Vulnerable code NOT executed | 🟢 LOW |
| `public_exploit = true` | Public exploits exist | 🔴 HIGH |
| `davis_risk_score > 7.0` | High real-world risk | 🟠 MEDIUM |

**Example:** A CRITICAL vulnerability with `function_in_use = false` has lower real-world risk than a HIGH vulnerability with `function_in_use = true`.

## Prioritization Guide

**P1 (Fix Immediately):**
- `severity = CRITICAL` AND `function_in_use = true`
- `public_exploit = true` AND `function_in_use = true`

**P2 (Fix This Sprint):**
- `severity = HIGH` AND `function_in_use = true`
- `davis_risk_score > 7.0`

**P3 (Schedule):**
- `severity = CRITICAL` AND `function_in_use = false`
- `severity = HIGH` AND `function_in_use = false`

**P4 (Monitor):**
- `severity = MEDIUM` or `LOW`
- `function_in_use = false`

## Troubleshooting

### "No vulnerabilities found"

Try increasing the timeframe:
```bash
python3 get_vulnerabilities.py --days 30
```

### "Authentication failed"

1. Check `DT_TENANT` includes `https://`
2. Verify `DT_API_TOKEN` is correct
3. Confirm token has `storage:events:read` scope

### "requests module not found"

Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Next Steps

- Read [README.md](./README.md) for detailed documentation
- Check [EXAMPLES.md](./EXAMPLES.md) for advanced use cases
- Review [get-vulnerabilities.dql](./get-vulnerabilities.dql) for query patterns

## Quick Reference

| Command | Description |
|---------|-------------|
| `./get-vulnerabilities.sh all` | Get all vulnerabilities |
| `./get-vulnerabilities.sh critical` | Critical + High only |
| `./get-vulnerabilities.sh priority` | Function in use |
| `./get-vulnerabilities.sh summary` | Summary report |
| `./get-vulnerabilities.sh recent` | Last 24 hours |
| `./get-vulnerabilities.sh help` | Show all options |

## Need Help?

1. Check [EXAMPLES.md](./EXAMPLES.md) for more examples
2. Review [README.md](./README.md) for field reference
3. Open an issue in the repository

---

**Pro Tip:** Always prioritize by `function_in_use` status, not just severity!
