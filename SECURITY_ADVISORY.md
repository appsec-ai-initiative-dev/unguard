# 🔒 Security Advisory - Unguard Frontend

**Date:** October 16, 2025  
**Severity:** CRITICAL (Now RESOLVED)  
**Status:** ✅ FIXED

---

## ⚠️ IMPORTANT: This is a Demo Application

**Unguard is an intentionally insecure demonstration application** designed to showcase Dynatrace's security monitoring capabilities. It contains deliberate vulnerabilities for training and demonstration purposes.

---

## Critical Vulnerabilities Fixed

### ✅ 1. Axios DoS Vulnerability (HIGH)
- **Issue:** CVE-2024 - Denial of Service through lack of data size check
- **Severity:** HIGH (CVSS 7.5)
- **Fixed:** Updated axios from 1.8.4 → 1.12.2
- **Status:** RESOLVED

### ✅ 2. Next.js Critical Vulnerabilities (CRITICAL)
Multiple critical security issues in Next.js 15.0.4:
- **DoS with Server Actions** (GHSA-7m27-7ghc-44w9)
- **Information exposure in dev server** (GHSA-3h52-269p-cp9r)
- **Cache poisoning DoS** (GHSA-67rr-84xm-4c7r)
- **Cache Key Confusion** (GHSA-g5qg-72qw-gw5v)
- **Content Injection** (GHSA-xv57-4mr9-wg8v)

**Fixed:** Updated Next.js from 15.0.4 → 15.5.5  
**Status:** RESOLVED

### ✅ 3. Swagger UI XSS Vulnerabilities (HIGH)
Multiple XSS and prototype pollution issues:
- **Prototype pollution** (GHSA-mmhx-hmjr-r674, CVSS 7.0)
- **Nesting-based mXSS** (GHSA-gx9m-whjm-85jf, CVSS 10.0)
- **XSS vulnerabilities** (GHSA-vhxf-7vqr-mrjg)

**Fixed:** Updated swagger-ui-react from 4.19.1 → 5.29.4  
**Status:** RESOLVED

---

## 🎯 @ctrl/tinycolor - Intentional Demo Package

### What is it?
The `@ctrl/tinycolor@4.1.1` package is **intentionally included** as part of Unguard's security demonstration features. This package:

1. **Simulates a supply chain attack** for training purposes
2. **Uses a local safe implementation** via Verdaccio (local npm registry)
3. **Triggers Dependabot alerts** to demonstrate security scanning
4. **Generates Dynatrace security events** for monitoring demos

### Safe Implementation
The application uses a **safe simulation** located at:
```
src/frontend-nextjs/vendor/ctrl-tinycolor-sim/
```

This simulation:
- ✅ Mimics malicious behavior **without actual harm**
- ✅ Uses fake/demo secrets only (SAFE_TOKEN_*)
- ✅ Sends telemetry to demo endpoints only
- ✅ Bundles a benign TruffleHog binary for scanning demos
- ✅ All behavior is logged to console for transparency

### How It Works
1. **Verdaccio** (local npm registry) runs on `http://127.0.0.1:4873`
2. The `.npmrc` file routes `@ctrl` packages to Verdaccio
3. The safe simulation is published to Verdaccio as version 4.1.1
4. npm installs the **safe simulation** instead of the real malicious package

---

## 🛡️ Running Unguard Safely

### Prerequisites
- Node.js 18 or later
- npm 8 or later
- Docker (for containerized deployment)

### Option 1: Using Verdaccio (Recommended for Full Demo)

**Step 1: Start Verdaccio**
```bash
npx verdaccio --config ops/verdaccio/config.yaml
```

**Step 2: Create Registry User (First Time Only)**
```bash
npm adduser --registry http://127.0.0.1:4873
# Username: demo-user
# Password: (choose a password)
# Email: demo@example.com
```

**Step 3: Publish Safe Simulation Package**
```bash
node ops/verdaccio/publish-tinycolor.js
```

**Step 4: Install Dependencies**
```bash
cd src/frontend-nextjs
npm install
```

**Step 5: Build and Run**
```bash
npm run build
npm start
```

### Option 2: Without Verdaccio (Skip @ctrl/tinycolor Demo)

If you want to run without the supply chain attack demo:

**Step 1: Remove the package reference**
```bash
cd src/frontend-nextjs
npm uninstall @ctrl/tinycolor
```

**Step 2: Update code to not import it**
Edit `src/frontend-nextjs/components/Timeline/TimelineHome.tsx`:
```typescript
// Remove or comment out:
// import { darken, lighten, simulateBeacon } from '@ctrl/tinycolor';

// Use alternative color manipulation or remove the feature
```

**Step 3: Install and build**
```bash
npm install
npm run build
npm start
```

---

## 🔍 Verification After Fix

### Check Installed Versions
```bash
cd src/frontend-nextjs
npm ls axios next swagger-ui-react
```

Expected output:
```
├── axios@1.12.2
├── next@15.5.5
└── swagger-ui-react@5.29.4
```

### Run Security Audit
```bash
npm audit
```

Expected: Only the intentional @ctrl/tinycolor warning should remain (if using Verdaccio).

### Build Test
```bash
npm run build
```

Should complete without errors.

---

## 📊 Dynatrace Validation

### Verify in Dynatrace RVA

Query to check vulnerability status:
```dql
fetch security.events, from:now() - 24h
| filter event.type == "VULNERABILITY_STATE_REPORT_EVENT"
| filter dt.entity.service == "frontend-nextjs"
| dedup {vulnerability.display_id, affected_entity.id}, sort: {timestamp desc}
| filter vulnerability.resolution_status == "OPEN"
| filter vulnerability.severity in ["CRITICAL", "HIGH"]
| summarize count = count(), by: {
    vulnerability_id = vulnerability.display_id,
    cve = vulnerability.references.cve,
    severity = vulnerability.severity,
    risk_score = vulnerability.risk_score
}
```

### Expected Results After Fix
- ✅ CVE-2025-49826 (HTTP Request Smuggling) - **RESOLVED**
- ✅ CVE-2024-3566 (Command Injection) - **RESOLVED**
- ⚠️ @ctrl/tinycolor GHSA alert - **EXPECTED** (intentional demo)

---

## 🚨 Security Best Practices

### For Production Use
**DO NOT use Unguard in production!** This application is intentionally insecure and designed for:
- Security training
- Dynatrace demonstrations
- Testing security scanning tools
- Learning about vulnerabilities

### For Demo Environments
1. ✅ Run in isolated networks only
2. ✅ Use Verdaccio for @ctrl/tinycolor simulation
3. ✅ Keep all dependencies updated
4. ✅ Monitor with Dynatrace Runtime Vulnerability Analytics
5. ✅ Restrict access to authorized users only
6. ✅ Never expose to the public internet

### Network Isolation
```yaml
# Example Kubernetes NetworkPolicy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: unguard-isolation
spec:
  podSelector:
    matchLabels:
      app: unguard
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          purpose: demo
```

---

## 📚 Additional Resources

### Documentation
- [Security Fix Notes](SECURITY_FIX_NOTES.md) - Comprehensive fix documentation
- [Vulnerability Investigation Report](VULNERABILITY_INVESTIGATION_REPORT.md) - Dynatrace findings
- [Remediation Plan](VULNERABILITY_REMEDIATION_PLAN.md) - Step-by-step fix guide
- [Quick Reference](VULNERABILITY_QUICK_REFERENCE.md) - Quick lookup guide
- [Executive Summary](EXECUTIVE_SUMMARY.md) - High-level overview

### Verdaccio Setup
- [ops/verdaccio/README.md](ops/verdaccio/README.md) - Detailed Verdaccio setup

### GitHub Workflows
- [.github/workflows/src-ghcr-build.yml](.github/workflows/src-ghcr-build.yml) - CI/CD pipeline

### External Links
- [Dynatrace Security Documentation](https://docs.dynatrace.com/docs/platform-modules/application-security)
- [GitHub Advisory Database](https://github.com/advisories)
- [Next.js Security](https://nextjs.org/docs/pages/building-your-application/configuring/security)

---

## 🎓 Learning Objectives

This vulnerability fix demonstrates:

1. **Runtime Vulnerability Detection** - How Dynatrace RVA identifies loaded vulnerabilities
2. **Supply Chain Security** - Safe simulation of compromised packages
3. **Dependency Management** - Importance of keeping dependencies updated
4. **Security Monitoring** - Using Davis AI for vulnerability prioritization
5. **Incident Response** - Systematic approach to vulnerability remediation

---

## 📞 Support

For questions about:
- **Security vulnerabilities**: Review the vulnerability reports
- **Verdaccio setup**: See ops/verdaccio/README.md
- **Dynatrace integration**: Check Dynatrace documentation
- **Demo usage**: Refer to the main README.md

---

## ✅ Summary

| Component | Before | After | Status |
|-----------|--------|-------|--------|
| axios | 1.8.4 (HIGH vuln) | 1.12.2 | ✅ FIXED |
| next | 15.0.4 (CRITICAL vulns) | 15.5.5 | ✅ FIXED |
| swagger-ui-react | 4.19.1 (HIGH vuln) | 5.29.4 | ✅ FIXED |
| @ctrl/tinycolor | 4.1.1 (DEMO) | 4.1.1 (safe sim) | ✅ SAFE DEMO |

**All critical production vulnerabilities have been resolved while maintaining the demo capabilities.**

---

**Last Updated:** October 16, 2025  
**Next Review:** As needed when new vulnerabilities are discovered  
**Maintained By:** Unguard Security Team
