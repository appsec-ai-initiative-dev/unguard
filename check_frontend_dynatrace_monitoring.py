#!/usr/bin/env python3

"""
Frontend Service Dynatrace Monitoring Report Generator
This script queries Dynatrace via MCP to check if the unguard-frontend service is monitored.
"""

import json
import sys
import os
import requests
from datetime import datetime

def log_step(message):
    """Log a step with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def print_header():
    """Print the report header"""
    print("=" * 100)
    print("🔍 DYNATRACE FRONTEND SERVICE MONITORING REPORT")
    print("=" * 100)
    
def print_service_details():
    """Print expected service details"""
    print("\n📋 Expected Frontend Service Details:")
    print("   - Service Name: unguard-frontend")
    print("   - Technology: Next.js (Node.js)")
    print("   - Container Port: 3000")
    print("   - Deployment: Kubernetes via Helm chart") 
    print("   - Image: ghcr.io/dynatrace-oss/unguard/unguard-frontend:0.12.0")
    print("   - Repository Path: appsec-ai-initiative-dev/unguard/src/frontend-nextjs")

def check_dynatrace_connectivity():
    """Check Dynatrace MCP connectivity"""
    print("\n🔗 Dynatrace MCP Connectivity Check:")
    
    # Check MCP server health
    try:
        response = requests.get("http://localhost:2301/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ MCP Server: Healthy and accessible")
        else:
            print(f"   ❌ MCP Server: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ MCP Server: Connection failed - {e}")
        return False
    
    # Check Dynatrace gateway configuration
    dt_base_url = os.environ.get('DT_BASE_URL')
    if dt_base_url:
        print(f"   ✅ Dynatrace Gateway: {dt_base_url}")
    else:
        print("   ❌ Dynatrace Gateway: Not configured")
        return False
    
    return True

def generate_dql_queries():
    """Generate DQL queries for frontend monitoring check"""
    print("\n📊 DQL Queries for Frontend Service Detection:")
    
    queries = {
        "container_instances": """
fetch dt.entity.container_group_instance
| fieldsAdd entity.name, entity.detected_name, entity.id, containerImageName
| filter contains(entity.detected_name, "unguard-frontend") 
       or contains(entity.name, "unguard-frontend")
       or contains(entity.name, "frontend")
       or contains(containerImageName, "unguard-frontend")
| limit 20""",
        
        "process_groups": """
fetch dt.entity.process_group_instance  
| fieldsAdd entity.name, entity.detected_name, entity.id, softwareTechnologies
| filter contains(entity.detected_name, "frontend") 
       or contains(entity.name, "frontend")
       or contains(entity.name, "unguard-frontend")
       or in("NODEJS", softwareTechnologies[])
| limit 20""",
        
        "services": """
fetch dt.entity.service
| fieldsAdd entity.name, entity.detected_name, entity.id, serviceType, agentTechnologyType
| filter contains(entity.detected_name, "frontend") 
       or contains(entity.name, "frontend") 
       or contains(entity.name, "unguard-frontend")
       or serviceType == "WEB_SERVICE"
| limit 20""",
        
        "kubernetes_workloads": """
fetch dt.entity.cloud_application
| fieldsAdd entity.name, entity.detected_name, entity.id, cloudApplicationType
| filter contains(entity.name, "unguard-frontend") 
       or contains(entity.detected_name, "frontend")
       or cloudApplicationType == "KUBERNETES"
| limit 20"""
    }
    
    for query_name, query in queries.items():
        print(f"\n   🔍 {query_name.replace('_', ' ').title()}:")
        print("   " + "-" * 60)
        for line in query.strip().split('\n'):
            print(f"   {line}")
    
    return queries

def print_monitoring_status():
    """Print monitoring status summary"""
    print("\n🎯 Monitoring Verification Strategy:")
    print("   1. ✅ MCP Server connectivity established")
    print("   2. ✅ Dynatrace Gateway configured") 
    print("   3. 🔄 Ready to execute DQL queries via MCP tools")
    print("   4. 🔄 Search for container group instances")
    print("   5. 🔄 Check process group instances") 
    print("   6. 🔄 Identify related services")
    print("   7. 🔄 Verify Kubernetes workload monitoring")

def main():
    """Main function to generate monitoring report"""
    
    print_header()
    log_step("🚀 Generating frontend service monitoring report...")
    
    print_service_details()
    
    # Check connectivity
    if not check_dynatrace_connectivity():
        print("\n❌ Cannot proceed - Dynatrace connectivity issues")
        return False
    
    # Generate queries
    queries = generate_dql_queries()
    
    # Print monitoring status
    print_monitoring_status()
    
    print("\n🔧 Next Steps:")
    print("   - Execute DQL queries using Dynatrace MCP tools")
    print("   - Analyze results for unguard-frontend entities")
    print("   - Verify Node.js process detection")
    print("   - Confirm container image matches expected repository")
    
    log_step("✅ Monitoring report generated - ready for DQL execution")
    print("\n" + "=" * 100)
    
    return True

if __name__ == "__main__":
    main()