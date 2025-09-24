# based on snippet from https://github.com/puppeteer/puppeteer/blob/main/docs/troubleshooting.md
FROM --platform=linux/amd64 ghcr.io/puppeteer/puppeteer:24.11.0 AS base

# Metadata labels for public GHCR visibility
LABEL org.opencontainers.image.title="unguard-user-simulator"
LABEL org.opencontainers.image.source="https://github.com/AppSec-AI-Initiative-Dev/unguard"
LABEL org.opencontainers.image.description="User simulator service for unguard demo application"
LABEL org.opencontainers.image.url="https://github.com/AppSec-AI-Initiative-Dev/unguard"
LABEL org.opencontainers.image.documentation="https://github.com/AppSec-AI-Initiative-Dev/unguard/blob/main/README.md"
LABEL org.opencontainers.image.licenses="Apache-2.0"

COPY --chown=pptruser:pptruser . .

RUN npm install
RUN npm run build

ENV NODE_ENV=production
ENV NODE_CONFIG_STRICT_MODE=1
CMD ["npm", "start"]
