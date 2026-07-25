# Build Runner (CI/CD Supply Chain Attack Demo)

The build runner simulates a CI/CD pipeline worker that installs npm dependencies containing a compromised package (`@ctrl/tinycolor` simulation). The malicious postinstall script harvests build secrets from environment variables and exfiltrates them to an attacker-controlled endpoint.

## Architecture

- **HTTP server** (`server.js`): Listens on port 8080 and exposes a `/trigger-build` endpoint. When triggered, it runs the exfiltration within a traced request context so Dynatrace captures the full trace (server span → internal span → outbound client span).
- **OTel SDK** (`tracing.js`): Bootstraps OpenTelemetry with `HttpInstrumentation` and `UndiciInstrumentation`. The Dynatrace OneAgent bridge intercepts the OTel SDK and forwards spans to Grail.
- **Compromised package** (`ctrl-tinycolor-sim/`): Locally vendored simulation of the `@ctrl/tinycolor` supply chain attack. See [ctrl-tinycolor-sim/README.md](ctrl-tinycolor-sim/README.md) for details.

## Why an HTTP server?

The Dynatrace OneAgent bridge only forwards traces that have a **server span entry point** (an incoming HTTP request). A standalone outbound POST with no parent server span would not be forwarded. The HTTP server approach ensures every exfil trace has a server span as its root, making the outbound exfil POST a child client span that gets forwarded to Grail.

## Endpoints

| Endpoint          | Method | Description                                                        |
|-------------------|--------|--------------------------------------------------------------------|
| `/`               | GET    | Health check — returns a readiness message.                        |
| `/trigger-build`  | POST   | Triggers the supply chain exfiltration simulation.                 |

## Environment variables

| Name                        | Description                                                          | Default                                                              |
|-----------------------------|----------------------------------------------------------------------|----------------------------------------------------------------------|
| `OTEL_SERVICE_NAME`         | OpenTelemetry service name                                           | `unguard-build-runner`                                               |
| `OTEL_RESOURCE_ATTRIBUTES`  | OpenTelemetry resource attributes                                    | `service.name=unguard-build-runner,service.namespace=unguard`       |
| `NODE_OPTIONS`              | Loads the OneAgent and tracing.js via `--require`                    | (set by Helm chart)                                                  |
| `CTRL_TINYCOLOR_EXFIL_URL`  | Exfiltration endpoint URL                                            | `https://webhook.site/1c129c66-a498-4463-990f-cb7072441d28`        |
| `CTRL_TINYCOLOR_DISABLE_EXFIL` | Set to `1` to disable exfiltration while keeping console logging  | (empty)                                                              |

The following build secrets are injected as environment variables for the demo:

- `NPM_TOKEN`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `GITHUB_TOKEN`, `GCP_SERVICE_ACCOUNT_KEY`, `DOCKER_PASSWORD`, `PYPI_API_TOKEN`, `CODECOV_TOKEN`

## Dynatrace span flow

When `/trigger-build` is called, the following spans are generated and forwarded to Grail:

1. **`POST` (server span)** — incoming request to `/trigger-build`
2. **`npm-install-build` (internal span)** — custom span wrapping the exfil logic
3. **`POST` (client span)** — outbound exfiltration to `webhook.site`

## Manual triggering

```bash
# From within the cluster
kubectl exec -n ci-cd deploy/unguard-build-runner -- wget -qO- http://localhost:8080/trigger-build

# From a local machine with port-forward
kubectl port-forward -n ci-cd svc/unguard-build-runner 8080:8080
curl -X POST http://localhost:8080/trigger-build
```

## Periodic triggering

A Kubernetes CronJob (`unguard-build-runner-trigger`) triggers the exfil every 6 hours by default. See [docs/SUPPLY-CHAIN-DEMO.md](../../docs/SUPPLY-CHAIN-DEMO.md) for details.
