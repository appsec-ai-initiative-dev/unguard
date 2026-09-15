# Deploying Unguard to Amazon EKS

This directory contains the deployment automation and documentation for running **Unguard** on an Amazon EKS cluster.

---

## 1. EKS Cluster Prerequisites

Before deploying Unguard, ensure your target EKS cluster meets the following requirements:

### Kubernetes Version
* **Supported**: Kubernetes 1.28 through 1.33+.

### Node Capacity & Sizing
Unguard is a polyglot microservice application consisting of ~15 services, an ephemeral MariaDB instance, and optional security demo generators:
* **Standard / AppSec Demo deployment** (`enable_ai_services: false`):
  * **Minimum**: 2 worker nodes with **4 vCPU / 16 GiB RAM** each (e.g. `t3.xlarge` or `t3a.xlarge`).
  * **Max Pods / IP Allocation**: Ensure your subnets and node types support at least 45–55 pods total across the cluster.
* **Full AI Services deployment** (`enable_ai_services: true` — Ollama + RAG):
  * Requires additional high-memory or GPU-enabled nodes (e.g. `g4dn.xlarge` or `m5.2xlarge`) to run LLM models without pod evictions.

### Network & Outbound Egress
* Worker nodes must have outbound internet connectivity (via NAT Gateway or public subnet with IGW) to:
  * Pull container images from **GitHub Container Registry** (`ghcr.io/dynatrace-oss/unguard/*`).
  * Pull helper images from Docker Hub (`curlimages/curl`, `bitnamilegacy/mariadb`, `busybox`).
  * Download Helm charts from `charts.bitnami.com` and `aws.github.io/eks-charts`.
  * Send telemetry to your Dynatrace tenant (if monitored).

### Storage
* **Default**: Unguard runs with ephemeral MariaDB (`primary.persistence.enabled=false`), which requires only local node storage (`emptyDir`).
* **Persistent**: If MariaDB persistence is enabled, the cluster must have the **AWS EBS CSI Driver** add-on installed and configured with a default `StorageClass` (e.g. `gp3`).

### Ingress & Load Balancing
* **ClusterIP (Default & Recommended for Demos)**:
  * Leaves `unguard-envoy-proxy` as an internal `ClusterIP` service.
  * Security generators (`detectionStream`, `incidentInjector`, `userSimulator`) generate and send traffic directly inside the cluster network.
  * No external Load Balancer or AWS resources are provisioned.
* **LoadBalancer (External Access)**:
  * If `service_type: LoadBalancer` is selected, the **AWS Load Balancer Controller** must be installed in `kube-system` with an associated IAM Role for Service Accounts (IRSA).
  * Automatically provisions an AWS Network Load Balancer (NLB).

### EKS Access & IAM
* The deployment identity (GitHub Actions role or engineer) only requires permissions to manage resources inside the deployment namespace:
  * Scope: **`AmazonEKSAdminPolicy`** scoped strictly to the target namespace (`type=namespace,namespaces=<namespace>`).
  * **No `ClusterAdmin` permissions**: The workflow does not require cluster-wide administrative privileges and cannot access `kube-system` or other namespaces.
  * Authentication mode on the cluster must be `API` or `API_AND_CONFIG_MAP`.

### Observability (Dynatrace OneAgent / DynaKube)
* To turn simulated attacks into runtime Application Protection (RAP) detections:
  1. Install the Dynatrace Operator on the cluster.
  2. Apply a `DynaKube` custom resource configured for cloud-native full-stack injection (see example in `dynakube-uan9847d.yaml`).
  3. Ensure **Runtime Application Protection** is enabled for the target host group in your Dynatrace tenant.

---

## 2. Deploying via GitHub Actions (`deploy-eks.yml`)

The repository includes a generic deployment workflow located at `.github/workflows/deploy-eks.yml`.

### Key Features
* **Environment-Driven / Multi-Account**: Target cluster and credentials are bound to a GitHub Environment, avoiding hardcoded AWS accounts or VPCs.
* **Local Chart Source**: Deploys the repository's `./chart` directory directly, including all current detection stream and incident injector templates.
* **Resource Guardrails**: Disables high-memory AI services by default (`enable_ai_services: false`) to avoid exhausting cluster nodes.
* **Image Tag Overrides**: Can deploy newly built CI images on the fly via `image_tag` without modifying `values.yaml` in git.

### Step 1: Onboard an AWS Account (Run Once)
Deploy the CloudFormation template `github-deploy-role.cfn.yaml` in the target AWS account:

```sh
aws cloudformation deploy \
  --template-file ops/eks/github-deploy-role.cfn.yaml \
  --stack-name unguard-github-deploy \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1 \
  --parameter-overrides ClusterNamePattern=appsec-ai-test
```

*Pass `CreateOIDCProvider=No` if `token.actions.githubusercontent.com` already exists in that account.*

### Step 2: Configure the GitHub Environment
In your GitHub repository settings, create an Environment (e.g. `appsec-ai-test`) and configure:

| Kind | Name | Value / Description |
|---|---|---|
| **Secret** | `AWS_DEPLOY_ROLE_ARN` | The `RoleArn` output from the CloudFormation stack |
| **Variable** | `EKS_CLUSTER_NAME` | Name of the target EKS cluster (e.g. `appsec-ai-test`) |
| **Variable** | `AWS_REGION` | AWS region of the cluster (e.g. `us-east-1`) |
| **Variable** | `LB_SCHEME` | *(Optional)* Set to `internal` or `internet-facing` (default `internet-facing`) |

> **Security Note:** Add **Required Reviewers** to any non-sandbox environment. The role is constrained by IAM to only manage workloads in the target namespace and cannot escalate to cluster-admin.

### Step 3: Trigger Deployment
Go to GitHub **Actions** -> **Deploy to EKS** -> **Run workflow**:
1. Select the target **Environment** (e.g. `appsec-ai-test`).
2. Optionally override the `image_tag`, `k8s_namespace`, or toggle demo generators.

---

## 3. Manual Deployment via Helm

If deploying manually from a workstation or jump host with `kubectl` and `helm` configured:

```sh
# 1. Update kubeconfig for the target cluster
aws eks update-kubeconfig --name <cluster-name> --region <region>

# 2. Deploy MariaDB prerequisite
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm upgrade --install unguard-mariadb bitnami/mariadb \
  --namespace unguard --create-namespace \
  --version 11.5.7 \
  --set primary.persistence.enabled=false \
  --set image.repository=bitnamilegacy/mariadb \
  --wait --timeout 5m

# 3. Deploy Unguard from local chart
helm upgrade --install unguard ./chart \
  --namespace unguard --create-namespace \
  --set localDev.enabled=false \
  --set envoyProxy.service.type=ClusterIP \
  --set ollama.enabled=false \
  --set ragService.enabled=false \
  --set detectionStream.enabled=true \
  --set incidentInjector.enabled=true \
  --set kspmMisconfig.enabled=true \
  --wait --timeout 10m
```

---

## 4. Verifying the Deployment

Check that all Unguard pods are in `Running` status:

```sh
kubectl get pods -n unguard -o wide
```

Watch the detection stream generator generating attacks:

```sh
kubectl logs -n unguard -l app.kubernetes.io/name=detection-stream -f
```

In Dynatrace (uan tenant), query detection findings:

```dql
fetch security.events, from:now()-30m
| filter event.kind == "SECURITY_EVENT" and event.type == "DETECTION_FINDING"
| summarize count(), by:{finding.type}
```
