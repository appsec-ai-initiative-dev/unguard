# @ctrl/tinycolor (simulation)

This locally vendored package emulates the behaviour of the compromised @ctrl/tinycolor release referenced in the StepSecurity report. It ships a benign TruffleHog binary, emits console beacons, and gathers **fake** secrets so Dynatrace can detect the supply-chain indicators without touching production data.

## Runtime behaviour

- **Postinstall** (postinstall.js) sets the bundled 	rufflehog binary executable when dependencies are installed on Unix-like systems.
- **Beaconing**: Whenever the module is imported, it schedules background beacons and launches the fake TruffleHog scan. All telemetry is logged to the console.
- **Secret harvesting**: The module looks for demo secrets in two places:
  - environment variables whose name or value contains SAFE_TOKEN_
  - files under process.env.CTRL_TINYCOLOR_FAKE_SECRET_DIR (defaults to <process.cwd()>/fake-secrets when not set) that contain the SAFE_TOKEN_ pattern
- **Simulated exfiltration**: After every harvest the module sends the findings to an HTTP endpoint (CTRL_TINYCOLOR_EXFIL_URL, defaults to https://collect.ctrl-tinycolor.example/exfil). The payload contains the discovered SAFE_TOKEN_* strings, the source of the scan (bundled, npx, etc.), hostname, and timestamp so Dynatrace can flag the outbound request.

Any matches are logged, shipped to the simulated exfil endpoint, and included in the beacon payload so downstream monitoring tools can visualise the exposure.

## Configuration knobs

- CTRL_TINYCOLOR_DISABLE_TRUFFLEHOG=1 ? skips spawning the bundled binary entirely.
- CTRL_TINYCOLOR_TRUFFLEHOG_COMMAND ? overrides the command that is executed (e.g. point to a wrapper script).
- CTRL_TINYCOLOR_TRUFFLEHOG_USE_NPX=1 ? runs 
px trufflehog ? instead of the bundled binary.
- CTRL_TINYCOLOR_FAKE_SECRET_DIR ? tells the library where to look for demo secret files. The Jenkins compose stack sets this automatically so the simulation finds the mounted fake credentials.
- CTRL_TINYCOLOR_EXFIL_URL ? endpoint that receives the JSON payload of harvested secrets; defaults to the canned demo URL.
- CTRL_TINYCOLOR_DISABLE_EXFIL=1 ? turns off the simulated exfiltration while leaving the console logging/beacons intact.

All harvested data is non-sensitive and exists purely to generate Indicators of Compromise for the demo environment.
