#!/usr/bin/env python3
"""
Dynatrace Vulnerability Query Script

This script queries Dynatrace Runtime Vulnerability Analytics (RVA) for the latest
vulnerabilities using the Dynatrace API and DQL queries.

Usage:
    python query_vulnerabilities.py [OPTIONS]

Environment Variables:
    DT_ENVIRONMENT: Dynatrace environment URL (e.g., https://abc123.live.dynatrace.com)
    DT_API_TOKEN: Dynatrace API token with the following permissions:
        - Read security events (securityEvents.read)
        - Execute DQL queries (dql.query.execute)

Examples:
    # Query all open vulnerabilities
    python query_vulnerabilities.py

    # Query only CRITICAL vulnerabilities
    python query_vulnerabilities.py --severity CRITICAL

    # Query vulnerabilities with function in use
    python query_vulnerabilities.py --function-in-use

    # Query specific CVE
    python query_vulnerabilities.py --cve CVE-2024-21508
"""

import os
import sys
import json
import argparse
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class DynatraceClient:
    """Client for interacting with Dynatrace API"""

    def __init__(self, environment_url: str, api_token: str):
        """
        Initialize the Dynatrace client.

        Args:
            environment_url: Dynatrace environment URL
            api_token: API token with required permissions
        """
        self.environment_url = environment_url.rstrip('/')
        self.api_token = api_token
        self.headers = {
            'Authorization': f'Api-Token {api_token}',
            'Content-Type': 'application/json'
        }

    def execute_dql_query(self, query: str) -> Dict:
        """
        Execute a DQL query against Dynatrace.

        Args:
            query: DQL query string

        Returns:
            Query results as a dictionary
        """
        url = f'{self.environment_url}/api/v2/query:execute'
        payload = {
            'query': query
        }

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error executing DQL query: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            sys.exit(1)


class VulnerabilityQuerier:
    """Query and format Dynatrace vulnerability data"""

    def __init__(self, client: DynatraceClient):
        """
        Initialize the vulnerability querier.

        Args:
            client: DynatraceClient instance
        """
        self.client = client

    def get_all_open_vulnerabilities(self, days: int = 7) -> List[Dict]:
        """
        Get all open vulnerabilities from the last N days.

        Args:
            days: Number of days to look back

        Returns:
            List of vulnerabilities
        """
        query = f"""
        fetch security.events, from:now()-{days}d
        | filter dt.system.bucket=="default_securityevents_builtin"
             AND event.provider=="Dynatrace"
             AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
             AND event.level=="ENTITY"
        | dedup {{vulnerability.display_id, affected_entity.id}}, sort:{{timestamp desc}}
        | filter vulnerability.resolution.status == "OPEN"
             AND vulnerability.parent.mute.status != "MUTED"
             AND vulnerability.mute.status != "MUTED"
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
        | fieldsAdd vulnerability.risk.level=if(vulnerability.risk.score>=9,"CRITICAL",
                                             else:if(vulnerability.risk.score>=7,"HIGH",
                                             else:if(vulnerability.risk.score>=4,"MEDIUM",
                                             else:if(vulnerability.risk.score>=0.1,"LOW",
                                             else:"NONE"))))
        | sort {{vulnerability.risk.score, direction:"descending"}}, {{affected_entities, direction:"descending"}}
        """
        return self._execute_and_parse(query)

    def get_vulnerabilities_by_severity(self, severity: str, days: int = 7) -> List[Dict]:
        """
        Get vulnerabilities filtered by severity level.

        Args:
            severity: Severity level (CRITICAL, HIGH, MEDIUM, LOW)
            days: Number of days to look back

        Returns:
            List of vulnerabilities
        """
        query = f"""
        fetch security.events, from:now()-{days}d
        | filter dt.system.bucket=="default_securityevents_builtin"
             AND event.provider=="Dynatrace"
             AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
             AND event.level=="ENTITY"
        | dedup {{vulnerability.display_id, affected_entity.id}}, sort:{{timestamp desc}}
        | filter vulnerability.resolution.status == "OPEN"
             AND vulnerability.parent.mute.status != "MUTED"
             AND vulnerability.mute.status != "MUTED"
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
        | fieldsAdd vulnerability.risk.level=if(vulnerability.risk.score>=9,"CRITICAL",
                                             else:if(vulnerability.risk.score>=7,"HIGH",
                                             else:if(vulnerability.risk.score>=4,"MEDIUM",
                                             else:if(vulnerability.risk.score>=0.1,"LOW",
                                             else:"NONE"))))
        | filter vulnerability.risk.level == "{severity}"
        | sort {{vulnerability.risk.score, direction:"descending"}}
        """
        return self._execute_and_parse(query)

    def get_vulnerabilities_with_function_in_use(self, days: int = 7) -> List[Dict]:
        """
        Get vulnerabilities where the vulnerable function is actually in use.

        Args:
            days: Number of days to look back

        Returns:
            List of vulnerabilities
        """
        query = f"""
        fetch security.events, from:now()-{days}d
        | filter dt.system.bucket=="default_securityevents_builtin"
             AND event.provider=="Dynatrace"
             AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
             AND event.level=="ENTITY"
        | dedup {{vulnerability.display_id, affected_entity.id}}, sort:{{timestamp desc}}
        | filter vulnerability.resolution.status == "OPEN"
             AND vulnerability.parent.mute.status != "MUTED"
             AND vulnerability.mute.status != "MUTED"
             AND vulnerability.davis_assessment.vulnerable_function_status == "IN_USE"
        | summarize{{
            vulnerability.risk.score=round(takeMax(vulnerability.risk.score),decimals:1),
            vulnerability.title=takeFirst(vulnerability.title),
            vulnerability.references.cve=takeFirst(vulnerability.references.cve),
            last_detected=coalesce(takeMax(vulnerability.resolution.change_date),takeMax(vulnerability.parent.first_seen)),
            affected_entities=countDistinctExact(affected_entity.id),
            public_internet_exposure=if(in("PUBLIC_NETWORK",collectArray(vulnerability.davis_assessment.exposure_status)),true,else:false),
            public_exploit_available=if(in("AVAILABLE",collectArray(vulnerability.davis_assessment.exploit_status)),true,else:false),
            data_assets_within_reach=if(in("REACHABLE",collectArray(vulnerability.davis_assessment.data_assets_status)),true,else:false)
        }}, by: {{vulnerability.display_id}}
        | fieldsAdd vulnerability.risk.level=if(vulnerability.risk.score>=9,"CRITICAL",
                                             else:if(vulnerability.risk.score>=7,"HIGH",
                                             else:if(vulnerability.risk.score>=4,"MEDIUM",
                                             else:if(vulnerability.risk.score>=0.1,"LOW",
                                             else:"NONE"))))
        | sort {{vulnerability.risk.score, direction:"descending"}}
        """
        return self._execute_and_parse(query)

    def get_vulnerability_by_cve(self, cve: str, days: int = 7) -> List[Dict]:
        """
        Look up a specific CVE.

        Args:
            cve: CVE identifier (e.g., CVE-2024-21508)
            days: Number of days to look back

        Returns:
            List of vulnerabilities matching the CVE
        """
        query = f"""
        fetch security.events, from:now()-{days}d
        | filter event.provider=="Dynatrace"
             AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
        | filter in("{cve}", vulnerability.references.cve)
        | dedup {{vulnerability.display_id, affected_entity.id}}, sort:{{timestamp desc}}
        | filter vulnerability.resolution.status == "OPEN"
        | fields vulnerability.display_id, vulnerability.title, vulnerability.references.cve, 
                 vulnerability.davis_assessment.vulnerable_function_status,
                 vulnerability.risk.score, affected_entity.id, affected_entity.name
        """
        return self._execute_and_parse(query)

    def _execute_and_parse(self, query: str) -> List[Dict]:
        """
        Execute a query and parse the results.

        Args:
            query: DQL query string

        Returns:
            List of result records
        """
        result = self.client.execute_dql_query(query)
        
        # Extract records from the result
        records = []
        if 'result' in result and 'records' in result['result']:
            records = result['result']['records']
        
        return records


def format_vulnerability_output(vulnerabilities: List[Dict], format_type: str = 'table') -> None:
    """
    Format and print vulnerability results.

    Args:
        vulnerabilities: List of vulnerability records
        format_type: Output format ('table', 'json', 'summary')
    """
    if not vulnerabilities:
        print("No vulnerabilities found.")
        return

    if format_type == 'json':
        print(json.dumps(vulnerabilities, indent=2, default=str))
        return

    if format_type == 'summary':
        print(f"\n{'='*80}")
        print(f"VULNERABILITY SUMMARY")
        print(f"{'='*80}")
        print(f"Total vulnerabilities found: {len(vulnerabilities)}\n")

        # Group by severity
        severity_counts = {}
        for vuln in vulnerabilities:
            level = vuln.get('vulnerability.risk.level', 'UNKNOWN')
            severity_counts[level] = severity_counts.get(level, 0) + 1

        print("By Severity:")
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'NONE']:
            count = severity_counts.get(severity, 0)
            if count > 0:
                print(f"  {severity}: {count}")
        print()
        return

    # Table format (default)
    print(f"\n{'='*120}")
    print(f"DYNATRACE RUNTIME VULNERABILITY ANALYTICS - LATEST VULNERABILITIES")
    print(f"{'='*120}\n")

    for idx, vuln in enumerate(vulnerabilities, 1):
        display_id = vuln.get('vulnerability.display_id', 'N/A')
        title = vuln.get('vulnerability.title', 'N/A')
        cve = vuln.get('vulnerability.references.cve', [])
        risk_score = vuln.get('vulnerability.risk.score', 'N/A')
        risk_level = vuln.get('vulnerability.risk.level', 'N/A')
        affected_entities = vuln.get('affected_entities', 0)
        func_in_use = vuln.get('vulnerable_function_in_use', False)
        exploit_available = vuln.get('public_exploit_available', False)
        public_exposure = vuln.get('public_internet_exposure', False)
        data_reachable = vuln.get('data_assets_within_reach', False)

        print(f"[{idx}] {display_id}")
        print(f"    Title: {title}")
        if cve:
            cve_list = cve if isinstance(cve, list) else [cve]
            print(f"    CVE: {', '.join(cve_list)}")
        print(f"    Risk: {risk_level} (Score: {risk_score})")
        print(f"    Affected Entities: {affected_entities}")
        print(f"    Davis Assessment:")
        print(f"      - Vulnerable Function In Use: {'✓ YES' if func_in_use else '✗ NO'}")
        print(f"      - Public Exploit Available: {'✓ YES' if exploit_available else '✗ NO'}")
        print(f"      - Public Internet Exposure: {'✓ YES' if public_exposure else '✗ NO'}")
        print(f"      - Data Assets Within Reach: {'✓ YES' if data_reachable else '✗ NO'}")
        print()

    print(f"{'='*120}")
    print(f"Total: {len(vulnerabilities)} vulnerabilities")
    print(f"{'='*120}\n")


def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(
        description='Query Dynatrace for the latest vulnerabilities',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--environment',
        help='Dynatrace environment URL (or set DT_ENVIRONMENT env var)',
        default=os.environ.get('DT_ENVIRONMENT')
    )
    
    parser.add_argument(
        '--token',
        help='Dynatrace API token (or set DT_API_TOKEN env var)',
        default=os.environ.get('DT_API_TOKEN')
    )
    
    parser.add_argument(
        '--severity',
        choices=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'],
        help='Filter by severity level'
    )
    
    parser.add_argument(
        '--function-in-use',
        action='store_true',
        help='Show only vulnerabilities where the vulnerable function is in use'
    )
    
    parser.add_argument(
        '--cve',
        help='Look up a specific CVE (e.g., CVE-2024-21508)'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Number of days to look back (default: 7)'
    )
    
    parser.add_argument(
        '--format',
        choices=['table', 'json', 'summary'],
        default='table',
        help='Output format (default: table)'
    )

    args = parser.parse_args()

    # Validate required parameters
    if not args.environment:
        print("Error: Dynatrace environment URL is required. Set DT_ENVIRONMENT or use --environment")
        sys.exit(1)
    
    if not args.token:
        print("Error: Dynatrace API token is required. Set DT_API_TOKEN or use --token")
        sys.exit(1)

    # Initialize client
    client = DynatraceClient(args.environment, args.token)
    querier = VulnerabilityQuerier(client)

    # Execute query based on options
    try:
        if args.cve:
            print(f"Querying Dynatrace for CVE: {args.cve}...")
            vulnerabilities = querier.get_vulnerability_by_cve(args.cve, args.days)
        elif args.function_in_use:
            print(f"Querying Dynatrace for vulnerabilities with function in use (last {args.days} days)...")
            vulnerabilities = querier.get_vulnerabilities_with_function_in_use(args.days)
        elif args.severity:
            print(f"Querying Dynatrace for {args.severity} vulnerabilities (last {args.days} days)...")
            vulnerabilities = querier.get_vulnerabilities_by_severity(args.severity, args.days)
        else:
            print(f"Querying Dynatrace for all open vulnerabilities (last {args.days} days)...")
            vulnerabilities = querier.get_all_open_vulnerabilities(args.days)

        # Format and display results
        format_vulnerability_output(vulnerabilities, args.format)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
