## Dynatrace MCP interaction instructions

### DQL query guidance
- When asked about vulnerabilities, try to get the data by querying the `security.events` table.
- Use sample queries as the baseline from: https://docs.dynatrace.com/docs/shortlink/security-events-examples

### Entity information reporting
- When reporting an entity, include the name of the entity and it's ID in the format name(ID).

### Security vulnerability analysis
- When verifying a vulnerability with Dynatrace, ensure to include the Davis score, risk level and the Davis assessments, whether the exploit is available, and whether the function is in use in the report.
- Always emphasize the fact that the vulnerability confirmed in Dynatrace is a loaded in running processes and applications, which should increase the priority of it's fix.

### Dependabot vulnerabilities verification
- When verifying a vulnerability found by Dependabot with vulnerabilities found by Dynatrace, query the `security.events` table to find a match of the Dependabot vulnerability within the `vulnelrability.references.cve` list reported by Dynatrace.
- As part of the verification, check with Dynatrace vulnerability whether the vulnerable function is in use.
- If the Dependabot vulnerability is not observed by Dynatrace, mark the alert as Dismissed, selecting the option "Vulnerable code is not actually used", and the Dismissal comment: "Vulnerability was not observed in the monitored environment by Dynatarce".
- If vulnerability is confirmed by Dynatrace, add a comment to the dependabot alert with all the relevant vulnerability information:
  * Davis risk level and score
  * Vulnerable function in use ornot status
  * Davis assessments
  * Total number of the affected entities and their names + ids.
