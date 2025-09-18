# MCP Client Integration Examples

This document shows how to integrate the MCP Client Service with other services in the Unguard application.

## Frontend Integration (Next.js)

Add MCP context reporting to your frontend:

```typescript
// services/MCPService.ts
export class MCPService {
  private baseUrl = process.env.NEXT_PUBLIC_MCP_SERVICE_URL || 'http://mcp-client-service:8090';

  async sendPerformanceContext(data: any) {
    try {
      const response = await fetch(`${this.baseUrl}/mcp/send-context`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          service: 'frontend-nextjs',
          timestamp: Date.now(),
          performance: data
        })
      });
      
      return await response.json();
    } catch (error) {
      console.error('Failed to send MCP context:', error);
      return null;
    }
  }

  async getInsights(query: string) {
    try {
      const response = await fetch(`${this.baseUrl}/mcp/insights?query=${encodeURIComponent(query)}`);
      return await response.json();
    } catch (error) {
      console.error('Failed to get MCP insights:', error);
      return null;
    }
  }
}
```

## Payment Service Integration (Python)

Add MCP reporting to the payment service:

```python
# payment_service/mcp_integration.py
import requests
import logging
import os

logger = logging.getLogger(__name__)

class MCPReporter:
    def __init__(self):
        self.mcp_url = os.environ.get('MCP_SERVICE_URL', 'http://mcp-client-service:8090')
        
    def send_transaction_context(self, transaction_data):
        """Send payment transaction context to MCP"""
        try:
            context = {
                'service': 'payment-service',
                'transaction': transaction_data,
                'timestamp': int(time.time() * 1000)
            }
            
            response = requests.post(
                f'{self.mcp_url}/mcp/send-context',
                json=context,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info("Successfully sent transaction context to MCP")
                return response.json()
            else:
                logger.warning(f"MCP context send failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to send MCP context: {e}")
            
        return None

# Usage in routes.py
mcp_reporter = MCPReporter()

@bp.route('/api/payment', methods=['POST'])
def process_payment():
    # ... existing payment logic ...
    
    # Send transaction data to MCP for analysis
    transaction_context = {
        'amount': payment_data['amount'],
        'currency': payment_data['currency'],
        'status': 'success',
        'response_time': processing_time
    }
    
    mcp_reporter.send_transaction_context(transaction_context)
    
    return jsonify(result)
```

## User Auth Service Integration (Node.js)

Add MCP authentication insights:

```javascript
// utils/mcp-client.js
const axios = require('axios');

class MCPClient {
  constructor() {
    this.baseUrl = process.env.MCP_SERVICE_URL || 'http://mcp-client-service:8090';
  }

  async sendAuthContext(contextData) {
    try {
      const response = await axios.post(`${this.baseUrl}/mcp/send-context`, {
        service: 'user-auth-service',
        timestamp: Date.now(),
        ...contextData
      });
      
      console.log('MCP context sent successfully');
      return response.data;
    } catch (error) {
      console.error('Failed to send MCP context:', error.message);
      return null;
    }
  }

  async getSecurityInsights() {
    try {
      const response = await axios.get(`${this.baseUrl}/mcp/insights?query=authentication+security`);
      return response.data;
    } catch (error) {
      console.error('Failed to get MCP insights:', error.message);
      return null;
    }
  }
}

module.exports = MCPClient;

// Usage in app.js
const MCPClient = require('./utils/mcp-client');
const mcpClient = new MCPClient();

app.post('/api/auth/login', async (req, res) => {
  // ... existing auth logic ...
  
  // Send authentication context to MCP
  const authContext = {
    authentication: {
      user_id: user.id,
      login_method: 'password',
      success: loginSuccessful,
      ip_address: req.ip,
      user_agent: req.get('User-Agent')
    }
  };
  
  mcpClient.sendAuthContext(authContext);
  
  res.json(result);
});
```

## Status Service Integration (Go)

Add MCP health reporting:

```go
// mcp_client.go
package main

import (
    "bytes"
    "encoding/json"
    "fmt"
    "net/http"
    "os"
    "time"
)

type MCPClient struct {
    BaseURL string
}

type MCPContext struct {
    Service   string      `json:"service"`
    Timestamp int64       `json:"timestamp"`
    Health    interface{} `json:"health"`
}

func NewMCPClient() *MCPClient {
    baseURL := os.Getenv("MCP_SERVICE_URL")
    if baseURL == "" {
        baseURL = "http://mcp-client-service:8090"
    }
    
    return &MCPClient{
        BaseURL: baseURL,
    }
}

func (c *MCPClient) SendHealthContext(healthData interface{}) error {
    context := MCPContext{
        Service:   "status-service",
        Timestamp: time.Now().UnixMilli(),
        Health:    healthData,
    }
    
    jsonData, err := json.Marshal(context)
    if err != nil {
        return err
    }
    
    resp, err := http.Post(
        c.BaseURL+"/mcp/send-context",
        "application/json",
        bytes.NewBuffer(jsonData),
    )
    
    if err != nil {
        return err
    }
    defer resp.Body.Close()
    
    if resp.StatusCode != http.StatusOK {
        return fmt.Errorf("MCP request failed with status: %d", resp.StatusCode)
    }
    
    return nil
}

// Usage in main.go
func healthHandler(w http.ResponseWriter, r *http.Request) {
    // ... existing health check logic ...
    
    // Send health data to MCP
    healthData := map[string]interface{}{
        "deployments_healthy": healthyDeployments,
        "total_deployments":   totalDeployments,
        "cluster_status":      clusterStatus,
    }
    
    mcpClient := NewMCPClient()
    if err := mcpClient.SendHealthContext(healthData); err != nil {
        log.Printf("Failed to send health context to MCP: %v", err)
    }
    
    json.NewEncoder(w).Encode(healthResponse)
}
```

## Environment Configuration

Add to your Kubernetes deployments:

```yaml
# Add to existing deployment manifests
env:
- name: MCP_SERVICE_URL
  value: "http://mcp-client-service:8090"
```

## Monitoring and Alerting

Set up monitoring for MCP connectivity:

```bash
# Health check script
#!/bin/bash
MCP_STATUS=$(curl -s http://mcp-client-service:8090/mcp/status | jq -r '.connected')

if [ "$MCP_STATUS" != "true" ]; then
    echo "MCP client is not connected to Dynatrace"
    exit 1
fi

echo "MCP client is healthy and connected"
```

## Batch Context Sending

For services that need to send bulk data:

```python
# Batch MCP context sender
class BatchMCPReporter:
    def __init__(self, batch_size=10, flush_interval=60):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.context_queue = []
        self.last_flush = time.time()
        
    def add_context(self, context_data):
        self.context_queue.append(context_data)
        
        if (len(self.context_queue) >= self.batch_size or 
            time.time() - self.last_flush >= self.flush_interval):
            self.flush()
    
    def flush(self):
        if not self.context_queue:
            return
            
        batch_context = {
            'service': 'batch-reporter',
            'batch_size': len(self.context_queue),
            'contexts': self.context_queue
        }
        
        # Send to MCP
        try:
            response = requests.post(
                'http://mcp-client-service:8090/mcp/send-context',
                json=batch_context
            )
            if response.status_code == 200:
                self.context_queue.clear()
                self.last_flush = time.time()
        except Exception as e:
            logging.error(f"Failed to flush MCP contexts: {e}")
```