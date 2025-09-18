# Dynatrace MCP Server Analysis

## Summary

**The unguard repository does NOT contain a Dynatrace MCP (Model Context Protocol) server.** 

After a comprehensive investigation of the repository, no MCP server implementation was found. The unguard project is an insecure demo application designed for security testing and educational purposes.

## What is Actually in This Repository

The unguard repository contains a collection of intentionally vulnerable microservices written in various programming languages, designed to demonstrate security vulnerabilities. It is **not** an MCP server implementation.

### Actual Services and APIs Exposed

The repository contains the following microservices with their respective APIs:

#### 1. Ad Service (.NET 5)
**API Endpoints:**
- `GET /ad` - Returns HTML page with an image advertisement
- `GET /ads` - Returns available files on server
- `POST /delete-ad` - Deletes specified file (vulnerable)
- `POST /update-ad` - Uploads and extracts zip files (vulnerable)

#### 2. Proxy Service (Java Spring)
**API Endpoints:**
- `GET /` - Proxies requests with HTTP client (vulnerable to SSRF)
- `GET /image` - Proxies requests with curl (vulnerable to command injection)

#### 3. Status Service (Go)
**API Endpoints:**
- `GET /deployments` - Returns Kubernetes deployment information
- `GET /deployments/health` - Returns deployment health status
- `GET /users` - Returns user list from MariaDB (vulnerable to SQL injection)

#### 4. Microblog Service (Java Spring)
**REST API for:**
- Reading/creating posts
- Following other users
- User interactions

#### 5. User Auth Service (Node.js Express)
**API for:**
- User authentication with JWT tokens (vulnerable to JWT key confusion)
- User management (vulnerable to SQL injection)

#### 6. Profile Service (Java Spring)
**API for:**
- Updating user biography information in H2 database (vulnerable to SQL injection)

#### 7. Membership Service (.NET 7)
**API for:**
- Managing user memberships in MariaDB (vulnerable to SQL injection)

#### 8. Like Service (PHP)
**API for:**
- Adding likes to posts using MariaDB (vulnerable to SQL injection)

#### 9. Payment Service (Python Flask)
**API for:**
- Adding and retrieving credit card payment information

### Infrastructure Components

- **Envoy Proxy** - Routes traffic and provides vulnerable health endpoints
- **Frontend (Next.js)** - Modern web interface with API integration
- **Jaeger** - Distributed tracing stack
- **MariaDB** - Relational database for user and token data
- **Redis** - Key-value store for user data
- **User Simulator** - Synthetic traffic generation using Puppeteer
- **Malicious Load Generator** - Automated attack scenarios

## Conclusion

**There is no Dynatrace MCP server in this repository.** The unguard project is specifically designed as an insecure demo application for security testing, not as an MCP protocol implementation.

If you're looking for a Dynatrace MCP server implementation, you may need to:
1. Check a different repository
2. Verify the correct repository name/organization
3. Confirm if the MCP server exists as a separate project

## Repository Purpose

This repository serves as:
- A security testing playground
- Educational tool for understanding vulnerabilities
- Demo application for monitoring tools (including Dynatrace monitoring via Monaco)
- Example of cloud-native microservices architecture

The project is designed to be **intentionally insecure** and should only be run in sandboxed environments.