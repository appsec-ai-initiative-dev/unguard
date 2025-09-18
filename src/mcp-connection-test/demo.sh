#!/bin/bash

# MCP Connection Test Demo Script
# This script demonstrates how to run the MCP connection test in different scenarios

set -e

echo "🧪 MCP Connection Test Demo"
echo "=========================="
echo

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed"
    exit 1
fi

echo "1. Testing Docker image build..."
cd /tmp
if docker build -t mcp-test-demo https://github.com/AppSec-AI-Initiative-Dev/unguard.git#main:src/mcp-connection-test > /dev/null 2>&1; then
    echo "✅ Docker image built successfully"
else
    echo "❌ Docker image build failed"
    exit 1
fi

echo

echo "2. Running MCP connection test (expecting failures since services aren't running)..."
echo "   This demonstrates the test output format:"
echo

# Run the test and capture output
if timeout 30 docker run --rm mcp-test-demo 2>&1; then
    echo "🎉 Test completed (unexpectedly passed - services might be running)"
else
    echo "✅ Test completed as expected (services not available in demo environment)"
fi

echo
echo "3. Example successful test output would look like:"
echo "   🚀 Starting MCP (Microservice Communication Protocol) Connection Tests"
echo "   Testing 10 services..."
echo "   ✅ frontend-nextjs: Connected (200) - 45ms"
echo "   ✅ status-service: Connected (200) - 32ms"
echo "   ✅ profile-service: Connected (200) - 28ms"
echo "   ... (and so on for all services)"
echo "   📊 MCP CONNECTION TEST RESULTS"
echo "   Total Services: 10"
echo "   ✅ Passed: 10"
echo "   ❌ Failed: 0"
echo "   🎉 All MCP connections are healthy!"

echo
echo "4. In a Kubernetes environment, run with:"
echo "   helm test unguard --namespace unguard"

echo
echo "Demo completed! The MCP connection test is ready for deployment."