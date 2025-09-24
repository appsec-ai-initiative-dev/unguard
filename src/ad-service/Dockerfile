FROM mcr.microsoft.com/dotnet/aspnet:5.0-alpine AS base

# Metadata labels for public GHCR visibility
LABEL org.opencontainers.image.title="unguard-ad-service"
LABEL org.opencontainers.image.source="https://github.com/AppSec-AI-Initiative-Dev/unguard"
LABEL org.opencontainers.image.description="Ad service for unguard demo application"
LABEL org.opencontainers.image.url="https://github.com/AppSec-AI-Initiative-Dev/unguard"
LABEL org.opencontainers.image.documentation="https://github.com/AppSec-AI-Initiative-Dev/unguard/blob/main/README.md"
LABEL org.opencontainers.image.licenses="Apache-2.0"

WORKDIR /app
EXPOSE 8082

FROM mcr.microsoft.com/dotnet/sdk:5.0 AS build

# Copy csproj and restore as distinct layers
WORKDIR /src
COPY ["AdService.csproj", "."]
RUN dotnet restore "AdService.csproj"

# Copy everything else and build
WORKDIR /src
COPY . .
RUN dotnet build "AdService.csproj" -c Release -o /app/build

# publish
FROM build AS publish
RUN dotnet publish "AdService.csproj" -c Release -o /app/publish

FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .
ENTRYPOINT ["dotnet", "AdService.dll"]

