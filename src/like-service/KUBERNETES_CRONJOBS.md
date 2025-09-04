# Kubernetes CronJob Alternative for Agent Scheduling

This file provides an alternative to Laravel's built-in scheduler using Kubernetes CronJobs.
This approach allows for more granular control and better resource management in a Kubernetes environment.

## CronJob Configurations

### Monitor Agent (Every Minute)

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: unguard-agent-monitor
  labels:
    app.kubernetes.io/name: like-service-agent
    app.kubernetes.io/part-of: unguard
    app.kubernetes.io/component: monitor
spec:
  schedule: "* * * * *"  # Every minute
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: agent-monitor
            image: unguard/like-service:latest
            command: ["php", "artisan", "agent:run", "--task=monitor"]
            env:
            - name: DB_HOST
              value: "unguard-mariadb"
            - name: DB_DATABASE
              value: "unguard"
            - name: DB_USERNAME
              value: "unguard"
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: unguard-mariadb
                  key: mariadb-password
          restartPolicy: OnFailure
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
```

### Cleanup Agent (Every 5 Minutes)

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: unguard-agent-cleanup
  labels:
    app.kubernetes.io/name: like-service-agent
    app.kubernetes.io/part-of: unguard
    app.kubernetes.io/component: cleanup
spec:
  schedule: "*/5 * * * *"  # Every 5 minutes
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: agent-cleanup
            image: unguard/like-service:latest
            command: ["php", "artisan", "agent:run", "--task=cleanup"]
            env:
            - name: DB_HOST
              value: "unguard-mariadb"
            - name: DB_DATABASE
              value: "unguard"
            - name: DB_USERNAME
              value: "unguard"
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: unguard-mariadb
                  key: mariadb-password
          restartPolicy: OnFailure
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
```

### Backup Agent (Every Hour)

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: unguard-agent-backup
  labels:
    app.kubernetes.io/name: like-service-agent
    app.kubernetes.io/part-of: unguard
    app.kubernetes.io/component: backup
spec:
  schedule: "0 * * * *"  # Every hour
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: agent-backup
            image: unguard/like-service:latest
            command: ["php", "artisan", "agent:run", "--task=backup"]
            env:
            - name: DB_HOST
              value: "unguard-mariadb"
            - name: DB_DATABASE
              value: "unguard"
            - name: DB_USERNAME
              value: "unguard"
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: unguard-mariadb
                  key: mariadb-password
          restartPolicy: OnFailure
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
```

## Deployment Instructions

1. Apply the CronJob configurations:
```bash
kubectl apply -f agent-cronjobs.yaml -n unguard
```

2. Verify CronJobs are created:
```bash
kubectl get cronjobs -n unguard
```

3. Monitor job execution:
```bash
kubectl get jobs -n unguard
kubectl logs -l app.kubernetes.io/component=monitor -n unguard
```

## Benefits of Kubernetes CronJobs vs Laravel Scheduler

### Kubernetes CronJobs:
- Better resource isolation
- Independent scaling and monitoring
- Built-in job history and retry logic
- Easier to monitor and debug
- Can use different resource limits per job type

### Laravel Scheduler:
- Simpler setup and configuration
- Single point of management
- Shared application context
- Lower resource overhead
- Better for simple use cases

Choose the approach that best fits your operational requirements and infrastructure setup.