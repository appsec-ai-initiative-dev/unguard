# Unguard Helm Chart

## Introduction

This chart bootstraps an Unguard deployment on a [Kubernetes](https://kubernetes.io) cluster using the [Helm](https://helm.sh)
package manager.

> **Warning** \
> Unguard is **insecure** by design and a careless installation will leave you exposed to severe security vulnerabilities. Make sure to restrict access and/or run it in a sandboxed environment.

## Prerequisites

- [Kubernetes 1.21+](https://kubernetes.io/)
- [Helm 3.8.0+](https://helm.sh/)

## Installing the Chart

> **Note**: This chart presumes an already running MariaDB database in the cluster. The default naming requirement
> is ```unguard-mariadb```.

To install the chart with the release name `unguard` in a new namespace `unguard` with an `unguard-mariadb` MariaDB instance:

1. Add the bitnami repository for the MariaDB dependency

   ```sh
    helm repo add bitnami https://charts.bitnami.com/bitnami
   ```

2. Install MariaDB

    > **Note:** The default release-name of the database installation is ```unguard-mariadb```.
    If you want to change this you also have to adopt the ```mariaDB.serviceName```value.

    ```sh
    helm install unguard-mariadb bitnami/mariadb --version 11.5.7 --set primary.persistence.enabled=false --wait --namespace unguard --create-namespace
    ```

    > **Note:** \
    The `--wait` flag waits for the installation to be completed \
    `--namespace unguard` specifiers the desired namespace \
    `--create-namespace` creates the namespace if it doesn't exist \
    For more details see the [Helm documentation](https://helm.sh/docs/helm/helm_install/)

3. Install Unguard

   > **Note**:\
   The default configuration is for deployment on a local cluster! \
   To deploy to an EKS cluster append: `--set localDev.enabled=false,aws.enabled=true`

    1. Using the **remote chart** from GitHub

       ```sh
       helm install unguard  oci://ghcr.io/dynatrace-oss/unguard/chart/unguard --wait --namespace unguard --create-namespace
       ```

    2. Using the **local chart**

        ```sh
        helm install unguard ./chart --wait --namespace unguard --create-namespace
        ```

These commands deploy Unguard in the default configuration.

> **Tip**: List all releases using `helm list`

## Uninstalling the Chart

To uninstall/delete the `unguard` deployment:

```sh
helm uninstall unguard -n unguard
```

To also uninstall the MariaDB deployment:

```sh
helm uninstall unguard-mariadb -n unguard
```

The command removes all the Kubernetes components associated with the chart and deletes the release.

## Install a specific version of Unguard

To install Unguard in a specific version provide the `--version` flag with the version you want to install:

```sh
helm install unguard  oci://ghcr.io/dynatrace-oss/unguard/chart/unguard --version 0.24.0
```

## Parameters

### Global parameters

| Name                             | Description                                                               | Default Value     |
|----------------------------------|---------------------------------------------------------------------------|-------------------|
| `localDev.enabled`               | Creates an Ingress and configures it for local (minikube/kind) deployment | `true`            |
| `aws.enabled`                    | Creates an Ingress and configures it for AWS EKS cluster deployment       | `false`           |
| `tracing.enabled`                | Activates tracing in services                                             | `false`           |
| `maliciousLoadGenerator.enabled` | Deploys the malicious load generator                                      | `false`           |
| `mariaDB.serviceName`            | Expected release-name of the MariaDB installation by Unguard              | `unguard-mariadb` |
| `ragService.enabled`             | Deploys the rag service (together with the feedback ingestion service)    | `false`           |
| `ollama.enabled`                 | Deploys an Ollama instance to be used by the rag-service                  | `false`           |
| `buildRunner.enabled`            | Deploys the CI/CD build runner supply chain attack demo                   | `false`           |
| `buildRunner.trigger.schedule`   | CronJob schedule for periodic build-runner exfil triggers                 | `0 */6 * * *`     |
| `shaiHuludTrigger.enabled`       | Deploys the CronJob that triggers the frontend shai-hulud exfil           | `false`           |
| `shaiHuludTrigger.schedule`      | CronJob schedule for periodic frontend exfil triggers                     | `0 */6 * * *`     |
| `attackSimulator.enabled`        | Deploys the CronJob that periodically attacks vulnerable endpoints        | `false`           |
| `attackSimulator.schedule`       | CronJob schedule for the periodic attack burst                            | `0 */2 * * *`     |
| `detectionStream.enabled`        | Deploys the continuous detection-stream generator (Deployment)            | `false`           |
| `detectionStream.minSleep`       | Min seconds of jitter between attack passes                               | `45`              |
| `detectionStream.maxSleep`       | Max seconds of jitter between attack passes                               | `150`             |
| `detectionStream.attackChancePercent` | Percent chance each individual attack fires per pass                 | `70`              |
| `detectionStream.attackerIps`    | Space-separated pool of source IPs spoofed via X-Forwarded-For            | geo-varied pool   |
| `detectionStream.misdirectChancePercent` | Percent chance of a "misdirected" attack (de-prioritize candidate) | `25`            |
| `incidentInjector.enabled`       | Deploys the incident injector (Davis problems ↔ detections)              | `false`           |
| `incidentInjector.rate`          | Concurrent requests per second during a burst                            | `8`               |
| `incidentInjector.durationSeconds` | Length of each malicious / benign burst                                | `120`             |
| `incidentInjector.gapSeconds`    | Quiet gap between bursts                                                  | `300`             |
| `incidentInjector.maliciousSourceIp` | Fixed source IP for the malicious burst (reads as one campaign)      | `185.220.101.47`  |
| `kspmMisconfig.enabled`          | Deploys inert workloads with insecure config for KSPM findings           | `false`           |

Specify each parameter using the `--set key=value[,key=value]` argument to `helm install`. For example,

```sh
helm install unguard oci://ghcr.io/dynatrace-oss/unguard/chart/unguard --set mariaDB.serviceName=mariadb
```

The above command changes the MariaDB installation release-name to `mariadb`.

Alternatively, a YAML file that specifies the values for the parameters can be provided while installing the chart. For example,

```sh
helm install unguard -f aws.yaml oci://ghcr.io/dynatrace-oss/unguard/chart/unguard
```

The above command applies the values from `aws.yaml` which creates and configures an ingress for EKS deployment.

> **Tip**: You can use the default [values.yaml](values.yaml)


## Installation on an AWS EKS cluster

> **Warning** \
> Unguard is **insecure** by design and a careless installation will leave you exposed to severe security vulnerabilities. \
> When installing Unguard with the `aws.enabled=true` value set, an ingress gets created. Please make sure to review its configuration.

> **Note**:\
These steps assume that an AWS Load Balancer Controller is installed. See https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.6/ for more information.

This Chart is prepared to install Unguard on an AWS EKS cluster. \
To install Unguard on an AWS EKS cluster running an AWS load balancer, you can run the following `helm` command:

```sh
helm install unguard oci://ghcr.io/dynatrace-oss/unguard/chart/unguard --set localDev.enabled=false,aws.enabled=true
```

This creates an ingress and adds the following default annotations:

```yaml
kubernetes.io/ingress.class: alb
alb.ingress.kubernetes.io/target-type: ip
alb.ingress.kubernetes.io/scheme: internal
alb.ingress.kubernetes.io/load-balancer-name: "unguard-lb"
```

These annotations can be adjusted by modifying and extending the `aws.yaml` values file and then passing it to the Unguard helm install command like shown bellow.

```sh
helm install unguard -f aws.yaml oci://ghcr.io/dynatrace-oss/unguard/chart/unguard
```

> **Note**:\
Passing the `aws.yaml` values file removes and overrides ALL default annotations.


## Tracing and Jaeger

To enable tracing, provide the YAML file [tracing.yaml](tracing.yaml) during installation. **Unguard is configured for Jaeger tracing.** \
To also install Jaeger tracing follow the [TRACING](../docs/TRACING.md#jaeger-installation-guide) guide.

```sh
helm install unguard oci://ghcr.io/dynatrace-oss/unguard/chart/unguard -f ./chart/tracing.yaml
```

## Supply Chain Attack Demo

Unguard includes a supply chain attack demo that simulates a compromised npm package (`@ctrl/tinycolor`) harvesting secrets and exfiltrating them to an attacker-controlled endpoint. The demo has two scenarios, both triggered periodically via CronJobs:

- **Build runner** (CI/CD): A build worker installs the compromised package, which harvests build secrets from environment variables.
- **Frontend server action** (runtime): A Next.js server action triggers the exfiltration within a traced request context.

Both scenarios generate OpenTelemetry traces that the Dynatrace OneAgent bridge forwards to Grail. See [docs/SUPPLY-CHAIN-DEMO.md](../docs/SUPPLY-CHAIN-DEMO.md) for full details.

To enable both scenarios:

```sh
helm install unguard ./chart \
  --set buildRunner.enabled=true \
  --set shaiHuludTrigger.enabled=true
```

The CronJobs trigger the exfiltration every 6 hours by default. Adjust the schedule via `buildRunner.trigger.schedule` and `shaiHuludTrigger.schedule`.

## Generating a Continuous Stream of Security Detections

Unguard can drive a steady stream of runtime security detections (SQLi, command
injection, SSRF, JNDI/Log4Shell) against its own intentionally vulnerable endpoints.
OneAgent Runtime Application Protection turns each attack into a `DETECTION_FINDING`
(plus a correlated Davis problem), which is useful for demos and for keeping a
security tenant populated with live data.

Two variants are shipped:

| Component | Kind | Cadence | Use when |
|-----------|------|---------|----------|
| `attackSimulator`  | CronJob    | Burst every N hours (default every 2h) | You want an occasional spike of findings. |
| `detectionStream`  | Deployment | Continuous, jittered loop               | You want a *stream* of findings while unguard is up. |

Enable the continuous stream:

```sh
helm upgrade --install unguard oci://ghcr.io/dynatrace-oss/unguard/chart/unguard \
  --set detectionStream.enabled=true
```

`detectionStream` is intentionally a **Deployment, not a CronJob**. Clusters whose
nodegroup is scaled to zero at night/weekends can leave a CronJob accumulating a
backlog of `Pending` jobs that all fire at once when nodes return. A Deployment
instead leaves a single unschedulable pod while the cluster is shrunk and resumes on
its own when it scales back up - no backlog, no thundering herd. Tune the volume and
shape of the stream with `detectionStream.minSleep`, `detectionStream.maxSleep`,
`detectionStream.attackChancePercent` and `detectionStream.attackerUsers`.

### Making the stream richer for triage and correlation

The base stream is enough for "there are detections", but three add-ons make the data
good enough to *drive AI SecOps use cases* (queue-level detection triage, problem ↔
security association, KSPM misconfiguration triage):

- **Attacker-IP diversity + more services.** The stream spoofs `X-Forwarded-For` /
  `X-Real-IP` from `detectionStream.attackerIps` so findings spread across `actor.ips`
  (each persona recurs from its own IP, with occasional distributed spread), and it
  now exercises the .NET (`membership`), Go (`users`), PHP (`like`) and Node
  (`auth/login`) injection paths as well as the Java ones - so detections land on
  several process groups and severities. `detectionStream.misdirectChancePercent`
  fires the occasional attack at a service that is *not* vulnerable to it, giving triage
  a clean de-prioritize / false-positive-looking candidate to discriminate.

- **`incidentInjector` - Davis problems that overlap detections.** The association use
  case joins a Davis problem's affected entities × detections in the problem window. A
  steady stream rarely raises *problems*, so this workload manufactures both halves: a
  **malicious** burst of broken-but-malicious SQLi at one service (RAP attack + 5xx →
  a failure-rate problem on the same entity/window → association *SUSPICIOUS*), and a
  **benign** burst of legitimate timeline reads at a different service (a load problem
  with no detection → association *BENIGN*). Whether Davis opens a problem depends on
  the tenant's anomaly detection; on a quiet tenant, raise sensitivity or set a static
  failure-rate/response-time threshold on the target services, and tune
  `incidentInjector.rate` / `durationSeconds`.

- **`kspmMisconfig` - posture findings.** Inert workloads (they only `sleep`) carrying
  deliberately insecure config - privileged, host namespaces, a read-only host mount,
  added Linux capabilities, no limits - so Kubernetes Security Posture Management emits
  compliance findings. Requires a kubernetes-monitoring ActiveGate with KSPM attached.

```sh
helm upgrade --install unguard oci://ghcr.io/dynatrace-oss/unguard/chart/unguard \
  --set detectionStream.enabled=true \
  --set incidentInjector.enabled=true \
  --set kspmMisconfig.enabled=true
```

## License

Copyright 2023 Dynatrace LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
