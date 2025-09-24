FROM gradle:6.9.1-jdk11 as builder

# Metadata labels for public GHCR visibility
LABEL org.opencontainers.image.title="unguard-microblog-service"
LABEL org.opencontainers.image.source="https://github.com/AppSec-AI-Initiative-Dev/unguard"
LABEL org.opencontainers.image.description="Microblog service for unguard demo application"
LABEL org.opencontainers.image.url="https://github.com/AppSec-AI-Initiative-Dev/unguard"
LABEL org.opencontainers.image.documentation="https://github.com/AppSec-AI-Initiative-Dev/unguard/blob/main/README.md"
LABEL org.opencontainers.image.licenses="Apache-2.0"

COPY --chown=gradle:gradle . /home/gradle/src
WORKDIR /home/gradle/src
RUN gradle build

FROM openjdk:11-jre-slim
EXPOSE 8080
COPY --from=builder /home/gradle/src/build/libs/**.jar /app/app.jar
WORKDIR /app
ENTRYPOINT ["java","-jar","app.jar"]
