# MCP Client Service

This service provides connectivity to Dynatrace MCP (Model Context Protocol) servers for enhanced observability and AI-driven insights.

## Features

- Connect to Dynatrace MCP servers
- Send telemetry data and context information
- Receive AI-driven recommendations and insights
- Health monitoring and connection status

## Environment Variables

| Name                 | Example Value                           | Description                                    |
|----------------------|----------------------------------------|------------------------------------------------|
| SERVER_PORT          | 8090                                   | The port that the server will run on          |
| MCP_SERVER_URL       | https://your-tenant.dynatrace.com/mcp | Dynatrace MCP server endpoint                  |
| MCP_API_TOKEN        | dt0c01.sample.token                    | Dynatrace API token for MCP access            |
| MCP_ENVIRONMENT_ID   | your-environment-id                    | Dynatrace environment identifier               |
| MCP_CONNECTION_TIMEOUT | 30                                   | Connection timeout in seconds                  |

## Endpoints

- `GET /health` - Health check and MCP connection status
- `POST /mcp/send-context` - Send application context to MCP server
- `GET /mcp/insights` - Retrieve AI insights from MCP server
- `GET /mcp/status` - Get MCP connection status and metrics

## Running

```bash
export SERVER_PORT=8090
export MCP_SERVER_URL="https://your-tenant.dynatrace.com/mcp"
export MCP_API_TOKEN="your-api-token"
export MCP_ENVIRONMENT_ID="your-environment"

python run.py
```

## License

Copyright 2024 Dynatrace LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.