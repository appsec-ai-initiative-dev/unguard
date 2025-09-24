FROM locustio/locust:2.9.0

# Metadata labels for public GHCR visibility
LABEL org.opencontainers.image.title="unguard-malicious-load-generator"
LABEL org.opencontainers.image.source="https://github.com/AppSec-AI-Initiative-Dev/unguard"
LABEL org.opencontainers.image.description="Malicious load generator for unguard demo application"
LABEL org.opencontainers.image.url="https://github.com/AppSec-AI-Initiative-Dev/unguard"
LABEL org.opencontainers.image.documentation="https://github.com/AppSec-AI-Initiative-Dev/unguard/blob/main/README.md"
LABEL org.opencontainers.image.licenses="Apache-2.0"

# install curl
USER root
RUN apt-get update
RUN apt-get install -y curl

COPY --chown=locust:locust . .
RUN chmod +x loadgen.sh
ENTRYPOINT ./loadgen.sh