## Dynatrace MCP interaction instructions

### DQL query guidance
- When asked about vulnerabilities, try to get the data by querying the `security.events` table.
- Use sample queries as the baseline from: https://docs.dynatrace.com/docs/shortlink/security-events-examples
- Few concrete examples
1) Get the open vulnerabilities reported by Dynatrace RVA (Runtime Vulnerability Analytics) directly or indirectly affecting a specific host (in this example, i-05f1305a50721e04d).
```fetch security.events
| filter dt.system.bucket=="default_securityevents_builtin"
     AND event.provider=="Dynatrace"
     AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
     AND event.level=="ENTITY"
// filter for the latest snapshot per entity
| dedup {vulnerability.display_id, affected_entity.id}, sort:{timestamp desc}
// filter for open non-muted vulnerabilities
| filter vulnerability.resolution.status == "OPEN"
     AND vulnerability.parent.mute.status != "MUTED"
     AND vulnerability.mute.status != "MUTED"
     // filter by the host name of the related/affected host
     AND in("easytravel-demo2",related_entities.hosts.names) OR affected_entity.name=="easytravel-demo2"
// now summarize on the vulnerability level
| summarize{
    vulnerability.risk.score=round(takeMax(vulnerability.risk.score),decimals:1),
    vulnerability.title=takeFirst(vulnerability.title),
    vulnerability.references.cve=takeFirst(vulnerability.references.cve),
    last_detected=coalesce(takeMax(vulnerability.resolution.change_date),takeMax(vulnerability.parent.first_seen)),
    affected_entities=countDistinctExact(affected_entity.id),
    vulnerable_function_in_use=if(in("IN_USE",collectArray(vulnerability.davis_assessment.vulnerable_function_status)),true, else:false),
    public_internet_exposure=if(in("PUBLIC_NETWORK",collectArray(vulnerability.davis_assessment.exposure_status)),true,else:false),
    public_exploit_available=if(in("AVAILABLE",collectArray(vulnerability.davis_assessment.exploit_status)),true,else:false),
    data_assets_within_reach=if(in("REACHABLE",collectArray(vulnerability.davis_assessment.data_assets_status)),true,else:false)
}, by: {vulnerability.display_id}
// map the risk level
| fieldsAdd vulnerability.risk.level=if(vulnerability.risk.score>=9,"CRITICAL",
                                     else:if(vulnerability.risk.score>=7,"HIGH",
                                     else:if(vulnerability.risk.score>=4,"MEDIUM",
                                     else:if(vulnerability.risk.score>=0.1,"LOW",
                                     else:"NONE"))))
| sort {vulnerability.risk.score, direction:"descending"}, {affected_entities, direction:"descending"}
```

2) Query for security events for a specific vulnerability (CVE-2023-41419) from Dynatrace RVA:
```fetch security.events
| filter dt.system.bucket=="default_securityevents_builtin"
     AND event.provider=="Dynatrace"
     AND event.type=="VULNERABILITY_STATE_REPORT_EVENT"
     AND event.level=="ENTITY"
// filter for the latest snapshot per entity
| dedup {vulnerability.display_id, affected_entity.id}, sort:{timestamp desc}
| filter in("CVE-2023-41419",vulnerability.references.cve)
// filter for open non-muted vulnerabilities
| filter vulnerability.resolution.status == "OPEN"
     AND vulnerability.parent.mute.status != "MUTED"
     AND vulnerability.mute.status != "MUTED"
```

### Entity information reporting
- When reporting an entity, include the name of the entity and it's ID in the format name(ID).

### Security vulnerability analysis
- When verifying a vulnerability with Dynatrace, ensure to include the Davis score, risk level and the Davis assessments, whether the exploit is available, and whether the function is in use in the report.
- Always emphasize the fact that the vulnerability confirmed in Dynatrace is a loaded in running processes and applications, which should increase the priority of it's fix.

### Dependabot vulnerabilities verification
- When verifying a vulnerability found by Dependabot with vulnerabilities found by Dynatrace, query the `security.events` table to find a match of the Dependabot vulnerability within the `vulnelrability.references.cve` list reported by Dynatrace.
- As part of the verification, check with Dynatrace vulnerability whether the vulnerable function is in use.
- If the Dependabot vulnerability is not observed by Dynatrace, mark the alert as Dismissed, selecting the option "Vulnerable code is not actually used", and the Dismissal comment: "Vulnerability was not observed in the monitored environment by Dynatarce".
- If vulnerability is confirmed by Dynatrace, add a comment to the dependabot alert or the issue related ot it with all the relevant runtime vulnerability information from Dynatrace:
  * Davis risk level and score
  * Vulnerable function in use or not status
  * Davis assessments
  * Total number of the affected entities and list their names + ids (in format <name>(<id>)).
