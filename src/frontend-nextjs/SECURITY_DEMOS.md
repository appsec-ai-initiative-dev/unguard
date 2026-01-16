# Security Demo Use Cases

This document describes the security demonstration features implemented in the Next.js frontend for Dynatrace detection testing.

## Overview

Two separate security attack simulations are available:

| Use Case | Route | Attack Type | CVE |
|----------|-------|-------------|-----|
| React2Shell | `/rce` | Remote Code Execution via Server Actions | CVE-2025-55182 |
| Shai-Hulud | `/shai-hulud` | Supply Chain Attack via compromised package | N/A (simulated) |

Both demos are designed to produce **Indicators of Compromise (IoC)** that Dynatrace can detect and alert on.

---

## React2Shell (`/rce`)

### Description

Demonstrates CVE-2025-55182 - a Remote Code Execution vulnerability in React Server Actions where malicious payloads exploit argument deserialization to execute arbitrary code on the server.

**Note:** This vulnerability has been patched in Next.js 15.5.9. This demo simulates the attack behavior for educational and detection testing purposes.

### Files

- `app/rce/page.tsx` - Client-side UI for triggering the attack
- `app/rce/actions.ts` - Server action that simulates post-exploitation behavior

### Behavior

When triggered, the server action:

1. **Spawns child processes** - Executes `curl` and `wget` to simulate attacker exfiltration tools
2. **Harvests environment variables** - Collects env vars containing TOKEN, SECRET, KEY, or PASSWORD
3. **Exfiltrates data via HTTP POST** - Sends harvested data to a webhook endpoint

### Dynatrace IoCs

| IoC Type | Description | Detection Method |
|----------|-------------|------------------|
| Process Spawning | Node.js spawns `curl` and `wget` child processes | Dynatrace Application Security - Process monitoring |
| Outbound HTTP | POST request with exfiltrated data | Distributed tracing - Outbound HTTP span |
| Suspicious Headers | `X-Attack: react2shell`, `X-CVE: CVE-2025-55182` | Request attribute capture |

### Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `REACT2SHELL_EXFIL_URL` | Target URL for exfiltration | `https://webhook.site/1c129c66-a498-4463-990f-cb7072441d28` |

### Example Exfiltration Payload

```json
{
  "attack": "react2shell",
  "cve": "CVE-2025-55182",
  "hostname": "server-hostname",
  "platform": "linux",
  "user": "node",
  "cwd": "/app",
  "secrets": {
    "DATABASE_PASSWORD": "secr****",
    "API_TOKEN": "tok_****"
  },
  "timestamp": "2025-12-18T10:00:00.000Z"
}
```

---

## Shai-Hulud (`/shai-hulud`)

### Description

Demonstrates a supply chain attack via the simulated compromised `@ctrl/tinycolor` package. The malicious package harvests secrets from environment variables and the filesystem, then exfiltrates them to an attacker-controlled URL.

### Files

- `app/shai-hulud/page.tsx` - Client-side UI for triggering the attack
- `app/shai-hulud/actions.ts` - Server action that triggers exfiltration within a traced request context
- `vendor/ctrl-tinycolor-sim/` - Vendored malicious package simulation

### Behavior

When triggered, the server action:

1. **Calls `harvestBenignSecrets()`** from the compromised package
2. **Collects SAFE_TOKEN_* values** from environment variables
3. **Scans `fake-secrets/` directory** for files containing tokens
4. **Exfiltrates via HTTP POST** within the traced request context (produces Dynatrace spans)

### Dynatrace IoCs

| IoC Type | Description | Detection Method |
|----------|-------------|------------------|
| Outbound HTTP | POST request with harvested secrets | Distributed tracing - Outbound HTTP span (child of incoming request) |
| Package Metadata | Headers identify compromised package | Request attribute capture |
| Secret Harvesting | Environment/file scanning for tokens | Log analysis |

### Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `CTRL_TINYCOLOR_EXFIL_URL` | Target URL for exfiltration | `https://webhook.site/1c129c66-a498-4463-990f-cb7072441d28` |
| `CTRL_TINYCOLOR_FAKE_SECRET_DIR` | Directory to scan for secrets | `./fake-secrets` |
| `CTRL_TINYCOLOR_DISABLE_EXFIL` | Set to any value to disable exfiltration | (unset) |
| `SAFE_TOKEN_*` | Demo tokens to be "harvested" | (unset) |

### Setup for Demo

1. Set environment variables with `SAFE_TOKEN_` prefix:
   ```bash
   export SAFE_TOKEN_001="demo-secret-value"
   export SAFE_TOKEN_002="another-secret"
   ```

2. Or create a `fake-secrets/` directory with token files:
   ```bash
   mkdir fake-secrets
   echo "SAFE_TOKEN_001=mysecret" > fake-secrets/tokens.txt
   ```

### Example Exfiltration Payload

```json
{
  "package": "@ctrl/tinycolor",
  "version": "3.6.0-sim",
  "source": "shai-hulud-server-action",
  "artifacts": {
    "envMatches": [
      { "key": "SAFE_TOKEN_001", "value": "demo-secret-value" }
    ],
    "fileMatches": [
      { "file": "/app/fake-secrets/tokens.txt", "snippet": "SAFE_TOKEN_001=mysecret" }
    ],
    "harvestedAt": "2025-12-18T10:00:00.000Z",
    "empty": false
  },
  "hostname": "server-hostname",
  "timestamp": "2025-12-18T10:00:00.000Z"
}
```

---

## Why Server Actions for Dynatrace Spans?

Dynatrace auto-instrumentation traces outbound HTTP requests **only when they occur within a traced request context** (i.e., as a child of an incoming request span).

The original `@ctrl/tinycolor` exfiltration ran at **module import time** (server startup), which means:
- No parent request span existed
- Outbound HTTP calls were orphaned and not traced

By moving exfiltration into **Server Actions**, the HTTP calls now:
- Execute within the context of an incoming POST request
- Appear as child spans in Dynatrace distributed traces
- Are properly attributed to the application

---

## Timeline Integration (Shai-Hulud)

The `@ctrl/tinycolor` package is also used in `components/Timeline/TimelineHome.tsx` for the background intensity slider. This demonstrates how a compromised package can be used innocuously in the UI while performing malicious actions server-side.

Client-side functions exported:
- `lighten(color, percent)` - Lightens a hex color
- `darken(color, percent)` - Darkens a hex color
- `simulateBeacon(metadata)` - Emits console beacon (client-side only)

---

## HTTP Headers for Detection Rules

Both demos include distinctive HTTP headers that can be used for Dynatrace detection rules:

### React2Shell
```
X-Attack: react2shell
X-CVE: CVE-2025-55182
Content-Type: application/json
```

### Shai-Hulud
```
X-Attack: shai-hulud
X-Package: @ctrl/tinycolor
Content-Type: application/json
```

These headers can be captured as request attributes in Dynatrace for alerting and filtering.
