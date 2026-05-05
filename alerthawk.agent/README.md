# Helm Chart for AlertHawk Agent (Monitoring Service)

[![Artifact Hub](https://img.shields.io/endpoint?url=https://artifacthub.io/badge/repository/alerthawk)](https://artifacthub.io/packages/search?repo=alerthawk)

This Helm chart deploys the **AlertHawk Monitoring Agent** (the `monitoring` service only).

## What this chart is for

Use `alerthawk.agent` when you want to run the monitoring worker/agent **close to the infrastructure you’re monitoring**.

Common use cases:

- Run the agent in an **on‑prem** Kubernetes cluster to monitor internal services/endpoints
- Run the agent in a **dedicated infra/edge** cluster with network access to restricted targets
- Run multiple agents in different regions / networks to collect checks from each location

This chart does **not** deploy the full AlertHawk stack (auth, notification, UI, APIs). It deploys only the monitoring component.

## Component deployed

- `*-monitoring` - AlertHawk Monitoring service/agent

## Prerequisites

- Kubernetes cluster
- Helm 3.x installed
- Connectivity from the agent to required external dependencies (see below)

### External dependencies

The monitoring agent expects the same backend dependencies as the `monitoring` component in the main `alerthawk` chart:

- **SQL Server**: configure `ConnectionStrings__SqlConnectionString`
- **Queue**: configure RabbitMQ (`RabbitMq__*`) or Azure Service Bus (`ServiceBus__*`) and `QueueType`
- **Auth API**: configure `AUTH_API_URL`
- Optional: Redis cache, Azure Blob Storage, Sentry, etc. (via `monitoring.env`)

## Installation

1. Add the Helm repository:

```bash
helm repo add alerthawk https://thiagoloureiro.github.io/AlertHawk.Chart/
helm repo update
```

2. Install the chart:

```bash
helm install alerthawk-agent alerthawk/alerthawk.agent -f values.yaml
```

Or install from local chart:

```bash
helm install alerthawk-agent . -f values.yaml
```

## Configuration

Most configuration is done via `monitoring.env` in `values.yaml`.

### Agent-specific settings

- `DISABLE_MASTER`: defaults to `true` (set to `false` only if you intentionally want this agent to act as “master” in your topology)
- `monitor_region`: defaults to `7` (use different values per network/region to identify where checks run)

### Example values.yaml

```yaml
image:
  monitoring: thiagoguaru/alerthawk.monitoring:3.1.23

monitoring:
  replicas: 1
  env:
    ConnectionStrings__SqlConnectionString: "Server=sql;Database=AlertHawk;User Id=...;Password=...;"
    QueueType: "RABBITMQ"
    RabbitMq__Host: "rabbitmq"
    RabbitMq__User: "user"
    RabbitMq__Pass: "pass"
    AUTH_API_URL: "http://alerthawk-auth.alerthawk.svc.cluster.local:8080"

    # Agent defaults
    DISABLE_MASTER: true
    monitor_region: 7
```

## Uninstallation

```bash
helm uninstall alerthawk-agent
```
