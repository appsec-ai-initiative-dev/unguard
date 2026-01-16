#!/bin/bash

DT_ENV_URL="https://pia1134d.dev.apps.dynatracelabs.com"
DT_API_TOKEN="${COPILOT2_MCP_DT_API_TOKEN}"

echo "=== Testing Grail Query API ==="
echo ""

# Test 1: Simple query via Grail
DQL_QUERY='fetch security.events, from:now() - 30d | limit 5'

echo "Query: $DQL_QUERY"
echo ""

# Try the platform storage endpoint
curl -X POST "${DT_ENV_URL}/platform/storage/query/v1/query:execute" \
  -H "Authorization: Api-Token ${DT_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"$DQL_QUERY\"}" \
  2>&1 | tee grail_test.json | jq '.'

echo ""
echo "=== End Test ==="
