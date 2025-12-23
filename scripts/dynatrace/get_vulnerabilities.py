#!/usr/bin/env python3
"""
Dynatrace Vulnerability Retrieval Script

This script retrieves active vulnerabilities from Dynatrace using DQL queries
and outputs them in various formats (JSON, CSV, Markdown).

Requirements:
    - Python 3.7+
    - requests library (pip install requests)

Environment Variables:
    - DT_TENANT: Dynatrace tenant URL (e.g., https://abc12345.live.dynatrace.com)
    - DT_API_TOKEN: Dynatrace API token with 'storage:events:read' scope

Usage:
    # Basic usage (outputs JSON)
    python get_vulnerabilities.py

    # Specify output format
    python get_vulnerabilities.py --format json
    python get_vulnerabilities.py --format csv
    python get_vulnerabilities.py --format markdown

    # Filter by severity
    python get_vulnerabilities.py --severity CRITICAL,HIGH

    # Filter by function-in-use
    python get_vulnerabilities.py --function-in-use

    # Filter by CVE
    python get_vulnerabilities.py --cve CVE-2024-12345

    # Specify timeframe (days)
    python get_vulnerabilities.py --days 30

    # Output to file
    python get_vulnerabilities.py --output vulnerabilities.json
"""

import os
import sys
import json
import argparse
import csv
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

try:
    import requests
except ImportError:
    print("Error: requests library not found. Install with: pip install requests")
    sys.exit(1)


class DynatraceVulnerabilityClient:
    """Client for retrieving vulnerabilities from Dynatrace"""

    def __init__(self, tenant_url: str, api_token: str):
        """
        Initialize the Dynatrace client

        Args:
            tenant_url: Dynatrace tenant URL (e.g., https://abc12345.live.dynatrace.com)
            api_token: API token with 'storage:events:read' scope
        """
        self.tenant_url = tenant_url.rstrip('/')
        self.api_token = api_token
        self.api_endpoint = f"{self.tenant_url}/api/v2/query/execute"

    def build_vulnerability_query(
        self,
        days: int = 7,
        severity_filter: Optional[List[str]] = None,
        function_in_use: bool = False,
        cve_filter: Optional[str] = None,
        entity_id: Optional[str] = None
    ) -> str:
        """
        Build DQL query for retrieving vulnerabilities

        Args:
            days: Number of days to look back
            severity_filter: List of severities to filter (CRITICAL, HIGH, MEDIUM, LOW)
            function_in_use: Filter for vulnerabilities where function is in use
            cve_filter: Filter for specific CVE
            entity_id: Filter for specific entity

        Returns:
            DQL query string
        """
        query = f"""
fetch security.events, from:now() - {days}d
| filter event.type == "VULNERABILITY_STATE_REPORT_EVENT"
| dedup {{vulnerability.display_id, affected_entity.id}}, sort: {{timestamp desc}}
| filter vulnerability.resolution_status == "OPEN"
"""

        # Add severity filter
        if severity_filter:
            severities = '", "'.join(severity_filter)
            query += f'| filter vulnerability.severity in ["{severities}"]\n'

        # Add function-in-use filter
        if function_in_use:
            query += "| filter davis.assessment.vulnerable_function_in_use == true\n"

        # Add entity filter
        if entity_id:
            query += f'| filter affected_entity.id == "{entity_id}"\n'

        # Add CVE filter (needs expansion)
        if cve_filter:
            query += "| expand vulnerability.references.cve\n"
            query += f'| filter vulnerability.references.cve == "{cve_filter}"\n'

        # Add field mappings
        query += """
| fieldsAdd 
    vuln_id = vulnerability.display_id,
    vuln_title = vulnerability.title,
    severity = vulnerability.severity,
    cvss_score = vulnerability.cvss_score,
    davis_risk_level = davis.assessment.risk_level,
    davis_risk_score = davis.assessment.risk_score,
    function_in_use = davis.assessment.vulnerable_function_in_use,
    public_exploit = davis.assessment.public_exploit_available,
    reachable_data = davis.assessment.reachable_data_asset,
    technology = vulnerability.technology,
    vulnerable_component = vulnerability.vulnerable_component,
    cve_ids = vulnerability.references.cve,
    entity_name = entityName(affected_entity.id),
    entity_type = affected_entity.type,
    entity_id = affected_entity.id,
    resolution_status = vulnerability.resolution_status,
    muted = vulnerability.muted,
    first_seen = vulnerability.first_seen_timestamp,
    last_updated = timestamp
| fields 
    vuln_id, vuln_title, severity, cvss_score,
    davis_risk_level, davis_risk_score, function_in_use, public_exploit, reachable_data,
    technology, vulnerable_component, cve_ids,
    entity_name, entity_type, entity_id,
    resolution_status, muted, first_seen, last_updated
| sort davis_risk_score desc, cvss_score desc
"""
        return query.strip()

    def execute_query(self, dql_query: str) -> Dict[str, Any]:
        """
        Execute DQL query against Dynatrace

        Args:
            dql_query: DQL query string

        Returns:
            Query results as dictionary

        Raises:
            requests.exceptions.RequestException: If API request fails
        """
        headers = {
            "Authorization": f"Api-Token {self.api_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "query": dql_query
        }

        response = requests.post(
            self.api_endpoint,
            headers=headers,
            json=payload,
            timeout=30
        )

        response.raise_for_status()
        return response.json()

    def get_vulnerabilities(
        self,
        days: int = 7,
        severity_filter: Optional[List[str]] = None,
        function_in_use: bool = False,
        cve_filter: Optional[str] = None,
        entity_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve vulnerabilities from Dynatrace

        Args:
            days: Number of days to look back
            severity_filter: List of severities to filter
            function_in_use: Filter for vulnerabilities where function is in use
            cve_filter: Filter for specific CVE
            entity_id: Filter for specific entity

        Returns:
            List of vulnerability dictionaries
        """
        query = self.build_vulnerability_query(
            days=days,
            severity_filter=severity_filter,
            function_in_use=function_in_use,
            cve_filter=cve_filter,
            entity_id=entity_id
        )

        result = self.execute_query(query)

        # Extract records from result
        if "result" in result and "records" in result["result"]:
            return result["result"]["records"]
        return []


class VulnerabilityFormatter:
    """Format vulnerabilities for different output formats"""

    @staticmethod
    def to_json(vulnerabilities: List[Dict[str, Any]], pretty: bool = True) -> str:
        """Format vulnerabilities as JSON"""
        if pretty:
            return json.dumps(vulnerabilities, indent=2, default=str)
        return json.dumps(vulnerabilities, default=str)

    @staticmethod
    def to_csv(vulnerabilities: List[Dict[str, Any]]) -> str:
        """Format vulnerabilities as CSV"""
        if not vulnerabilities:
            return ""

        import io
        output = io.StringIO()
        
        # Define field order for CSV
        fieldnames = [
            'vuln_id', 'vuln_title', 'severity', 'cvss_score',
            'davis_risk_score', 'function_in_use', 'public_exploit',
            'technology', 'vulnerable_component', 'cve_ids',
            'entity_name', 'entity_id', 'first_seen', 'last_updated'
        ]

        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        
        for vuln in vulnerabilities:
            # Convert arrays and complex types to strings
            row = vuln.copy()
            if 'cve_ids' in row and isinstance(row['cve_ids'], list):
                row['cve_ids'] = ', '.join(row['cve_ids']) if row['cve_ids'] else ''
            writer.writerow(row)

        return output.getvalue()

    @staticmethod
    def to_markdown(vulnerabilities: List[Dict[str, Any]]) -> str:
        """Format vulnerabilities as Markdown table"""
        if not vulnerabilities:
            return "No vulnerabilities found."

        # Summary section
        md = "# Vulnerability Report\n\n"
        md += f"**Generated:** {datetime.now().isoformat()}\n"
        md += f"**Total Vulnerabilities:** {len(vulnerabilities)}\n\n"

        # Count by severity
        severity_counts = {}
        function_in_use_count = 0
        public_exploit_count = 0

        for vuln in vulnerabilities:
            severity = vuln.get('severity', 'UNKNOWN')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            if vuln.get('function_in_use'):
                function_in_use_count += 1
            if vuln.get('public_exploit'):
                public_exploit_count += 1

        md += "## Summary by Severity\n\n"
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            count = severity_counts.get(severity, 0)
            md += f"- **{severity}:** {count}\n"
        
        md += f"\n**Function In Use:** {function_in_use_count}\n"
        md += f"**Public Exploits Available:** {public_exploit_count}\n\n"

        # Detailed table
        md += "## Vulnerability Details\n\n"
        md += "| Vuln ID | Title | Severity | CVSS | Davis Score | Function In Use | Component | Entity |\n"
        md += "|---------|-------|----------|------|-------------|-----------------|-----------|--------|\n"

        for vuln in vulnerabilities:
            vuln_id = vuln.get('vuln_id', 'N/A')
            title = vuln.get('vuln_title', 'N/A')[:50]  # Truncate long titles
            severity = vuln.get('severity', 'N/A')
            cvss = vuln.get('cvss_score', 'N/A')
            davis = vuln.get('davis_risk_score', 'N/A')
            func_in_use = '✅' if vuln.get('function_in_use') else '❌'
            component = vuln.get('vulnerable_component', 'N/A')[:30]
            entity = vuln.get('entity_name', 'N/A')[:30]

            md += f"| {vuln_id} | {title} | {severity} | {cvss} | {davis} | {func_in_use} | {component} | {entity} |\n"

        return md


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Retrieve vulnerabilities from Dynatrace",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --format json
  %(prog)s --severity CRITICAL,HIGH --function-in-use
  %(prog)s --cve CVE-2024-12345
  %(prog)s --days 30 --output report.json
        """
    )

    parser.add_argument(
        '--format', '-f',
        choices=['json', 'csv', 'markdown'],
        default='json',
        help='Output format (default: json)'
    )

    parser.add_argument(
        '--severity', '-s',
        help='Filter by severity (comma-separated: CRITICAL,HIGH,MEDIUM,LOW)'
    )

    parser.add_argument(
        '--function-in-use',
        action='store_true',
        help='Filter for vulnerabilities where function is in use'
    )

    parser.add_argument(
        '--cve',
        help='Filter by specific CVE (e.g., CVE-2024-12345)'
    )

    parser.add_argument(
        '--entity',
        help='Filter by specific entity ID'
    )

    parser.add_argument(
        '--days', '-d',
        type=int,
        default=7,
        help='Number of days to look back (default: 7)'
    )

    parser.add_argument(
        '--output', '-o',
        help='Output file (default: stdout)'
    )

    parser.add_argument(
        '--tenant',
        help='Dynatrace tenant URL (default: DT_TENANT env var)'
    )

    parser.add_argument(
        '--token',
        help='Dynatrace API token (default: DT_API_TOKEN env var)'
    )

    args = parser.parse_args()

    # Get credentials
    tenant_url = args.tenant or os.getenv('DT_TENANT')
    api_token = args.token or os.getenv('DT_API_TOKEN')

    if not tenant_url or not api_token:
        print("Error: Dynatrace credentials not provided.", file=sys.stderr)
        print("Set DT_TENANT and DT_API_TOKEN environment variables or use --tenant and --token", file=sys.stderr)
        sys.exit(1)

    # Parse severity filter
    severity_filter = None
    if args.severity:
        severity_filter = [s.strip().upper() for s in args.severity.split(',')]

    try:
        # Create client and retrieve vulnerabilities
        client = DynatraceVulnerabilityClient(tenant_url, api_token)
        
        print(f"Retrieving vulnerabilities from Dynatrace...", file=sys.stderr)
        print(f"Timeframe: Last {args.days} days", file=sys.stderr)
        if severity_filter:
            print(f"Severity filter: {', '.join(severity_filter)}", file=sys.stderr)
        if args.function_in_use:
            print(f"Filtering for: Function in use", file=sys.stderr)
        if args.cve:
            print(f"CVE filter: {args.cve}", file=sys.stderr)

        vulnerabilities = client.get_vulnerabilities(
            days=args.days,
            severity_filter=severity_filter,
            function_in_use=args.function_in_use,
            cve_filter=args.cve,
            entity_id=args.entity
        )

        print(f"Found {len(vulnerabilities)} vulnerabilities", file=sys.stderr)

        # Format output
        formatter = VulnerabilityFormatter()
        
        if args.format == 'json':
            output = formatter.to_json(vulnerabilities)
        elif args.format == 'csv':
            output = formatter.to_csv(vulnerabilities)
        elif args.format == 'markdown':
            output = formatter.to_markdown(vulnerabilities)
        else:
            output = formatter.to_json(vulnerabilities)

        # Write output
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"Output written to: {args.output}", file=sys.stderr)
        else:
            print(output)

    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Dynatrace: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
