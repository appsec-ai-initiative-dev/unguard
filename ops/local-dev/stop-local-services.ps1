param(
    [string]$MariaDbContainer = "unguard-mariadb",
    [string]$RedisContainer = "unguard-redis"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Remove-ContainerIfExists {
    param([string]$Name)

    $exists = docker ps -a --format '{{.Names}}' | Where-Object { $_ -eq $Name }
    if (-not $exists) {
        Write-Host "Container '$Name' not found." -ForegroundColor DarkGray
        return
    }

    if (docker ps --format '{{.Names}}' | Where-Object { $_ -eq $Name }) {
        Write-Host "Stopping '$Name'" -ForegroundColor Yellow
        docker stop $Name | Out-Null
    }

    Write-Host "Removing '$Name'" -ForegroundColor Yellow
    docker rm $Name | Out-Null
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Docker CLI not found. Nothing to clean up.'
}

Remove-ContainerIfExists -Name $MariaDbContainer
Remove-ContainerIfExists -Name $RedisContainer

Write-Host 'Local MariaDB/Redis containers removed.' -ForegroundColor Green
