# Shai-Hulud Supply Chain Attack Demo

This directory contains the frontend scenario for the supply chain attack demo. It simulates a runtime supply chain attack where a compromised npm package (`@ctrl/tinycolor`) is imported by the frontend application.

## Files

- `page.tsx` — The Shai-Hulud demo page with a trigger button
- `actions.ts` — Server action that triggers the exfiltration within a traced request context

## How it works

1. The user (or the `unguard-shai-hulud-trigger` CronJob) visits `/ui/shai-hulud`
2. Clicking the "Trigger Supply Chain Exfiltration" button calls the `triggerSupplyChainExfil` server action
3. The server action:
   - Launches the TruffleHog scan from the compromised `@ctrl/tinycolor` package
   - Harvests benign secrets from environment variables and the filesystem
   - Exfiltrates the harvested secrets to `https://webhook.site/1c129c66-a498-4463-990f-cb7072441d28` via `fetch()`
4. The outbound `POST` to `webhook.site` is captured as a client span by the OpenTelemetry HTTP instrumentation

## Dynatrace span flow

```
POST /ui/shai-hulud (server span)
  └── POST https://webhook.site/... (client span — the IoC)
```

The server action runs within a traced request context, so the outbound exfil POST is a child span of the server span. This is required for the Dynatrace OneAgent bridge to forward the trace to Grail.

## Periodic triggering

A Kubernetes CronJob (`unguard-shai-hulud-trigger`) triggers this scenario every 6 hours by using Puppeteer to visit the page and click the trigger button. See [docs/SUPPLY-CHAIN-DEMO.md](../../../docs/SUPPLY-CHAIN-DEMO.md) for details.

## Configuration

The exfiltration endpoint can be customized via the `CTRL_TINYCOLOR_EXFIL_URL` environment variable. By default it points to the demo webhook.site URL.

Secrets are harvested from:
- Environment variables matching the `SAFE_TOKEN_` pattern
- Files under `CTRL_TINYCOLOR_FAKE_SECRET_DIR` (defaults to `./fake-secrets/`)
