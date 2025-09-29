# Local Dev Infrastructure Scripts

PowerShell helpers for running Unguard without spinning up the full Kubernetes stack.

## Prerequisites

- Docker Desktop (or another Docker Engine) running locally.
- PowerShell 7+ (tested) – Windows PowerShell 5.1 works as well.

## Usage

From the repository root:

`powershell
# Start MariaDB + Redis, create demo schemas
./ops/local-dev/start-local-services.ps1

# Optionally, override the defaults
./ops/local-dev/start-local-services.ps1 -MariaDbPassword 'strongpass' -MariaDbImage 'mariadb:11.4'
`

The script:

1. Ensures Docker is available.
2. Starts (or recreates) a unguard-mariadb container and creates the databases expected by the microservices (my_database, memberships, likeDb).
3. Starts (or recreates) a unguard-redis container.
4. Prints the environment variables each service should use when you run them via 
pm, yarn, dotnet run, etc.

When you are done with local development:

`powershell
./ops/local-dev/stop-local-services.ps1
`

That stops and removes the MariaDB and Redis demo containers.

> **Note**: These scripts are intentionally lightweight and only provision dependencies required by the Node/.NET/PHP services. Other components (Jaeger, S3 emulators, etc.) are not included.
