#!/usr/bin/env python3
"""
Script to query Dynatrace for top vulnerabilities.
This script fetches the top 5 OPEN vulnerabilities from Dynatrace Runtime Vulnerability Analytics (RVA).
"""

import os
import sys
import json
import requests
from typing import List, Dict, Any


def get_dynatrace_config() -> tuple:
    """
    Get Dynatrace configuration from environment variables.
    
    Returns:
        tuple: (dt_url, dt_token)
    
    Raises:
        ValueError: If required environment variables are not set
    """
    dt_url = os.environ.get('DT_URL') or os.environ.get('DYNATRACE_URL')
    dt_token = os.environ.get('DT_TOKEN') or os.environ.get('DYNATRACE_API_TOKEN')
    
    if not dt_url:
        raise ValueError(
            "Dynatrace URL not found. Please set DT_URL or DYNATRACE_URL environment variable.\n"
            "Example: export DT_URL='https://your-environment.live.dynatrace.com'"
        )
    
    if not dt_token:
        raise ValueError(
            "Dynatrace API token not found. Please set DT_TOKEN or DYNATRACE_API_TOKEN environment variable.\n"
            "Example: export DT_TOKEN='dt0c01.xxx...'"
        )
    
    # Ensure URL doesn't end with a slash
    dt_url = dt_url.rstrip('/')
    
    return dt_url, dt_token


def query_top_vulnerabilities(dt_url: str, dt_token: str, limit: int = 5) -> Dict[str, Any]:
    """
    Query Dynatrace for top OPEN vulnerabilities.
    
    Args:
        dt_url: Dynatrace environment URL
        dt_token: Dynatrace API token
        limit: Number of top vulnerabilities to retrieve (default: 5)
    
    Returns:
        dict: Query results from Dynatrace
    
    Raises:
        requests.exceptions.RequestException: If the API request fails
    """
    # DQL query to get top OPEN vulnerabilities from Runtime Vulnerability Analytics
    dql_query = f"""
fetch security.events, from:now()-1h
| filter dt.system.bucket=="default_securityevents_builtin"
     AND event.provider=="Dynatrace"
     AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
     AND event.level=="ENTITY"
// filter for the latest snapshot per entity
| dedup {{vulnerability.display_id, affected_entity.id}}, sort:{{timestamp desc}}
// filter for open non-muted vulnerabilities
| filter vulnerability.resolution.status == "OPEN"
     AND vulnerability.parent.mute.status != "MUTED"
     AND vulnerability.mute.status != "MUTED"
// now summarize on the vulnerability level
| summarize{{
    vulnerability.risk.score=round(takeMax(vulnerability.risk.score),decimals:1),
    vulnerability.title=takeFirst(vulnerability.title),
    vulnerability.references.cve=takeFirst(vulnerability.references.cve),
    last_detected=coalesce(takeMax(vulnerability.resolution.change_date),takeMax(vulnerability.parent.first_seen)),
    affected_entities=countDistinctExact(affected_entity.id),
    vulnerable_function_in_use=if(in("IN_USE",collectArray(vulnerability.davis_assessment.vulnerable_function_status)),true, else:false),
    public_internet_exposure=if(in("PUBLIC_NETWORK",collectArray(vulnerability.davis_assessment.exposure_status)),true,else:false),
    public_exploit_available=if(in("AVAILABLE",collectArray(vulnerability.davis_assessment.exploit_status)),true,else:false),
    data_assets_within_reach=if(in("REACHABLE",collectArray(vulnerability.davis_assessment.data_assets_status)),true,else:false)
}}, by: {{vulnerability.display_id}}
// map the risk level
| fieldsAdd vulnerability.risk.level=if(vulnerability.risk.score>=9,"CRITICAL",
                                     else:if(vulnerability.risk.score>=7,"HIGH",
                                     else:if(vulnerability.risk.score>=4,"MEDIUM",
                                     else:if(vulnerability.risk.score>=0.1,"LOW",
                                     else:"NONE"))))
| sort {{vulnerability.risk.score, direction:"descending"}}, {{affected_entities, direction:"descending"}}
| limit {limit}
"""
    
    # API endpoint for DQL queries
    api_endpoint = f"{dt_url}/api/v2/query/execute"
    
    headers = {
        "Authorization": f"Api-Token {dt_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": dql_query
    }
    
    try:
        response = requests.post(api_endpoint, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error querying Dynatrace API: {e}", file=sys.stderr)
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status code: {e.response.status_code}", file=sys.stderr)
            print(f"Response body: {e.response.text}", file=sys.stderr)
        raise


def format_vulnerability_output(results: Dict[str, Any]) -> None:
    """
    Format and print vulnerability results in a readable format.
    
    Args:
        results: Query results from Dynatrace
    """
    if 'result' not in results or 'records' not in results['result']:
        print("No vulnerability data found in the response.")
        return
    
    records = results['result']['records']
    
    if not records:
        print("No open vulnerabilities found.")
        return
    
    print(f"\n{'='*80}")
    print(f"TOP {len(records)} VULNERABILITIES FROM DYNATRACE")
    print(f"{'='*80}\n")
    
    for idx, record in enumerate(records, 1):
        vuln_id = record.get('vulnerability.display_id', 'N/A')
        title = record.get('vulnerability.title', 'N/A')
        risk_score = record.get('vulnerability.risk.score', 'N/A')
        risk_level = record.get('vulnerability.risk.level', 'N/A')
        cves = record.get('vulnerability.references.cve', [])
        affected_entities = record.get('affected_entities', 0)
        last_detected = record.get('last_detected', 'N/A')
        
        # Davis assessments
        vuln_func_in_use = record.get('vulnerable_function_in_use', False)
        public_exposure = record.get('public_internet_exposure', False)
        exploit_available = record.get('public_exploit_available', False)
        data_assets_reachable = record.get('data_assets_within_reach', False)
        
        print(f"#{idx} Vulnerability ID: {vuln_id}")
        print(f"   Title: {title}")
        print(f"   Risk Level: {risk_level} (Score: {risk_score})")
        
        if cves:
            cve_list = ', '.join(cves) if isinstance(cves, list) else cves
            print(f"   CVEs: {cve_list}")
        
        print(f"   Affected Entities: {affected_entities}")
        print(f"   Last Detected: {last_detected}")
        
        print(f"   Davis Assessments:")
        print(f"      - Vulnerable Function In Use: {'Yes' if vuln_func_in_use else 'No'}")
        print(f"      - Public Internet Exposure: {'Yes' if public_exposure else 'No'}")
        print(f"      - Public Exploit Available: {'Yes' if exploit_available else 'No'}")
        print(f"      - Data Assets Within Reach: {'Yes' if data_assets_reachable else 'No'}")
        print(f"   {'-'*76}")
        print()


def main():
    """
    Main function to execute the vulnerability query.
    """
    try:
        # Get Dynatrace configuration
        dt_url, dt_token = get_dynatrace_config()
        
        print("Querying Dynatrace for top 5 vulnerabilities...")
        print(f"Dynatrace URL: {dt_url}")
        
        # Query for top 5 vulnerabilities
        results = query_top_vulnerabilities(dt_url, dt_token, limit=5)
        
        # Format and display results
        format_vulnerability_output(results)
        
        # Also save raw JSON output to a file
        output_file = "dynatrace_top_vulnerabilities.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nRaw JSON output saved to: {output_file}")
        
    except ValueError as e:
        print(f"Configuration Error: {e}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"API Request Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
