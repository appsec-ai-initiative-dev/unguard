# Application Crash Investigation - Root Cause Analysis

**Investigation Date:** 2025-10-15  
**Investigator:** AI Incident Response System  
**Status:** ✅ RESOLVED - Application NOT Crashing

---

## Executive Summary

**Finding:** The unguard application is **NOT crashing**. The application is functioning normally with proper exception handling. However, a **data integrity issue** was identified causing a 33.5% error rate on the profile service's getBio endpoint.

---

## Investigation Results

### 1. Davis AI Problems Analysis ✅
- **No active problems** affecting the unguard application
- All microservices running normally
- Service availability: 100%

### 2. Backend Exceptions Analysis ⚠️

**Total Exceptions Found:** 243 in last 4 hours

**Exception Details:**
- **Type:** `org.dynatrace.profileservice.exceptions.BioNotFoundException`
- **Location:** `BioController.java:121`
- **Method:** `getBio()`
- **Affected Users:** 81 unique user IDs
- **Error Rate:** 33.5% (81 failed / 242 total getBio requests)
- **HTTP Status:** 404 Not Found (correctly handled as expected business logic)

**Stack Trace:**
```
org.dynatrace.profileservice.BioController.getBio (BioController.java:121)
→ Spring CGLIB Proxy
→ Spring AOP Framework  
→ Tomcat Request Processing
```

### 3. Error Logs Correlation ✅
- No ERROR or WARN logs found matching the exceptions
- This confirms exceptions are **properly handled** as expected business logic

### 4. Business Impact Assessment ⚠️
- **Error Rate:** 33.5%
- **Service Availability:** 100% uptime
- **Performance:** Fast response (~2-3ms per request)
- **Affected Users:** 81 users cannot view their bios
- **Service:** `unguard-profile-service` (SERVICE-4EDEC65BF29137C0)

---

## Root Cause Analysis

### Primary Cause: Missing Biography Data

The `BioController.getBio()` method throws `BioNotFoundException` when users don't have bio records in the database:

```java
@GetMapping("/user/{id}/bio")
public Bio getBio(@PathVariable("id") String userId) throws BioNotFoundException {
    Bio bio = databaseManager.getBio(Integer.parseInt(userId));
    
    if (bio != null) {
        return bio;
    }
    
    throw new BioNotFoundException("Bio for user with id '" + userId + "' not found"); // Line 121
}
```

**File:** `src/profile-service/src/main/java/org/dynatrace/profileservice/BioController.java`

### Contributing Factors:
1. **Incomplete User Onboarding:** Users created without bio initialization
2. **Test Data:** Sequential IDs suggest load testing without bio setup
3. **Data Migration Gap:** Possible missing bio records from user imports

---

## 🚨 CRITICAL SECURITY VULNERABILITY DETECTED

### Command Injection Vulnerability

**Severity:** 🔴 CRITICAL  
**Location:** `BioController.java:78` in `markdownToHtml()` method  
**Risk:** Remote Code Execution (RCE)

**Vulnerable Code:**
```java
private String markdownToHtml(String markdown) {
    // Unsafe code below, vulnerable to command injection, as 'markdown' is user controlled
    final String[] command = {"/bin/sh", "-c", "echo '" + markdown + "' | markdown"};
    
    final ProcessBuilder processBuilder = new ProcessBuilder(command);
    // ... process execution
}
```

**Problem:** User-controlled input (`markdown`) is directly concatenated into shell commands without sanitization.

**Attack Vector:**
```bash
# Attacker can send bioText like:
'; rm -rf / #

# Which creates command:
echo ''; rm -rf / #' | markdown
```

---

## Recommendations

### Immediate Actions (24 hours)

1. **Fix Command Injection Vulnerability** 🔴 CRITICAL
   - Remove shell execution for markdown conversion
   - Use a secure markdown library (e.g., CommonMark, Flexmark)
   - Never concatenate user input into shell commands

2. **Verify Data Integrity**
   - Identify which users lack bio records
   - Determine if this is expected behavior or a bug

3. **Set Up Monitoring**
   - Alert when getBio error rate > 10%
   - Track bio coverage metrics

### Short-term Actions (1 week)

4. **Implement Bio Initialization**
   - Create default bio records on user creation
   - Add database migration to backfill missing bios

5. **API Documentation**
   - Document that 404 is expected for users without bios
   - Update API contracts

### Long-term Actions (Next Sprint)

6. **Security Hardening**
   - Security audit of all shell command usage
   - Add SAST scanning to CI/CD pipeline
   - Implement input validation framework

7. **Database Schema Enhancement**
   - Consider making bio optional with proper null handling
   - Add foreign key constraints for data integrity

---

## Service Health Status

| Metric | Status | Value |
|--------|--------|-------|
| Service Availability | ✅ GREEN | 100% |
| Performance | ✅ GREEN | 2-3ms avg |
| Data Integrity | ⚠️ YELLOW | 81 missing bios |
| Error Rate | ⚠️ YELLOW | 33.5% |
| Security | 🔴 RED | Command injection exists |

---

## Conclusion

**The application is NOT crashing** - it's working as designed with proper exception handling. The perceived "crash" is actually:

1. **Expected behavior:** 404 responses for missing bio data (correctly handled)
2. **Data quality issue:** 81 users missing bio records (needs attention)
3. **Security vulnerability:** Critical command injection flaw (requires immediate fix)

**Next Steps:**
1. Fix the command injection vulnerability immediately
2. Review user onboarding process to ensure bio initialization
3. Consider backfilling missing bio records
4. Update monitoring to distinguish between "missing data 404" vs "service failure"

---

## Technical Details

**DQL Queries Used:**
- Davis Problems: `fetch dt.davis.problems, from:now() - 24h`
- Exception Analysis: `fetch spans, from:now() - 4h | filter request.is_failed == true and isNotNull(span.events) | expand span.events`
- Service Metrics: `timeseries sum(dt.service.request.count, scalar: true), from: now()-4h`

**Investigation Methodology:**
Following Dynatrace Expert Incident Response workflow:
1. ✅ Query Davis AI problems
2. ✅ Analyze backend exceptions (with MANDATORY span.events expansion)
3. ✅ Correlate with error logs
4. ✅ Assess business impact
5. ✅ Provide detailed RCA with file locations
