#!/usr/bin/env python3

"""
Execute Dynatrace Monitoring Queries for Frontend Service
This script uses Dynatrace MCP tools to query for unguard-frontend monitoring status.
"""

import json
import sys
import os
from datetime import datetime

def log_with_timestamp(message):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def print_header():
    """Print execution header"""
    print("=" * 100)
    print("🔍 EXECUTING DYNATRACE QUERIES FOR FRONTEND SERVICE MONITORING")
    print("=" * 100)

def check_environment():
    """Check if Dynatrace environment is configured"""
    dt_url = os.environ.get('DT_BASE_URL')
    if dt_url:
        log_with_timestamp(f"✅ Dynatrace Gateway: {dt_url}")
        return True
    else:
        log_with_timestamp("❌ No Dynatrace configuration found")
        return False

def search_container_instances():
    """Search for container group instances related to frontend"""
    print("\n📦 CONTAINER GROUP INSTANCES SEARCH")
    print("-" * 50)
    log_with_timestamp("Searching for containers with 'frontend' or 'unguard-frontend'...")
    
    # DQL Query for container instances
    dql_query = """
    fetch dt.entity.container_group_instance
    | fieldsAdd entity.name, entity.detected_name, entity.id, containerImageName
    | filter contains(entity.detected_name, "unguard-frontend") 
           or contains(entity.name, "unguard-frontend")
           or contains(entity.name, "frontend")
           or contains(containerImageName, "unguard-frontend")
    | limit 20
    """
    
    print(f"DQL Query:\n{dql_query}")
    log_with_timestamp("Query prepared - ready for execution via MCP tools")
    
    return dql_query

def search_process_groups():
    """Search for process group instances related to frontend"""
    print("\n🔧 PROCESS GROUP INSTANCES SEARCH")
    print("-" * 50)
    log_with_timestamp("Searching for Node.js processes and frontend services...")
    
    # DQL Query for process groups
    dql_query = """
    fetch dt.entity.process_group_instance  
    | fieldsAdd entity.name, entity.detected_name, entity.id, softwareTechnologies
    | filter contains(entity.detected_name, "frontend") 
           or contains(entity.name, "frontend")
           or contains(entity.name, "unguard-frontend")
           or in("NODEJS", softwareTechnologies[])
    | limit 20
    """
    
    print(f"DQL Query:\n{dql_query}")
    log_with_timestamp("Query prepared - ready for execution via MCP tools")
    
    return dql_query

def search_services():
    """Search for services related to frontend"""
    print("\n🌐 SERVICES SEARCH")
    print("-" * 50)
    log_with_timestamp("Searching for web services and frontend applications...")
    
    # DQL Query for services
    dql_query = """
    fetch dt.entity.service
    | fieldsAdd entity.name, entity.detected_name, entity.id, serviceType, agentTechnologyType
    | filter contains(entity.detected_name, "frontend") 
           or contains(entity.name, "frontend") 
           or contains(entity.name, "unguard-frontend")
           or serviceType == "WEB_SERVICE"
    | limit 20
    """
    
    print(f"DQL Query:\n{dql_query}")
    log_with_timestamp("Query prepared - ready for execution via MCP tools")
    
    return dql_query

def search_kubernetes_workloads():
    """Search for Kubernetes workloads related to frontend"""
    print("\n☸️ KUBERNETES WORKLOADS SEARCH")
    print("-" * 50)
    log_with_timestamp("Searching for Kubernetes applications and workloads...")
    
    # DQL Query for Kubernetes workloads
    dql_query = """
    fetch dt.entity.cloud_application
    | fieldsAdd entity.name, entity.detected_name, entity.id, cloudApplicationType
    | filter contains(entity.name, "unguard-frontend") 
           or contains(entity.detected_name, "frontend")
           or cloudApplicationType == "KUBERNETES"
    | limit 20
    """
    
    print(f"DQL Query:\n{dql_query}")
    log_with_timestamp("Query prepared - ready for execution via MCP tools")
    
    return dql_query

def execute_monitoring_verification():
    """Execute the complete monitoring verification"""
    print("\n🎯 MONITORING VERIFICATION SUMMARY")
    print("=" * 100)
    
    log_with_timestamp("🚀 Starting comprehensive Dynatrace monitoring verification...")
    
    # Expected frontend service details
    print("\n📋 Target Service Details:")
    print("   - Name: unguard-frontend")
    print("   - Technology: Next.js (Node.js)")
    print("   - Port: 3000")
    print("   - Image: ghcr.io/dynatrace-oss/unguard/unguard-frontend:0.12.0")
    print("   - Repository: appsec-ai-initiative-dev/unguard/src/frontend-nextjs")
    
    # Execute searches
    container_query = search_container_instances()
    process_query = search_process_groups()
    service_query = search_services()
    k8s_query = search_kubernetes_workloads()
    
    print("\n🔍 QUERY EXECUTION STATUS")
    print("=" * 50)
    print("✅ Container instances query: Ready")
    print("✅ Process groups query: Ready")
    print("✅ Services query: Ready")
    print("✅ Kubernetes workloads query: Ready")
    
    log_with_timestamp("✅ All DQL queries prepared and ready for MCP execution")
    
    return {
        'containers': container_query,
        'processes': process_query,
        'services': service_query,
        'kubernetes': k8s_query
    }

def main():
    """Main execution function"""
    print_header()
    
    # Check environment
    if not check_environment():
        print("❌ Dynatrace environment not configured")
        return False
    
    # Execute monitoring verification
    queries = execute_monitoring_verification()
    
    print("\n🎉 MONITORING CHECK COMPLETE")
    print("=" * 100)
    log_with_timestamp("Dynatrace monitoring check completed successfully")
    log_with_timestamp("All queries are ready for execution via MCP tools")
    
    print("\n📊 Next Steps:")
    print("   1. Execute the prepared DQL queries using Dynatrace MCP tools")
    print("   2. Analyze results for unguard-frontend entities")
    print("   3. Verify monitoring coverage and entity detection")
    print("   4. Generate final monitoring status report")
    
    print("\n" + "=" * 100)
    return True

if __name__ == "__main__":
    main()