# Jenkins CI Demo Environment

This folder spins up a single-node Jenkins instance that mimics a CI server holding sensitive material. It bakes in a handful of **benign** demo secrets so the simulated supply-chain payload can discover them just like the real worm.

## Contents

- Dockerfile ? builds on top of the official jenkins/jenkins:lts-jdk17 image, adds fake secrets under /opt/demo-fake-secrets, and exports several environment variables that match the SAFE_TOKEN_* pattern.
- ake-secrets/ ? files copied into the image. They live under /opt/demo-fake-secrets and /var/jenkins_home/demo-fake-secrets inside the container so both pipelines and the TruffleHog simulation can read them.
- docker-compose.yml ? starts the Jenkins controller, exposes ports 8080/50000, and places extra environment variables into the runtime environment (SAFE_TOKEN_*, CTRL_TINYCOLOR_FAKE_SECRET_DIR, and CTRL_TINYCOLOR_EXFIL_URL). The exfil URL is set to https://demo-exfil.unguard.local/collect so the simulated payload produces a predictable outbound request for Dynatrace.

## Usage

1. Build and launch Jenkins:

   `ash
   cd ops/jenkins
   docker compose up --build
   `

   The first startup may take ~2?3 minutes while Jenkins initializes the home directory. Once healthy the UI is available at <http://localhost:8080> with the default admin account (dmin/dmin since the setup wizard is disabled).

2. Verify demo secrets:

   `ash
   docker compose exec jenkins ls /var/jenkins_home/demo-fake-secrets
   docker compose exec jenkins printenv | grep SAFE_TOKEN
   `

   You should see the files copied from ake-secrets/ and several environment variables containing SAFE_TOKEN_ values.

3. Wire into the demo pipeline. When you run the Next.js build or tests inside this Jenkins agent, the simulated @ctrl/tinycolor package will automatically:
   - set the bundled 	rufflehog binary executable (postinstall step),
   - spawn the scanner during runtime,
   - harvest any SAFE_TOKEN_* secrets from environment variables or /var/jenkins_home/demo-fake-secrets, and
   - POST the findings to the configured exfil URL (CTRL_TINYCOLOR_EXFIL_URL).

   The HTTP request body includes the hostname, scan source, and the harvested tokens, which makes it easy to build Dynatrace detections around the outbound call.

4. Tearing down:

   `ash
   docker compose down
   `

   The named volume jenkins_home persists across restarts so the fake secrets survive container recreation. Remove it with docker volume rm ops_jenkins_jenkins_home if you need a clean slate.

> **Note**: All tokens in this setup are intentionally fake. They exist solely to generate telemetry for the demo and must never be used outside of the lab environment.
