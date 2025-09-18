# MCP Connection Test

This service tests the **Microservice Communication Protocol (MCP)** connections between all Unguard services.

## Purpose

The MCP Connection Test validates that all microservices in the Unguard application can be reached and are responding correctly. This is essential for ensuring proper service-to-service communication in the microservices architecture.

## What it Tests

The test checks connectivity to the following services:

1. **Frontend (Next.js)** - `/ui/api/healthz` endpoint
2. **Status Service (Go)** - `/status-service/deployments/health` endpoint  
3. **Profile Service (Java)** - `/healthz` endpoint
4. **Microblog Service (Java)** - `/timeline` endpoint (basic connectivity)
5. **User Auth Service (Node.js)** - `/user-auth-service/register` endpoint
6. **Membership Service (.NET)** - Basic connectivity test
7. **Like Service (PHP)** - Basic connectivity test
8. **Payment Service (Python)** - Basic connectivity test
9. **Proxy Service (Java)** - Basic connectivity test
10. **Ad Service (.NET)** - `/ad-service/ad` endpoint

## Environment Variables

The test uses the same environment variables as the main application:

- `FRONTEND_ADDRESS` (default: `unguard-frontend-nextjs`)
- `STATUS_SERVICE_ADDRESS` (default: `unguard-status-service`)
- `PROFILE_SERVICE_ADDRESS` (default: `unguard-profile-service`)
- `MICROBLOG_SERVICE_ADDRESS` (default: `unguard-microblog-service`)
- `USER_AUTH_SERVICE_ADDRESS` (default: `unguard-user-auth-service`)
- `MEMBERSHIP_SERVICE_ADDRESS` (default: `unguard-membership-service`)
- `LIKE_SERVICE_ADDRESS` (default: `unguard-like-service`)
- `PAYMENT_SERVICE_ADDRESS` (default: `unguard-payment-service`)
- `PROXY_SERVICE_ADDRESS` (default: `unguard-proxy-service`)
- `AD_SERVICE_ADDRESS` (default: `unguard-ad-service`)

Plus the base path variables:
- `STATUS_SERVICE_BASE_PATH` (default: `/status-service`)
- `MEMBERSHIP_SERVICE_BASE_PATH` (default: `/membership-service`)
- `LIKE_SERVICE_BASE_PATH` (default: `/like-service`)
- `AD_SERVICE_BASE_PATH` (default: `/ad-service`)

## Running the Test

### Standalone
```bash
npm install
npm test
```

### Docker
```bash
docker build -t mcp-connection-test .
docker run --rm mcp-connection-test
```

### Kubernetes/Helm Test
The test is integrated into the Helm chart as a test pod that runs after deployment.

```bash
helm test unguard --namespace unguard
```

## Test Results

The test provides:
- ✅ **PASS**: Service is reachable and responding as expected
- ❌ **FAIL**: Service is unreachable or responding with unexpected status
- ❓ **UNKNOWN**: Test encountered an unexpected error

## Exit Codes

- `0`: All tests passed
- `1`: One or more tests failed

## Implementation Notes

- Each service test has a 10-second timeout
- Tests run in parallel for faster execution
- Different services expect different HTTP status codes based on their endpoint behavior
- The test is designed to be resilient and provide meaningful feedback even when some services are unavailable