# Using the MCP Client Service

## Quick Start with Dynatrace

To connect to an actual Dynatrace MCP server:

1. **Obtain Dynatrace Credentials:**
   - Get your Dynatrace environment URL (e.g., `https://your-tenant.live.dynatrace.com`)
   - Create an API token with MCP access permissions
   - Note your environment ID

2. **Configure Environment Variables:**
   ```bash
   export MCP_SERVER_URL="https://your-tenant.live.dynatrace.com/api/v2/mcp"
   export MCP_API_TOKEN="dt0c01.YOUR_ACTUAL_TOKEN"
   export MCP_ENVIRONMENT_ID="your-environment-id"
   export SERVER_PORT=8090
   ```

3. **Start the Service:**
   ```bash
   cd src/mcp-client-service
   python3 run.py
   ```

4. **Test Connection:**
   ```bash
   # Check service health
   curl http://localhost:8090/health
   
   # Connect to MCP server
   curl -X POST http://localhost:8090/mcp/connect
   
   # Check connection status
   curl http://localhost:8090/mcp/status
   ```

## API Endpoints

### Health Check
```bash
GET /health
```
Returns service health and MCP connection status.

### Connect to MCP Server
```bash
POST /mcp/connect
```
Establishes connection to Dynatrace MCP server.

### Send Context Data
```bash
POST /mcp/send-context
Content-Type: application/json

{
  "service": "frontend",
  "performance": {
    "response_time": 150,
    "error_rate": 0.02
  },
  "metrics": {
    "cpu_usage": 65,
    "memory_usage": 80
  }
}
```
Sends application context to MCP server for analysis.

### Get AI Insights
```bash
GET /mcp/insights?query=application+performance
```
Retrieves AI-driven insights from Dynatrace MCP server.

### Ping MCP Server
```bash
POST /mcp/ping
```
Sends ping to maintain connection with MCP server.

### Get Connection Status
```bash
GET /mcp/status
```
Returns current MCP connection status and metrics.

## Integration Examples

### Frontend Integration
```javascript
// Send performance data to MCP server
const contextData = {
  service: 'frontend-nextjs',
  performance: {
    page_load_time: performance.timing.loadEventEnd - performance.timing.navigationStart,
    first_contentful_paint: performance.getEntriesByType('paint')[0].startTime
  }
};

await fetch('/mcp/send-context', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(contextData)
});
```

### Backend Service Integration
```python
import requests

# Send service metrics to MCP
context = {
    "service": "payment-service",
    "transactions": {
        "total": 1250,
        "successful": 1225,
        "failed": 25
    }
}

response = requests.post('http://mcp-client-service:8090/mcp/send-context', json=context)
```

## Configuration for Different Environments

### Development
```bash
export MCP_SERVER_URL="https://dev-tenant.dynatrace.com/api/v2/mcp"
export MCP_ENVIRONMENT_ID="dev-environment"
```

### Production
```bash
export MCP_SERVER_URL="https://prod-tenant.dynatrace.com/api/v2/mcp"
export MCP_ENVIRONMENT_ID="prod-environment"
```

## Troubleshooting

### Connection Issues
1. Verify API token has MCP permissions
2. Check environment ID is correct
3. Ensure MCP endpoint URL is accessible
4. Check firewall/network connectivity

### Authentication Errors
1. Regenerate API token with proper permissions
2. Verify token format (should start with `dt0c01.`)
3. Check token expiration

### Service Discovery
The MCP client service can be discovered by other services in the cluster at:
- Service name: `mcp-client-service`
- Port: `8090`
- Health endpoint: `http://mcp-client-service:8090/health`