# Quick Deployment Guide - Ad-Service Fix

## Overview
This guide provides step-by-step instructions to deploy the IOException fix for the ad-service.

## Prerequisites
- Access to the Kubernetes cluster
- Docker registry credentials
- kubectl configured for the cluster

## Deployment Steps

### Option 1: Using Existing CI/CD Pipeline (Recommended)
If the repository has automated deployment:

1. **Merge the PR** to trigger automated build and deployment
2. **Monitor the pipeline** for successful completion
3. **Verify deployment** using the verification steps below

### Option 2: Manual Deployment

#### Step 1: Build the Docker Image
```bash
cd /path/to/unguard/src/ad-service

# Build the image with the new tag
docker build -t ghcr.io/appsec-ai-initiative-dev/unguard/ad-service:fix-ioexception .

# Tag as latest
docker tag ghcr.io/appsec-ai-initiative-dev/unguard/ad-service:fix-ioexception \
           ghcr.io/appsec-ai-initiative-dev/unguard/ad-service:latest
```

#### Step 2: Push to Registry
```bash
# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Push the images
docker push ghcr.io/appsec-ai-initiative-dev/unguard/ad-service:fix-ioexception
docker push ghcr.io/appsec-ai-initiative-dev/unguard/ad-service:latest
```

#### Step 3: Deploy to Kubernetes
```bash
# Update the deployment to use the new image
kubectl set image deployment/unguard-ad-service \
  ad-service=ghcr.io/appsec-ai-initiative-dev/unguard/ad-service:fix-ioexception \
  -n unguard

# Or restart the deployment to pull latest
kubectl rollout restart deployment/unguard-ad-service -n unguard
```

#### Step 4: Monitor Rollout
```bash
# Watch the rollout status
kubectl rollout status deployment/unguard-ad-service -n unguard

# Verify new pods are running
kubectl get pods -n unguard -l app=ad-service
```

### Option 3: Using Skaffold (If Available)
```bash
cd /path/to/unguard

# Deploy using skaffold
skaffold run -p production
```

## Verification

### 1. Check Pod Status
```bash
kubectl get pods -n unguard -l app=ad-service
# Expected: Running status with recent start time
```

### 2. Check Pod Logs
```bash
kubectl logs -n unguard deployment/unguard-ad-service --tail=100

# Should NOT see IOException errors
# Should see normal startup and request logs
```

### 3. Test the Service
```bash
# Get the service endpoint
kubectl get svc -n unguard unguard-ad-service

# Test the endpoint
curl http://<service-ip>/ad-service/ad

# Expected: 200 OK or empty response (not 500 error)
```

### 4. Monitor in Dynatrace

Query to verify no more IOExceptions:
```dql
fetch logs, from: now() - 1h
| filter contains(k8s.pod.name, "ad-service")
| filter contains(content, "IOException")
| summarize count()
```

Expected result: 0 events

Query to check service health:
```dql
fetch logs, from: now() - 15m
| filter contains(k8s.pod.name, "ad-service")
| filter contains(content, "error") or contains(content, "Error")
| fields timestamp, content
| limit 50
```

Expected result: No IOException, only normal operational logs

### 5. Check Application Health
```bash
# If health check endpoint exists
curl http://<service-ip>/health
curl http://<service-ip>/ready
```

## Rollback Plan

If issues are detected after deployment:

### Quick Rollback
```bash
# Rollback to previous version
kubectl rollout undo deployment/unguard-ad-service -n unguard

# Verify rollback
kubectl rollout status deployment/unguard-ad-service -n unguard
```

### Full Rollback
```bash
# Revert to specific revision
kubectl rollout history deployment/unguard-ad-service -n unguard
kubectl rollout undo deployment/unguard-ad-service --to-revision=<number> -n unguard
```

## Post-Deployment Monitoring

### Monitor for 24-48 Hours

1. **Dynatrace Queries** (Run every 4 hours):
```dql
// Check for any errors
fetch logs, from: now() - 4h
| filter contains(k8s.pod.name, "ad-service")
| filter loglevel == "ERROR" or loglevel == "WARN"
| summarize count(), by: {content}

// Check service availability
fetch dt.entity.service
| filter entity.name contains "ad-service"
| fields id, entity.name
```

2. **Kubernetes Metrics**:
```bash
# Check resource usage
kubectl top pod -n unguard -l app=ad-service

# Check restart count (should be 0)
kubectl get pods -n unguard -l app=ad-service -o wide
```

3. **Application Metrics**:
   - Request count: Should remain stable
   - Error rate: Should drop to ~0%
   - Response time: Should remain consistent

## Success Criteria

✅ New pods deployed successfully  
✅ No IOException in logs for 1 hour  
✅ Service responding to requests  
✅ Error rate < 0.1%  
✅ No pod restarts  
✅ Dynatrace shows no new errors  

## Troubleshooting

### Issue: Pods Not Starting
```bash
# Check pod events
kubectl describe pod -n unguard <pod-name>

# Check logs
kubectl logs -n unguard <pod-name>
```

### Issue: Image Pull Failed
```bash
# Verify image exists
docker pull ghcr.io/appsec-ai-initiative-dev/unguard/ad-service:fix-ioexception

# Check image pull secret
kubectl get secret -n unguard
```

### Issue: Service Still Shows Errors
```bash
# Verify correct image is running
kubectl get pod -n unguard <pod-name> -o jsonpath='{.spec.containers[*].image}'

# Check if old pods still exist
kubectl get pods -n unguard -o wide
```

## Contact Information

For issues or questions:
- Repository: https://github.com/appsec-ai-initiative-dev/unguard
- Issues: Create a GitHub issue with tag "deployment"
- Dynatrace: Monitor dashboards and alerts

---

**Last Updated**: October 15, 2025  
**Related PR**: copilot/fix-environment-down-issue  
**Status**: Ready for deployment
