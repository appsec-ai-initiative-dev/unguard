# Supply Chain Attack Demo

This demo showcases two supply chain attack scenarios using a compromised npm package (`@ctrl/tinycolor` simulation). Both scenarios generate traces that flow to Dynatrace Grail, where they can be detected as Indicators of Compromise (IoCs).

## Scenarios

### 1. CI/CD Build Runner (build-time exfiltration)

Simulates a CI/CD pipeline worker that installs a compromised npm package. The malicious postinstall script harvests build secrets from environment variables and exfiltrates them to an attacker-controlled endpoint.

- **Service**: `unguard-build-runner` (namespace: `ci-cd`)
- **Compromised package**: `@ctrl/tinycolor@3.6.0-sim` (locally vendored)
- **Exfil target**: `https://webhook.site/1c129c66-a498-4463-990f-cb7072441d28`
- **Harvested secrets**: `NPM_TOKEN`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `GITHUB_TOKEN`, `GCP_SERVICE_ACCOUNT_KEY`, `DOCKER_PASSWORD`, `PYPI_API_TOKEN`, `CODECOV_TOKEN`

See [src/build-runner/README.md](../src/build-runner/README.md) for technical details.

### 2. Frontend Server Action (runtime exfiltration)

Simulates a runtime supply chain attack where the compromised package is imported by the frontend application. A server action triggers the exfiltration within a traced request context.

- **Service**: `unguard-frontend` (namespace: `unguard`)
- **Trigger endpoint**: `/ui/shai-hulud` (POST server action)
- **Compromised package**: `@ctrl/tinycolor@3.6.0-sim`
- **Exfil target**: `https://webhook.site/1c129c66-a498-4463-990f-cb7072441d28`

See [src/frontend-nextjs/app/shai-hulud/](../src/frontend-nextjs/app/shai-hulud/) for the server action implementation.

## Dynatrace span flow

Both scenarios generate traces with the following span structure:

```
Server span (incoming request)
  └── Internal span (exfil logic)
        └── Client span (outbound POST to webhook.site)
```

The Dynatrace OneAgent bridge intercepts the OpenTelemetry SDK and forwards these spans to Grail. The outbound `POST` client span to `webhook.site` is the key IoC.

### Querying spans in Grail

```dql
// Build-runner exfil spans
fetch spans
| filter service.name == "unguard-build-runner"
| filter span.kind == "client" and contains(url.full, "webhook.site")
| fields timestamp, span.name, url.full, span.kind

// Frontend exfil spans
fetch spans
| filter service.name == "unguard-frontend"
| filter span.kind == "client" and contains(url.full, "webhook.site")
| fields timestamp, span.name, url.full, span.kind
```

## Periodic triggering

Both scenarios are triggered automatically every 6 hours via Kubernetes CronJobs:

| CronJob                              | Namespace | Schedule      | Description                                          |
|--------------------------------------|-----------|---------------|------------------------------------------------------|
| `unguard-build-runner-trigger`       | `ci-cd`   | `0 */6 * * *` | POSTs to `unguard-build-runner:8080/trigger-build`   |
| `unguard-shai-hulud-trigger`         | `default` | `0 */6 * * *` | Puppeteer visits `/ui/shai-hulud` and clicks trigger |

### Manual triggering

```bash
# Build-runner
kubectl create job --from=cronjob/unguard-build-runner-trigger -n ci-cd manual-trigger-1

# Frontend
kubectl create job --from=cronjob/unguard-shai-hulud-trigger manual-trigger-1
```

### Adjusting the schedule

Edit `chart/values.yaml`:

```yaml
buildRunner:
  trigger:
    schedule: "0 */6 * * *"  # every 6 hours

shaiHuludTrigger:
  schedule: "0 */6 * * *"  # every 6 hours
```

## Helm chart configuration

Enable both scenarios in your Helm values:

```yaml
buildRunner:
  enabled: true

shaiHuludTrigger:
  enabled: true
```

Or via command line:

```sh
helm install unguard ./chart \
  --set buildRunner.enabled=true \
  --set shaiHuludTrigger.enabled=true
```

## Key implementation detail: OneAgent bridge and server spans

The Dynatrace OneAgent bridge only forwards OpenTelemetry traces that have a **server span entry point** (an incoming HTTP request). A standalone outbound HTTP POST with no parent server span will not be forwarded to Grail.

This is why:

- The **build-runner** runs an HTTP server with a `/trigger-build` endpoint instead of a standalone script. The incoming curl request from the CronJob creates a server span, and the exfil POST becomes a child client span.
- The **frontend** uses a Next.js server action (POST to `/ui/shai-hulud`) triggered by a Puppeteer click. The server action creates a server span, and the exfil POST becomes a child client span.

Without this pattern, the OneAgent bridge silently drops the outbound exfil spans.
