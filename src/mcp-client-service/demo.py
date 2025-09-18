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
MCP Client Service Demonstration

This script demonstrates the MCP client service capabilities with mock data.
"""

import requests
import json
import time
import threading
import subprocess
import signal
import sys
import os

class MCPDemo:
    def __init__(self, mcp_url="http://localhost:8090"):
        self.mcp_url = mcp_url
        self.server_process = None
        
    def start_mcp_service(self):
        """Start the MCP service in background"""
        print("🚀 Starting MCP Client Service...")
        
        env = os.environ.copy()
        env.update({
            'SERVER_PORT': '8090',
            'MCP_SERVER_URL': 'https://demo.dynatrace.com/mcp',
            'MCP_API_TOKEN': 'demo-token-12345',
            'MCP_ENVIRONMENT_ID': 'demo-environment'
        })
        
        self.server_process = subprocess.Popen(
            ['python3', 'run.py'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for service to start
        for i in range(10):
            try:
                response = requests.get(f"{self.mcp_url}/health", timeout=1)
                if response.status_code == 200:
                    print("✅ MCP Service started successfully")
                    return True
            except:
                time.sleep(1)
                
        print("❌ Failed to start MCP service")
        return False
    
    def stop_mcp_service(self):
        """Stop the MCP service"""
        if self.server_process:
            print("🛑 Stopping MCP Service...")
            self.server_process.terminate()
            self.server_process.wait()
            print("✅ MCP Service stopped")
    
    def check_health(self):
        """Check service health"""
        print("\n📊 Checking MCP Service Health...")
        try:
            response = requests.get(f"{self.mcp_url}/health")
            data = response.json()
            
            print(f"   Service Status: {data['status']}")
            print(f"   MCP Connected: {data['mcp_connection']['connected']}")
            print(f"   Server URL: {data['mcp_connection']['server_url']}")
            print(f"   Environment: {data['mcp_connection']['environment_id']}")
            
            return True
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
    
    def test_connection(self):
        """Test MCP server connection"""
        print("\n🔌 Testing MCP Connection...")
        try:
            response = requests.post(f"{self.mcp_url}/mcp/connect")
            data = response.json()
            
            print(f"   Connection Status: {data['status']}")
            print(f"   Message: {data['message']}")
            
            return data['status'] == 'connected'
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False
    
    def send_sample_contexts(self):
        """Send sample application contexts"""
        print("\n📤 Sending Sample Application Contexts...")
        
        contexts = [
            {
                "service": "frontend-nextjs",
                "performance": {
                    "page_load_time": 1200,
                    "first_contentful_paint": 800,
                    "largest_contentful_paint": 1500
                },
                "user_metrics": {
                    "active_users": 245,
                    "bounce_rate": 0.25
                }
            },
            {
                "service": "payment-service", 
                "transactions": {
                    "total": 1250,
                    "successful": 1225,
                    "failed": 25,
                    "avg_response_time": 180
                },
                "errors": {
                    "timeout_errors": 15,
                    "validation_errors": 8,
                    "gateway_errors": 2
                }
            },
            {
                "service": "user-auth-service",
                "authentication": {
                    "login_attempts": 2840,
                    "successful_logins": 2765,
                    "failed_logins": 75,
                    "security_events": 12
                }
            }
        ]
        
        for i, context in enumerate(contexts):
            try:
                response = requests.post(
                    f"{self.mcp_url}/mcp/send-context",
                    json=context,
                    timeout=5
                )
                
                if response.status_code == 200:
                    print(f"   ✅ Context {i+1} sent successfully: {context['service']}")
                else:
                    print(f"   ⚠️  Context {i+1} failed: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Context {i+1} error: {e}")
            
            time.sleep(0.5)
    
    def get_insights(self):
        """Get AI insights from MCP"""
        print("\n🧠 Getting AI Insights...")
        
        queries = [
            "application performance",
            "security threats",
            "user experience",
            "error analysis"
        ]
        
        for query in queries:
            try:
                response = requests.get(
                    f"{self.mcp_url}/mcp/insights",
                    params={"query": query},
                    timeout=5
                )
                
                if response.status_code == 200:
                    print(f"   ✅ Insights for '{query}': Available")
                else:
                    print(f"   ⚠️  Insights for '{query}': Failed ({response.status_code})")
                    
            except Exception as e:
                print(f"   ❌ Insights for '{query}': Error - {e}")
            
            time.sleep(0.3)
    
    def ping_service(self):
        """Test ping functionality"""
        print("\n🏓 Testing MCP Ping...")
        try:
            response = requests.post(f"{self.mcp_url}/mcp/ping")
            data = response.json()
            
            print(f"   Ping Status: {data['status']}")
            print(f"   Message: {data['message']}")
            
        except Exception as e:
            print(f"❌ Ping failed: {e}")
    
    def show_status(self):
        """Show detailed MCP status"""
        print("\n📈 MCP Connection Status...")
        try:
            response = requests.get(f"{self.mcp_url}/mcp/status")
            data = response.json()
            
            print(f"   Connected: {data['connected']}")
            print(f"   Server URL: {data['server_url']}")
            print(f"   Environment ID: {data['environment_id']}")
            print(f"   Last Ping: {data['last_ping']}")
            print(f"   Uptime: {data['uptime']:.2f} seconds")
            
        except Exception as e:
            print(f"❌ Status check failed: {e}")
    
    def run_demo(self):
        """Run the complete demonstration"""
        print("🎯 MCP Client Service Demonstration")
        print("=" * 50)
        
        # Start service
        if not self.start_mcp_service():
            return False
        
        try:
            # Wait a moment for service to fully initialize
            time.sleep(2)
            
            # Run demo steps
            self.check_health()
            self.test_connection()
            self.send_sample_contexts()
            self.get_insights()
            self.ping_service()
            self.show_status()
            
            print("\n" + "=" * 50)
            print("✅ MCP Client Service Demonstration Complete!")
            print("\nThe MCP client service is now ready to connect to")
            print("actual Dynatrace MCP servers with proper credentials.")
            
            print("\n📝 Next Steps:")
            print("1. Configure real Dynatrace credentials")
            print("2. Deploy to Kubernetes cluster")
            print("3. Integrate with other services")
            print("4. Monitor MCP connectivity and insights")
            
        finally:
            # Always stop the service
            time.sleep(2)
            self.stop_mcp_service()
        
        return True


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print('\n\n🛑 Demo interrupted by user')
    sys.exit(0)


if __name__ == '__main__':
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Change to the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Run the demo
    demo = MCPDemo()
    success = demo.run_demo()
    
    if success:
        print("\n🎉 Demo completed successfully!")
    else:
        print("\n💥 Demo failed!")
        sys.exit(1)