# Helm Chart for AlertHawk Metrics Agent

[![Artifact Hub](https://img.shields.io/endpoint?url=https://artifacthub.io/badge/repository/alerthawk)](https://artifacthub.io/packages/search?repo=alerthawk)

This Helm chart deploys the AlertHawk Metrics Agent, which collects Kubernetes metrics and sends them to the AlertHawk Metrics API.

## Component Deployed

- `alerthawk-metrics` - Metrics collection agent that monitors Kubernetes clusters and sends metrics to the AlertHawk Metrics API

## Prerequisites

- Kubernetes cluster (1.19+)
- Helm 3.x installed
- AlertHawk Metrics API service running (for receiving collected metrics)
- ClickHouse database (for the Metrics API to store metrics)

## Installation

1. Add the Helm repository:
   ```bash
   helm repo add alerthawk https://thiagoloureiro.github.io/AlertHawk.Chart/
   helm repo update
   ```

2. Configure your `values.yaml` file with the required environment variables (see Configuration section below).

3. Install the chart:
   ```bash
   helm install alerthawk-metrics-agent alerthawk/alerthawk-metrics-agent -f values.yaml
   ```

   Or install from local chart:
   ```bash
   helm install alerthawk-metrics-agent . -f values.yaml
   ```

## Configuration

### Basic Configuration

- `nameOverride`: Override the default deployment name (default: `alerthawk`)
- `replicas`: Number of pod replicas to run (default: `1`)

### Image Configuration

- `image.repository`: Container image repository (default: `thiagoguaru/alerthawk.metrics`)
- `image.tag`: Container image tag/version (default: `3.1.7`)
- `image.pullPolicy`: Image pull policy - `Always`, `IfNotPresent`, or `Never` (default: `Always`)

### Deployment Strategy

- `strategy.type`: Deployment strategy - `RollingUpdate` or `Recreate` (default: `RollingUpdate`)
- `strategy.rollingUpdate.maxSurge`: Maximum number of pods that can be created over desired (default: `25%`)
- `strategy.rollingUpdate.maxUnavailable`: Maximum number of pods unavailable during update (default: `25%`)

### Service Account

- `serviceAccount.name`: Kubernetes service account name (default: `alerthawk-sa`)

### Security Context

- `securityContext.allowPrivilegeEscalation`: Allow privilege escalation (default: `false`)
- `securityContext.privileged`: Run in privileged mode (default: `false`)
- `securityContext.readOnlyRootFilesystem`: Mount root filesystem as read-only (default: `false`)
- `securityContext.runAsNonRoot`: Run as non-root user (default: `false`)

### Resource Limits

Optional resource limits and requests can be configured:

```yaml
resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 100m
    memory: 128Mi
```

### Environment Variables

The following environment variables are required for the metrics agent to function:

#### Required Environment Variables

- `CLICKHOUSE_CONNECTION_STRING`: **Required** - ClickHouse database connection string
  - Format: `Host=hostname;Port=8123;Database=dbname;Username=user;Password=pass`
  - Example: `Host=clickhouse.clickhouse.svc.cluster.local;Port=8123;Database=default;Username=admin;Password=admin2000`

- `CLUSTER_NAME`: **Required** - Name of the Kubernetes cluster being monitored
  - Example: `aks-tools-01`

- `METRICS_API_URL`: **Required** - Metrics API service URL where collected metrics will be sent
  - Format: `http://service-name.namespace.svc.cluster.local:port`
  - Example: `http://alerthawk-metrics-api.alerthawk.svc.cluster.local:8080`

#### Optional Environment Variables

- `METRICS_COLLECTION_INTERVAL_SECONDS`: Interval in seconds for collecting metrics from Kubernetes (default: `40`)
  - Type: Integer
  - Example: `40`

- `NAMESPACES_TO_WATCH`: Comma-separated list of namespaces to monitor for metrics
  - Default: `alerthawk,clickhouse,cattle-system,security-portal,graylog,ingress-nginx,velero,signoz,umami,akv2k8s,splunk,wiz,sentry`
  - Example: `alerthawk,clickhouse,production,staging`

- `METRICS_API_URL_OLD`: Legacy metrics API URL for backward compatibility (optional)
  - Example: `https://api.monitoring.nam-tools.abb.com/metrics`

## Example values.yaml

```yaml
nameOverride: "alerthawk"
replicas: 1

image:
  repository: thiagoguaru/alerthawk.metrics
  tag: "3.1.7"
  pullPolicy: Always

strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 25%
    maxUnavailable: 25%

serviceAccount:
  name: alerthawk-sa

securityContext:
  allowPrivilegeEscalation: false
  privileged: false
  readOnlyRootFilesystem: false
  runAsNonRoot: false

env:
  CLICKHOUSE_CONNECTION_STRING: "Host=clickhouse.clickhouse.svc.cluster.local;Port=8123;Database=default;Username=admin;Password=admin2000"
  METRICS_COLLECTION_INTERVAL_SECONDS: "40"
  CLUSTER_NAME: "aks-tools-01"
  METRICS_API_URL: "http://alerthawk-metrics-api.alerthawk.svc.cluster.local:8080"
  NAMESPACES_TO_WATCH: "alerthawk,clickhouse,cattle-system,security-portal,graylog,ingress-nginx,velero,signoz,umami,akv2k8s,splunk,wiz,sentry"
```

## Rancher UI Configuration

This chart includes `questions.yml` and `values.schema.json` files that enable a user-friendly form interface in Rancher. When deploying through Rancher, you'll see organized form fields for:

- Basic configuration (replicas, name override)
- Image settings (repository, tag, pull policy)
- Deployment strategy
- Environment variables (all configurable with descriptions)
- Security context settings
- Resource limits and requests

## What the Metrics Agent Does

The AlertHawk Metrics Agent:

1. **Monitors Kubernetes Resources**: Collects metrics from pods, deployments, services, and other resources in specified namespaces
2. **Sends to Metrics API**: Forwards collected metrics to the AlertHawk Metrics API service
3. **Configurable Collection**: Allows you to specify which namespaces to monitor and how frequently to collect metrics
4. **Cluster Identification**: Tags metrics with the cluster name for multi-cluster environments

## Troubleshooting

### Metrics not being collected

- Verify the `METRICS_API_URL` is correct and accessible from the pod
- Check that the service account has proper permissions to read Kubernetes resources
- Ensure the specified namespaces exist and are accessible

### Connection issues

- Verify the `CLICKHOUSE_CONNECTION_STRING` format is correct
- Check network connectivity between the metrics agent and ClickHouse
- Ensure the Metrics API service is running and accessible

### Pod not starting

- Check pod logs: `kubectl logs -n <namespace> <pod-name>`
- Verify all required environment variables are set
- Check service account exists: `kubectl get serviceaccount alerthawk-sa -n <namespace>`

## Uninstallation

To uninstall the chart:

```bash
helm uninstall alerthawk-metrics-agent
```

## Support

For issues and questions, please visit:
- GitHub: https://github.com/thiagoloureiro/AlertHawk.Chart
- Artifact Hub: https://artifacthub.io/packages/search?repo=alerthawk
