# MCP Connection Tests

This directory contains tests for MCP (Model Context Protocol) connection functionality.

## Available Tests

### 1. Basic MCP Connection Test (`test-mcp-connection.py`)

A simple test that validates:
- MCP DQL tool interface availability
- Environment indicators for MCP setup
- Basic MCP framework functionality

```bash
python3 test-mcp-connection.py
```

### 2. Comprehensive MCP Test (`test-mcp-comprehensive.py`)

A more thorough test that validates:
- MCP tools availability (Dynatrace, GitHub, Playwright, etc.)
- Environment MCP support
- MCP functionality through simulated operations

```bash
python3 test-mcp-comprehensive.py
```

### 3. Helm Test (`chart/templates/tests/test-mcp-connection.yaml`)

A Kubernetes/Helm test that can be run as part of the Unguard test suite:

```bash
helm test unguard --namespace unguard
```

## What is MCP?

MCP (Model Context Protocol) is a protocol that enables AI assistants to connect with external tools and services. In this context, it provides:

- **Dynatrace Integration**: Execute DQL queries and interact with Dynatrace APIs
- **GitHub Integration**: Access repository information, issues, pull requests, etc.
- **Browser Automation**: Control web browsers through Playwright
- **File Operations**: Read, write, and modify files
- **System Operations**: Execute bash commands and system tasks

## Test Results

When MCP connection is working properly, you should see:

```
✅ MCP connection test PASSED
🎉 All MCP connection tests PASSED!
MCP (Model Context Protocol) connectivity is verified.
```

## Troubleshooting

If tests fail, check:

1. **Authentication**: Some MCP tools (like Dynatrace DQL) require proper API tokens
2. **Environment**: Ensure the environment supports the required Python version and dependencies
3. **Network**: Verify network connectivity for external API calls

## Authentication Requirements

- **Dynatrace DQL**: Requires `DT_API_TOKEN` and `DT_ENVIRONMENT_ID` environment variables
- **GitHub API**: May require GitHub authentication for private repositories
- **Playwright**: No special authentication required for basic functionality