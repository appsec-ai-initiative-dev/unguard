FROM --platform=linux/amd64 envoyproxy/envoy:v1.23.0

# Metadata labels for public GHCR visibility
LABEL org.opencontainers.image.title="unguard-envoy-proxy"
LABEL org.opencontainers.image.source="https://github.com/AppSec-AI-Initiative-Dev/unguard"
LABEL org.opencontainers.image.description="Envoy proxy for unguard demo application"
LABEL org.opencontainers.image.url="https://github.com/AppSec-AI-Initiative-Dev/unguard"
LABEL org.opencontainers.image.documentation="https://github.com/AppSec-AI-Initiative-Dev/unguard/blob/main/README.md"
LABEL org.opencontainers.image.licenses="Apache-2.0"

RUN apt-get update && \
    apt-get install -y curl python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

USER envoy:envoy
ADD --chown=envoy:envoy config /etc/envoy/unguard

EXPOSE 8080
EXPOSE 8081

CMD ["-c", "/etc/envoy/unguard/envoy-config.yaml"]
