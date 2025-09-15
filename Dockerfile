# Umbrella image for unguard (optional aggregate image)
# This can serve as a simple landing container (e.g., Nginx serving docs or a placeholder)
FROM nginx:1.27-alpine
LABEL org.opencontainers.image.title="unguard"
LABEL org.opencontainers.image.source="https://github.com/AppSec-AI-Initiative-Dev/unguard"
LABEL org.opencontainers.image.description="Aggregate placeholder image for unguard demo stack"

# Provide a minimal index page
RUN echo '<html><head><title>unguard</title></head><body><h1>unguard</h1><p>Composite microservices demo - see Helm chart for services.</p></body></html>' > /usr/share/nginx/html/index.html

EXPOSE 80
