param(
    [string]$MariaDbPassword = "unguard",
    [string]$MariaDbContainer = "unguard-mariadb",
    [string]$MariaDbImage = "mariadb:11",
    [string]$RedisContainer = "unguard-redis",
    [string]$RedisImage = "redis:7-alpine"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Assert-DockerAvailable {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw 'Docker CLI not found. Install Docker Desktop or ensure docker.exe is on PATH.'
    }

    docker version | Out-Null
}

function Ensure-Container {
    param(
        [string]$Name,
        [ScriptBlock]$Create,
        [ScriptBlock]$Wait
    )

    $exists = docker ps -a --format '{{.Names}}' | Where-Object { $_ -eq $Name }

    if (-not $exists) {
        & $Create
    } elseif (-not (docker ps --format '{{.Names}}' | Where-Object { $_ -eq $Name })) {
        Write-Host "Starting container '$Name'" -ForegroundColor Yellow
        docker start $Name | Out-Null
    } else {
        Write-Host "Container '$Name' already running" -ForegroundColor Green
    }

    if ($Wait) {
        & $Wait
    }
}

function Initialize-MariaDb {
    Write-Host "Ensuring MariaDB container..." -ForegroundColor Cyan
    Ensure-Container -Name $MariaDbContainer -Create {
        Write-Host "Creating MariaDB container '$MariaDbContainer'" -ForegroundColor Yellow
        docker run -d `
            --name $MariaDbContainer `
            -e "MARIADB_ROOT_PASSWORD=$MariaDbPassword" `
            -p 3306:3306 `
            $MariaDbImage | Out-Null
    } -Wait {
        Write-Host 'Waiting for MariaDB to accept connections...' -ForegroundColor Yellow
        $timeout = [TimeSpan]::FromMinutes(2)
        $sw = [Diagnostics.Stopwatch]::StartNew()
        while ($sw.Elapsed -lt $timeout) {
            try {
                docker exec $MariaDbContainer mysqladmin ping -uroot -p$MariaDbPassword --silent 2>$null | Out-Null
                Write-Host 'MariaDB is ready.' -ForegroundColor Green
                break
            } catch {
                Start-Sleep -Seconds 2
            }
        }

        if ($sw.Elapsed -ge $timeout) {
            throw 'Timed out waiting for MariaDB to start.'
        }

        Write-Host 'Creating required schemas...' -ForegroundColor Yellow
        $createSql = (
            "CREATE DATABASE IF NOT EXISTS my_database;",
            "CREATE DATABASE IF NOT EXISTS memberships;",
            "CREATE DATABASE IF NOT EXISTS likeDb;"
        ) -join "`n"
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($createSql)
        $tempFile = New-TemporaryFile
        [System.IO.File]::WriteAllBytes($tempFile.FullName, $bytes)
        try {
            docker cp $tempFile.FullName "${MariaDbContainer}:/tmp/init.sql" | Out-Null
            docker exec $MariaDbContainer sh -c "mysql -uroot -p$MariaDbPassword < /tmp/init.sql" | Out-Null
        } finally {
            Remove-Item $tempFile.FullName -Force
        }
    }
}

function Initialize-Redis {
    Write-Host "Ensuring Redis container..." -ForegroundColor Cyan
    Ensure-Container -Name $RedisContainer -Create {
        Write-Host "Creating Redis container '$RedisContainer'" -ForegroundColor Yellow
        docker run -d `
            --name $RedisContainer `
            -p 6379:6379 `
            $RedisImage | Out-Null
    } -Wait {
        Write-Host 'Waiting for Redis to accept connections...' -ForegroundColor Yellow
        $timeout = [TimeSpan]::FromMinutes(1)
        $sw = [Diagnostics.Stopwatch]::StartNew()
        while ($sw.Elapsed -lt $timeout) {
            try {
                docker exec $RedisContainer redis-cli ping | Out-Null
                Write-Host 'Redis is ready.' -ForegroundColor Green
                break
            } catch {
                Start-Sleep -Seconds 2
            }
        }

        if ($sw.Elapsed -ge $timeout) {
            throw 'Timed out waiting for Redis to start.'
        }
    }
}

Assert-DockerAvailable
Initialize-MariaDb
Initialize-Redis

Write-Host ''
Write-Host 'Local infrastructure ready.' -ForegroundColor Green
Write-Host 'Use the following environment variables in each microservice shell:'
Write-Host "  MARIADB_SERVICE=127.0.0.1" -ForegroundColor Cyan
Write-Host "  MARIADB_PASSWORD=$MariaDbPassword" -ForegroundColor Cyan
Write-Host "  UNGUARD_MARIADB_SERVICE_HOST=127.0.0.1" -ForegroundColor Cyan
Write-Host "  UNGUARD_MARIADB_SERVICE_PORT_MYSQL=3306" -ForegroundColor Cyan
Write-Host ''
Write-Host 'When finished developing, run ops/local-dev/stop-local-services.ps1 to clean up.' -ForegroundColor Yellow
