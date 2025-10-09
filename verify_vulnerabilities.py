#!/usr/bin/env python3
"""
Script to verify Dependabot vulnerabilities with Dynatrace.
Queries Dynatrace to check which vulnerabilities are confirmed in running applications.
"""

import os
import sys
import json
import requests
from typing import Dict, List, Any, Optional

class DynatraceVerifier:
    def __init__(self):
        self.dt_base_url = os.getenv('DT_BASE_URL')
        self.dt_environment = os.getenv('DT_ENVIRONMENT')
        self.github_pat = os.getenv('COPILOT_SPONSOR_PAT_VALERIY')
        
        if not self.dt_base_url or not self.dt_environment:
            raise ValueError("Missing Dynatrace environment variables")
            
        # Define vulnerabilities to check
        self.vulnerabilities = [
            {
                "cve": "CVE-2023-41419",
                "package": "gevent",
                "service": "malicious-load-generator",
                "alert_id": 44,
                "fixed_version": "23.9.0"
            },
            {
                "cve": "CVE-2022-40083", 
                "package": "github.com/labstack/echo/v4",
                "service": "status-service",
                "alert_id": 86,
                "fixed_version": "4.9.0"
            },
            {
                "cve": "CVE-2024-45337",
                "package": "golang.org/x/crypto", 
                "service": "status-service",
                "alert_id": 102,
                "fixed_version": "0.31.0"
            },
            {
                "cve": "CVE-2021-44906",
                "package": "minimist",
                "service": "user-auth-service", 
                "alert_id": 129,
                "fixed_version": "1.2.6"
            },
            {
                "cve": "CVE-2024-21511",
                "package": "mysql2",
                "service": "user-auth-service",
                "alert_id": 138, 
                "fixed_version": "3.9.7"
            },
            {
                "cve": "CVE-2024-21508",
                "package": "mysql2",
                "service": "user-auth-service",
                "alert_id": 137,
                "fixed_version": "3.9.4"
            },
            {
                "cve": "CVE-2025-29927", 
                "package": "next",
                "service": "frontend-nextjs",
                "alert_id": 11,
                "fixed_version": "15.2.3"
            }
        ]

    def query_dynatrace(self, dql_query: str) -> Optional[Dict]:
        """Execute a DQL query against Dynatrace"""
        try:
            # Use the MCP gateway URL structure
            url = f"{self.dt_base_url}/dt-security/v1/query/execute"
            headers = {
                "Content-Type": "application/json"
            }
            
            payload = {
                "query": dql_query,
                "requestTimeoutMilliseconds": 30000
            }
            
            print(f"Querying Dynatrace: {dql_query[:100]}...")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            print(f"Error querying Dynatrace: {e}")
            return None

    def check_running_containers(self, service_name: str) -> List[Dict]:
        """Check if containers for a service are running"""
        dql_query = f"""
        fetch dt.entity.container_group_instance
        | fieldsAdd containerImageName, matchingOptions=splitString("appsec-ai-initiative-dev/unguard/src/{service_name}", "/")
        | fieldsAdd collectedArray=iCollectArray(contains(containerImageName,matchingOptions[]))
        | filterOut in(false,collectedArray)
        | fieldsAdd entity.name, entity.type
        """
        
        result = self.query_dynatrace(dql_query)
        if result and "records" in result:
            return result["records"]
        return []

    def check_vulnerability_in_security_events(self, cve: str) -> Dict:
        """Check if a CVE is reported in Dynatrace security events"""
        dql_query = f"""
        fetch security.events
        | filter dt.system.bucket=="default_securityevents_builtin"
             AND event.provider=="Dynatrace"
             AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
             AND event.level=="ENTITY"
        | dedup {{vulnerability.display_id, affected_entity.id}}, sort:{{timestamp desc}}
        | filter in("{cve}", vulnerability.references.cve)
        | filter vulnerability.resolution.status == "OPEN"
             AND vulnerability.parent.mute.status != "MUTED"
             AND vulnerability.mute.status != "MUTED"
        | fieldsAdd vulnerability.davis_assessment.vulnerable_function_status,
                     vulnerability.davis_assessment.exploit_status,
                     vulnerability.davis_assessment.exposure_status,
                     vulnerability.davis_assessment.data_assets_status,
                     vulnerability.risk.score,
                     vulnerability.risk.level,
                     affected_entity.name,
                     affected_entity.id
        """
        
        result = self.query_dynatrace(dql_query)
        return {
            "found": result and "records" in result and len(result["records"]) > 0,
            "records": result.get("records", []) if result else []
        }

    def verify_vulnerability(self, vuln_info: Dict) -> Dict:
        """Verify a single vulnerability"""
        print(f"\n=== Verifying {vuln_info['cve']} in {vuln_info['service']} ===")
        
        # Check running containers
        containers = self.check_running_containers(vuln_info['service'])
        print(f"Found {len(containers)} running containers for {vuln_info['service']}")
        
        # Check security events
        security_events = self.check_vulnerability_in_security_events(vuln_info['cve'])
        print(f"Security events found: {security_events['found']}")
        
        if security_events['found']:
            records = security_events['records']
            print(f"Found {len(records)} security event records")
            
            # Check if vulnerable function is in use
            vulnerable_function_in_use = False
            for record in records:
                func_status = record.get('vulnerability.davis_assessment.vulnerable_function_status')
                if func_status == "IN_USE":
                    vulnerable_function_in_use = True
                    break
            
            print(f"Vulnerable function in use: {vulnerable_function_in_use}")
            
            # Determine status
            if vulnerable_function_in_use:
                status = "Confirmed"
                reason = "Vulnerability found in security events AND vulnerable function is in use"
            else:
                status = "Not-confirmed" 
                reason = "Vulnerability found in security events but vulnerable function is NOT in use"
        else:
            if len(containers) > 0:
                status = "Not-confirmed"
                reason = "Service is running but vulnerability not found in security events"
            else:
                status = "Not-confirmed"
                reason = "Service not running and vulnerability not found in security events"
        
        return {
            "cve": vuln_info['cve'],
            "package": vuln_info['package'], 
            "service": vuln_info['service'],
            "alert_id": vuln_info['alert_id'],
            "fixed_version": vuln_info['fixed_version'],
            "status": status,
            "reason": reason,
            "containers_found": len(containers),
            "security_events_found": security_events['found'],
            "security_events_count": len(security_events['records']),
            "security_events_details": security_events['records']
        }

    def dismiss_dependabot_alert(self, alert_id: int, reason: str) -> bool:
        """Dismiss a Dependabot alert using GitHub API"""
        if not self.github_pat:
            print("No GitHub PAT available, cannot dismiss alerts")
            return False
            
        try:
            url = f"https://api.github.com/repos/appsec-ai-initiative-dev/unguard/dependabot/alerts/{alert_id}"
            headers = {
                "Authorization": f"token {self.github_pat}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            payload = {
                "state": "dismissed",
                "dismissed_reason": "not_used",
                "dismissed_comment": reason
            }
            
            response = requests.patch(url, headers=headers, json=payload)
            response.raise_for_status()
            print(f"Successfully dismissed alert {alert_id}")
            return True
            
        except Exception as e:
            print(f"Error dismissing alert {alert_id}: {e}")
            return False

    def add_github_comment(self, issue_number: int, comment: str) -> bool:
        """Add a comment to the GitHub issue"""
        if not self.github_pat:
            print("No GitHub PAT available, cannot add comments")
            return False
            
        try:
            url = f"https://api.github.com/repos/appsec-ai-initiative-dev/unguard/issues/{issue_number}/comments"
            headers = {
                "Authorization": f"token {self.github_pat}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            payload = {"body": comment}
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            print(f"Successfully added comment to issue #{issue_number}")
            return True
            
        except Exception as e:
            print(f"Error adding comment to issue #{issue_number}: {e}")
            return False

    def run_verification(self):
        """Run verification for all vulnerabilities"""
        print("Starting Dynatrace vulnerability verification...")
        print(f"Dynatrace environment: {self.dt_environment}")
        
        results = []
        confirmed_vulns = []
        not_confirmed_vulns = []
        
        for vuln in self.vulnerabilities:
            result = self.verify_vulnerability(vuln)
            results.append(result)
            
            if result['status'] == 'Confirmed':
                confirmed_vulns.append(result)
            else:
                not_confirmed_vulns.append(result)
        
        # Generate summary
        print(f"\n=== VERIFICATION SUMMARY ===")
        print(f"Total vulnerabilities checked: {len(results)}")
        print(f"Confirmed vulnerabilities: {len(confirmed_vulns)}")
        print(f"Not-confirmed vulnerabilities: {len(not_confirmed_vulns)}")
        
        # Generate report for GitHub issue
        comment_parts = ["## Dynatrace Vulnerability Verification Results\n"]
        
        if confirmed_vulns:
            comment_parts.append("### ✅ Confirmed Vulnerabilities (need fixing):\n")
            for vuln in confirmed_vulns:
                comment_parts.append(f"- **{vuln['cve']}** ({vuln['package']}) in {vuln['service']}")
                comment_parts.append(f"  - Status: {vuln['status']}")
                comment_parts.append(f"  - Reason: {vuln['reason']}")
                comment_parts.append(f"  - Fix available: {vuln['fixed_version']}\n")
        
        if not_confirmed_vulns:
            comment_parts.append("### ❌ Not-Confirmed Vulnerabilities (will be dismissed):\n")
            for vuln in not_confirmed_vulns:
                comment_parts.append(f"- **{vuln['cve']}** ({vuln['package']}) in {vuln['service']}")
                comment_parts.append(f"  - Status: {vuln['status']}")
                comment_parts.append(f"  - Reason: {vuln['reason']}\n")
        
        comment = "\n".join(comment_parts)
        
        # Add comment to GitHub issue
        self.add_github_comment(432, comment)
        
        # Dismiss not-confirmed alerts
        for vuln in not_confirmed_vulns:
            self.dismiss_dependabot_alert(vuln['alert_id'], vuln['reason'])
        
        # Save results to file for further processing
        with open('/tmp/verification_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        return results

if __name__ == "__main__":
    try:
        verifier = DynatraceVerifier()
        results = verifier.run_verification()
        
        # Exit with appropriate code
        confirmed_count = len([r for r in results if r['status'] == 'Confirmed'])
        if confirmed_count > 0:
            print(f"\nFound {confirmed_count} confirmed vulnerabilities that need fixing.")
        else:
            print("\nNo confirmed vulnerabilities found.")
            
    except Exception as e:
        print(f"Error during verification: {e}")
        sys.exit(1)