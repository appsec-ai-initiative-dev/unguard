# Verdaccio Setup for Tinycolor Simulation

This folder contains a minimal Verdaccio configuration that lets the simulated
`@ctrl/tinycolor` package masquerade as version `4.1.1`. When Dependabot inspects
`package.json`, it will now see a vulnerable release even though the bits come
from `src/frontend-nextjs/vendor/ctrl-tinycolor-sim`.

## 1. Start Verdaccio

```bash
npx verdaccio --config ops/verdaccio/config.yaml
```

The config listens on `http://127.0.0.1:4873`, proxies everything else to the
public npm registry, and reserves local storage for `@ctrl/tinycolor`.

## 2. Create a registry user (once)

```bash
npm adduser --registry http://127.0.0.1:4873
```

## 3. Publish the simulated package as 4.1.1

```bash
node ops/verdaccio/publish-tinycolor.js
```

The helper script:
- copies `vendor/ctrl-tinycolor-sim` to a temp directory,
- rewrites the version to `4.1.1` and clears the `private` flag,
- publishes it to Verdaccio (skips the publish if that version already exists).

Override the defaults if needed:

```bash
VERDACCIO_REGISTRY=http://127.0.0.1:4873 \
VERDACCIO_TINYCOLOR_VERSION=4.1.1 \
node ops/verdaccio/publish-tinycolor.js
```

## 4. Point installs at Verdaccio

Add or extend an `.npmrc` so the `@ctrl` scope resolves through Verdaccio while
everything else continues to use npmjs:

```
@ctrl:registry=http://127.0.0.1:4873
registry=https://registry.npmjs.org/
```

## 5. Update the app dependency

Set `src/frontend-nextjs/package.json` to reference `"@ctrl/tinycolor": "4.1.1"`
so Dependabot and npm both consume the Verdaccio-hosted build. After editing,
reinstall dependencies (`npm install`) and commit the lockfile.

## GitHub Actions automation

The workflow `.github/workflows/src-ghcr-build.yml` now launches Verdaccio,
creates a CI user, seeds `@ctrl/tinycolor@4.1.1`, and builds Docker images using
`--network host` so `127.0.0.1:4873` is reachable during `npm ci`.

With these steps in place Dependabot will see the vulnerable `4.1.1` release,
trigger its advisory, and Dynatrace can ingest the alert for the PoC.
