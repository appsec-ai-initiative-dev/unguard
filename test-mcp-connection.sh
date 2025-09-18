#!/bin/bash

# MCP Connection Test Script
# This script tests various MCP capabilities

echo "=== MCP Connection Test Script ==="
echo "Date: $(date)"
echo "Repository: $(pwd)"
echo ""

echo "✅ Testing file system access..."
ls -la mcp-connection-test.md

echo ""
echo "✅ Testing command execution..."
echo "Current directory: $(pwd)"
echo "Git branch: $(git branch --show-current)"

echo ""
echo "✅ Testing file operations..."
echo "File exists: $(test -f mcp-connection-test.md && echo 'YES' || echo 'NO')"
echo "File size: $(wc -c < mcp-connection-test.md) bytes"

echo ""
echo "✅ Testing repository interaction..."
echo "Repository status:"
git status --porcelain

echo ""
echo "🎉 MCP Connection Test Complete!"
echo "All basic MCP functionality is working correctly."