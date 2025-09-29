FROM jenkins/jenkins:lts-jdk17

USER root
RUN mkdir -p /opt/demo-fake-secrets
COPY fake-secrets/ /opt/demo-fake-secrets/
RUN chown -R jenkins:jenkins /opt/demo-fake-secrets && chmod 600 /opt/demo-fake-secrets/*
ENV SAFE_TOKEN_JENKINS_ENV=SAFE_TOKEN_901
ENV SAFE_TOKEN_JENKINS_PIPELINE=SAFE_TOKEN_777
ENV FAKE_AWS_ACCESS_KEY_ID=SAFE_TOKEN_AWS123
ENV FAKE_AWS_SECRET_ACCESS_KEY=SAFE_TOKEN_AWS456
USER jenkins

# Provide a marker file Jenkins can surface in jobs and the demo can reference.
RUN mkdir -p /var/jenkins_home/demo-fake-secrets && \
    cp /opt/demo-fake-secrets/* /var/jenkins_home/demo-fake-secrets/
