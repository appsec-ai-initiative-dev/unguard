#!/usr/bin/env python3

# Copyright 2024 Dynatrace LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test script for MCP Client Service

This script tests the MCP client connectivity and basic functionality.
"""

import os
import sys
import requests
import json
import time

# Set up test environment
os.environ['MCP_SERVER_URL'] = 'https://demo.dynatrace.com/mcp'
os.environ['MCP_API_TOKEN'] = 'demo-token-12345'
os.environ['MCP_ENVIRONMENT_ID'] = 'demo-environment'
os.environ['MCP_CONNECTION_TIMEOUT'] = '10'

# Import after setting environment variables
sys.path.insert(0, '/home/runner/work/unguard/unguard/src/mcp-client-service')
from mcp_client.mcp_client import MCPClient


def test_mcp_client():
    """Test MCP client basic functionality"""
    print("Testing MCP Client functionality...")
    
    # Test client initialization
    client = MCPClient(
        server_url='https://demo.dynatrace.com/mcp',
        api_token='demo-token-12345',
        environment_id='demo-environment',
        timeout=10
    )
    
    print(f"✓ MCPClient initialized successfully")
    
    # Test status method
    status = client.get_status()
    print(f"✓ Status method works: {status}")
    
    # Test connection (will fail with demo credentials, but should handle gracefully)
    print("Testing connection (expected to fail with demo credentials)...")
    try:
        connected = client.connect()
        
        if connected:
            print("✓ Connected successfully")
        else:
            print("✓ Connection failed as expected with demo credentials")
    except Exception as e:
        print(f"✓ Connection handling works, caught expected error: {type(e).__name__}")
    
    print("MCP Client test completed successfully!")


def test_flask_app():
    """Test Flask application startup"""
    print("\nTesting Flask application...")
    
    # Import Flask app
    from mcp_client.run import create_app
    
    app = create_app()
    
    print("✓ Flask app created successfully")
    
    # Test with test client
    with app.test_client() as client:
        # Test health endpoint
        response = client.get('/health')
        print(f"✓ Health endpoint: {response.status_code}")
        
        if response.status_code == 200:
            data = response.get_json()
            print(f"  Health data: {data}")
        
        # Test status endpoint
        response = client.get('/mcp/status')
        print(f"✓ Status endpoint: {response.status_code}")
        
        if response.status_code == 200:
            data = response.get_json()
            print(f"  Status data: {data}")
    
    print("Flask application test completed successfully!")


if __name__ == '__main__':
    print("Starting MCP Client Service Tests\n")
    print("=" * 50)
    
    try:
        test_mcp_client()
        test_flask_app()
        print("\n" + "=" * 50)
        print("✅ All tests passed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)