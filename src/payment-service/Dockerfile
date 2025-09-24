FROM python:3.8.0-slim-buster

# Metadata labels for public GHCR visibility
LABEL org.opencontainers.image.title="unguard-payment-service"
LABEL org.opencontainers.image.source="https://github.com/AppSec-AI-Initiative-Dev/unguard"
LABEL org.opencontainers.image.description="Payment service for unguard demo application"
LABEL org.opencontainers.image.url="https://github.com/AppSec-AI-Initiative-Dev/unguard"
LABEL org.opencontainers.image.documentation="https://github.com/AppSec-AI-Initiative-Dev/unguard/blob/main/README.md"
LABEL org.opencontainers.image.licenses="Apache-2.0"

# Install Poetry
RUN pip install poetry==1.8.3

# Copy only requirements to cache them in docker layer
WORKDIR /poetry
COPY poetry.lock pyproject.toml /poetry/

# Project initialization:
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

# Creating folders, and files for a project:
WORKDIR /app
COPY . /app

EXPOSE 8084

RUN poetry run opentelemetry-bootstrap -a install

ENTRYPOINT ["opentelemetry-instrument", "python", "payment_service/run.py"]

