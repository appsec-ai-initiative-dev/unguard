# Security Findings Verification

DQL queries + MCP tool calls to verify that `trigger-security-findings.sh` /
`attackSimulator` CronJob produced findings, problems, and spans in Dynatrace.

Wait ~2-5 min after triggering attacks for OneAgent to ship data to Grail.

## 1. Davis Problems (should be AUTO-OPENED by RAP detections)

```
mcp3_query-problems(status="ACTIVE", history="30m")
```

Expected problem titles (one per attack):
- `SQL Injection attack detected on unguard-profile-service`
- `Command Injection attack detected on unguard-profile-service`
- `Command Injection attack detected on unguard-proxy-service`
- `SSRF attack detected on unguard-proxy-service`
- `SQL Injection attack detected on unguard-user-auth-service`
- `JNDI Injection attack detected on unguard-microblog-service`

Each problem's root cause = the RAP detection; impact = the affected service;
evidence includes the correlated span.

## 2. Runtime Attack Protection detections (DETECTION_FINDING)

```
mcp3_get-security-events-summary(
  eventTypes="DETECTION_FINDING",
  timeRange="30m",
  summarizationString="| summarize by:{finding.title, dt.security.risk.level, object.name}, {count=count()}"
)
```

Filter for unguard services:
```
fetch security.events, from:now()-30m
| filter event.type == "DETECTION_FINDING"
| filter matchesPhrase(object.name, "unguard")
| fields finding.time.created, finding.title, dt.security.risk.level, object.name, finding.id
| sort finding.time.created desc
```

## 3. Spans (attack request flow)

Frontend -> profile-service (SQLi + CMDi via bio):
```
fetch spans, from:now()-30m
| filter matchesPhrase(service.name, "unguard-profile-service")
| filter matchesPhrase(span.name, "/user/") or matchesPhrase(span.name, "bio")
| fields timestamp, trace_id, span.name, span.kind, http.request.method, url.full, http.response.status_code
| sort timestamp desc
```

Frontend -> proxy-service (CMDi + SSRF):
```
fetch spans, from:now()-30m
| filter matchesPhrase(service.name, "unguard-proxy-service")
| fields timestamp, trace_id, span.name, url.full, http.response.status_code
| sort timestamp desc
```

Frontend -> microblog-service (JNDI/Log4Shell):
```
fetch spans, from:now()-30m
| filter matchesPhrase(service.name, "unguard-microblog-service")
| filter matchesPhrase(span.name, "post")
| fields timestamp, trace_id, span.name, http.request.method
| sort timestamp desc
```

## 4. Runtime Vulnerability Analytics (Log4Shell CVE-2021-44228)

```
mcp3_get-dynatrace-vulnerabilities(
  cves="CVE-2021-44228",
  customSummarizationAndFieldsSelection="| fields vulnerability.display_id, vulnerability.title, vulnerability.risk.level, affected_entity.names, vulnerability.davis_assessment.vulnerable_function_status, vulnerability.davis_assessment.exploit_status, vulnerability.davis_assessment.exposure_status"
)
```

Expected: `vulnerable_function_status=IN_USE`, `exploit_status=AVAILABLE`,
`exposure_status=PUBLIC_NETWORK` on microblog-service after the JNDI attack.

## 5. Runtime Vulnerability Analytics (@postman/aether-icons malicious package)

The `@postman/aether-icons` package (versions 2.23.2-2.23.4) was compromised in
the Shai-Hulud 2.0 npm supply-chain attack (Nov 24, 2025). Advisory IDs:
`MAL-2025-190676` (OSV), `GMS-2025-245` (GitLab). No traditional CVE — it's a
malicious-code advisory sourced from the Dynatrace Vulnerability feed (OSV/GHSA).

The frontend depends on `@postman/aether-icons@2.23.2` via a local file dependency
(`src/frontend-nextjs/simulated-packages/@postman/aether-icons`). To make OneAgent
inventory it as a software component (so RVA can match the advisory), the package
is loaded at runtime from `node_modules` in `tracing.js` via `NODE_OPTIONS --require`,
outside the Next.js webpack bundle. See
`src/frontend-nextjs/tracing.js` and `chart/templates/frontend.yaml` (NODE_OPTIONS).

### Verify the component is inventoried

```
mcp3_get-dynatrace-vulnerabilities(
  components="@postman/aether-icons",
  customSummarizationAndFieldsSelection="| fields vulnerability.display_id, vulnerability.title, vulnerability.risk.level, vulnerability.type, affected_entity.names, affected_entity.vulnerable_component.names, vulnerability.resolution.status"
)
```

Expected: one vulnerability with `vulnerability.type` indicating malicious code,
`affected_entity.vulnerable_component.names` containing `@postman/aether-icons`,
`affected_entity.names` containing `unguard-frontend` / `next-js-frontend`.

### Threat-hunting workflow (OTX → IOC → affected services)

This simulates the "AlienVault OTX pulse → IOC → am I affected?" workflow:

1. **OTX pulse** describes the Shai-Hulud 2.0 attack with IOC = compromised npm
   package name + version range (`@postman/aether-icons` 2.23.2-2.23.4).
2. **Hunt in Grail** for any process running that package:

```
fetch security.events, from:now()-7d
| filter event.type == "VULNERABILITY_STATE_REPORT_EVENT"
| filter matchesPhrase(affected_entity.vulnerable_component.name, "aether-icons")
| fields vulnerability.display_id, vulnerability.title, vulnerability.risk.level,
        affected_entity.names, affected_entity.vulnerable_component.names,
        vulnerability.first_seen, vulnerability.resolution.status
| sort vulnerability.first_seen desc
```

3. **List all software components** on the frontend process to confirm inventory:

```
mcp3_get-dynatrace-vulnerabilities(
  entityIdsOrNames="unguard-frontend,next-js-frontend",
  customSummarizationAndFieldsSelection="| summarize by:{affected_entity.vulnerable_component.names}, {vulnerabilities=count(), titles=collectDistinct(vulnerability.title), risk_levels=collectDistinct(vulnerability.risk.level)}"
)
```

### Why OneAgent didn't inventory it before this fix

Next.js `output: 'standalone'` bundles `@postman/aether-icons`'s code into the
server bundle at build time. OneAgent's Node.js module hook only reports packages
that are `require()`'d from `node_modules` at runtime — bundled code is invisible.
Loading the package in `tracing.js` (which runs before the Next.js server via
`NODE_OPTIONS --require`) makes OneAgent see the `require()` and inventory the
component. Restart the frontend pod after deploying to trigger re-inventory
(RVA matches against vulnerability feeds every ~1-5 min).

## 6. End-to-end correlation (problem -> detection -> span -> vulnerability)

```
fetch dt.davis.problems, from:now()-30m
| filter event.category == "SECURITY"
| filter matchesPhrase(event.description, "unguard")
| fields display_id, event.status, event.start, event.description, affected_entity_ids
| sort event.start desc
```

Then for each problem ID, fetch the linked spans:
```
fetch spans, from:now()-30m
| filter matchesPhrase(service.name, "unguard")
| filter span.kind == "server"
| fields trace_id, span.id, parent_span_id, service.name, span.name, url.full, http.response.status_code
| sort timestamp desc
```

## 7. React2Shell (CVE-2025-55182, Next.js frontend RCE)

Step `[8/8]` of `trigger-security-findings.sh` (or the malicious-load-generator
`post_react2shell` task) POSTs the React Flight exploit payload to the frontend root
page (`/ui/`). The payload executes **unauthenticated**, during request deserialization
before any app code runs.

### RVA finding (present regardless of the attack)

```
mcp3_get-dynatrace-vulnerabilities(
  cves="CVE-2025-55182",
  customSummarizationAndFieldsSelection="| fields vulnerability.display_id, vulnerability.title, vulnerability.risk.level, affected_entity.names, affected_entity.vulnerable_component.names, vulnerability.davis_assessment.exploit_status, vulnerability.resolution.status"
)
```

Expected: `Next.js is vulnerable to RCE in React flight protocol` with
`affected_entity.vulnerable_component.names` containing `next` (15.0.4) on the frontend.

### Verify code execution

The default payload writes command output into the frontend container:

```bash
kubectl exec -n unguard deploy/unguard-frontend -- cat /tmp/pwned.txt
```

### Attack span + process IoCs

```
fetch spans, from:now()-30m
| filter matchesPhrase(service.name, "unguard-frontend")
| filter http.request.method == "POST"
| fields timestamp, trace_id, span.name, url.full, http.response.status_code
| sort timestamp desc
```

Look for `POST /ui/` with content type `multipart/form-data` (usually HTTP 500 — the
command still executes). In the OneAgent process view for the frontend, the Node.js
server process spawns `sh -c` / `curl` children during the attack window.

Note: RAP's injection-style attack rules (SQLi/CMDi/SSRF/JNDI) do not cover Flight
deserialization RCE — do not expect a DETECTION_FINDING for this attack. The demo
story is RVA (known CVE on running code) + runtime IoC visibility (process chain,
outbound exfil span) + optional safe simulation via the `/ui/rce` page.

### Why the payload is not inline / not in the CronJob

Endpoint AV (Microsoft Defender) deletes script/YAML files containing the inline
exploit string. The payload therefore lives only in
`exploit-toolkit/exploits/react2shell/payload/react2shell-payload.txt` (a `.txt`, which
AV tolerates) and is read at runtime by `trigger-security-findings.sh` and the
exploit-toolkit CLI (`python exploit.py react2shell "id" --target <host>`). The
`attackSimulator` CronJob does not fire this attack; trigger it locally instead.

## Deploy + trigger

```bash
# Option A: Helm (enables periodic CronJob every 2h)
helm upgrade unguard ./chart -f aws-values.yaml \
  --set attackSimulator.enabled=true

# Manual one-shot from CronJob:
kubectl create job --from=cronjob/unguard-attack-simulator-trigger \
  -n unguard attack-sim-manual-1

# Option B: Local script (needs reachability to frontend)
FRONTEND_ADDR=<ingress-or-port-forward> ./trigger-security-findings.sh

# Option C: React2Shell only, via exploit-toolkit CLI (no login needed)
cd exploit-toolkit && python exploit.py react2shell "id > /tmp/pwned.txt" --target <frontend-host>
```
