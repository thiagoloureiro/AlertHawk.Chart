# AlertHawk Helm Charts

<p align="center">
  <img src="https://raw.githubusercontent.com/thiagoloureiro/AlertHawk/main/logo.png" alt="AlertHawk" width="120" />
</p>

<p align="center">
  <strong>Self-hosted monitoring, alerting, metrics, and FinOps for Kubernetes</strong>
</p>

<p align="center">
  <a href="https://artifacthub.io/packages/search?repo=alerthawk"><img src="https://img.shields.io/endpoint?url=https://artifacthub.io/badge/repository/alerthawk" alt="Artifact Hub" /></a>
  <a href="https://artifacthub.io/packages/helm/alerthawk/alerthawk"><img src="https://img.shields.io/badge/chart-alerthawk-0F1689?logo=helm&logoColor=white" alt="alerthawk chart" /></a>
  <img src="https://img.shields.io/badge/Helm-3-0F1689?logo=helm&logoColor=white" alt="Helm 3" />
  <img src="https://img.shields.io/badge/Kubernetes-1.24+-326CE5?logo=kubernetes&logoColor=white" alt="Kubernetes" />
  <a href="https://github.com/thiagoloureiro/AlertHawk.Chart/releases"><img src="https://img.shields.io/github/v/release/thiagoloureiro/AlertHawk.Chart?include_prereleases&sort=semver&label=latest%20release" alt="Latest release" /></a>
  <a href="https://github.com/thiagoloureiro/AlertHawk.Chart/stargazers"><img src="https://img.shields.io/github/stars/thiagoloureiro/AlertHawk.Chart?style=flat" alt="GitHub stars" /></a>
  <a href="https://github.com/thiagoloureiro/AlertHawk.Chart/commits"><img src="https://img.shields.io/github/last-commit/thiagoloureiro/AlertHawk.Chart" alt="Last commit" /></a>
  <a href="https://github.com/thiagoloureiro/AlertHawk.Chart/issues"><img src="https://img.shields.io/github/issues/thiagoloureiro/AlertHawk.Chart" alt="Issues" /></a>
</p>

---

## Overview

This repository publishes Helm charts for [AlertHawk](https://github.com/thiagoloureiro/AlertHawk) — a self-hosted monitoring platform. Charts are available on [Artifact Hub](https://artifacthub.io/packages/search?repo=alerthawk) and via the Helm repository below.

| Chart | Description | Latest |
| --- | --- | --- |
| [`alerthawk`](./alerthawk) | Full stack: monitoring, auth, notification, UI, metrics API, FinOps API | [![Version](https://img.shields.io/badge/version-3.3.34-blue)](https://artifacthub.io/packages/helm/alerthawk/alerthawk) |
| [`alerthawk.agent`](./alerthawk.agent) | Monitoring agent only | [![Version](https://img.shields.io/badge/version-3.3.12-blue)](https://artifacthub.io/packages/helm/alerthawk/alerthawk.agent) |
| [`alerthawk-metrics-agent`](./alerthawk.metrics.agent) | Kubernetes metrics collector | [![Version](https://img.shields.io/badge/version-3.3.17-blue)](https://artifacthub.io/packages/helm/alerthawk/alerthawk-metrics-agent) |

## Table of Contents

- [Charts](#charts)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [External Dependencies](#external-dependencies)
- [Configuration](#configuration)
- [Uninstall](#uninstall)
- [Useful Links](#useful-links)

## Charts

### `alerthawk` (full stack)

Deploys the complete AlertHawk platform as Kubernetes Deployments and Services:

| Component | Role |
| --- | --- |
| `alerthawk-monitoring` | Uptime checks and monitor orchestration |
| `alerthawk-auth` | Authentication and user management |
| `alerthawk-notification` | Alert delivery (Slack, push, etc.) |
| `alerthawk-ui` | Web UI |
| `alerthawk-metrics-api` | Metrics ingestion and query API |
| `alerthawk-finops-api` | Azure cost / FinOps analysis |

Optional ClickHouse can be installed as a subchart when `clickhouse.enabled` is `true`.

### `alerthawk.agent`

Lightweight chart that runs only the monitoring agent service — useful when scaling check workers independently of the full stack.

### `alerthawk-metrics-agent`

Collects Kubernetes cluster metrics and sends them to AlertHawk Metrics API.

## Prerequisites

- A Kubernetes cluster (1.24+ recommended)
- [Helm 3.x](https://helm.sh/docs/intro/install/)
- SQL Server (required by most backend services)
- ClickHouse (required by `metrics-api`)
- Optional: Redis, RabbitMQ or Azure Service Bus, Azure AD

## Quick Start

### 1. Add the Helm repository

```bash
helm repo add alerthawk https://thiagoloureiro.github.io/AlertHawk.Chart/
helm repo update
```

### 2. Configure values

Copy and edit the chart values (connection strings, JWT, Azure AD, etc.). See [Configuration](#configuration) and the chart’s `values.yaml`.

```bash
helm show values alerthawk/alerthawk > my-values.yaml
# edit my-values.yaml
```

### 3. Install

**From the Helm repo:**

```bash
helm install alerthawk alerthawk/alerthawk -f my-values.yaml
```

**From a local clone:**

```bash
helm dependency update ./alerthawk
helm install alerthawk ./alerthawk -f my-values.yaml
```

**Agent charts:**

```bash
helm install alerthawk-agent alerthawk/alerthawk.agent -f my-values.yaml
helm install alerthawk-metrics-agent alerthawk/alerthawk-metrics-agent -f my-values.yaml
```

## External Dependencies

### ClickHouse (required for metrics-api)

`alerthawk-metrics-api` needs ClickHouse. It also needs SQL Server (see below).

#### Option 1: Install ClickHouse with this chart (recommended)

Set `clickhouse.enabled: true` in `values.yaml`. ClickHouse is pulled from `https://thiagoloureiro.github.io/clickhouse.chart/`.

```yaml
clickhouse:
  enabled: true
  # Additional ClickHouse configuration can be added here
```

Then set `CLICKHOUSE_CONNECTION_STRING` under `metrics-api` (typically `http://clickhouse:8123/default` when using the subchart).

#### Option 2: External ClickHouse

Set `clickhouse.enabled: false` and install ClickHouse separately:

```bash
helm repo add clickhouse https://thiagoloureiro.github.io/clickhouse.chart/
helm repo update
helm install my-clickhouse clickhouse/clickhouse
```

Point `CLICKHOUSE_CONNECTION_STRING` at that instance.

**Reference:** [ClickHouse chart on Artifact Hub](https://artifacthub.io/packages/helm/clickhouse-alerthawk/clickhouse)

### SQL Server (required for auth, notification, monitoring, metrics-api, and finops-api)

Configure `ConnectionStrings__SqlConnectionString` in each service’s `env` section in `values.yaml`.

### Azure Cost Management (required for finops-api)

`alerthawk-finops-api` reads Azure cost and usage via the Azure Resource Manager API. Configure a dedicated app registration (or service principal) with a client secret under `Azure__*` in `finops-api.env`.

- Use `https://management.azure.com` unless you target another cloud / sovereign region.
- Grant the principal permission to query cost data (commonly **Cost Management Reader** at subscription or management-group scope).

Also configure Azure AD (`AzureAd__*`) if users sign in with SSO, and JWT (`Jwt__*`) so other AlertHawk services can call the FinOps API securely.

#### Optional: AI and scheduled analysis (finops-api)

- **AI integration:** `AI__ApiURl`, `AI__ApiKey`, `AI__ApiKeyHeaderName`
- **Weekly analysis:** `WeeklyAnalysis__Enabled`, `WeeklyAnalysis__DayOfWeekUtc`, `WeeklyAnalysis__HourUtc`, `WeeklyAnalysis__MinuteUtc` (UTC)

### Azure AD SSO (optional)

For SSO on any service, set:

| Variable | Description |
| --- | --- |
| `AzureAd__ClientId` | Application (client) ID |
| `AzureAd__TenantId` | Tenant ID |
| `AzureAd__ClientSecret` | Client secret |
| `AzureAd__Instance` | e.g. `https://login.microsoftonline.com/` |
| `AzureAd__CallbackPath` | OIDC callback path (default: `/signin-oidc`) |

## Configuration

### ClickHouse

- `clickhouse.enabled`: `true` to install the subchart; `false` for an external instance (default: `false`)
- Extra subchart values go under `clickhouse`. See the [ClickHouse chart docs](https://artifacthub.io/packages/helm/clickhouse-alerthawk/clickhouse).

When enabled, set `CLICKHOUSE_CONNECTION_STRING` in `metrics-api.env` (typically `http://clickhouse:8123/default`).

### Environment variables

#### Common

| Variable | Description |
| --- | --- |
| `ASPNETCORE_ENVIRONMENT` | e.g. `Development`, `Production` |
| `Sentry__Enabled` | Enable Sentry (boolean) |
| `Sentry__Dsn` | Sentry DSN |
| `Sentry__Environment` | Sentry environment name |
| `SwaggerUICredentials__username` | Swagger UI username |
| `SwaggerUICredentials__password` | Swagger UI password |
| `Jwt__Key` | JWT signing key |
| `Jwt__Issuers` | JWT issuer(s), comma-separated |
| `Jwt__Audiences` | JWT audience(s), comma-separated |
| `Logging__LogLevel__Default` | Default log level |
| `Logging__LogLevel__Microsoft.IdentityModel.LoggingExtensions.IdentityLoggerAdapter` | Identity Model log level |

#### metrics-api

| Variable | Description |
| --- | --- |
| `CLICKHOUSE_CONNECTION_STRING` | **Required** — ClickHouse connection string |
| `ConnectionStrings__SqlConnectionString` | **Required** — SQL Server connection string |
| `RabbitMq__Host` / `User` / `Pass` | RabbitMQ credentials |
| `QueueType` | e.g. `RABBITMQ`, `SERVICEBUS` |
| `ServiceBus__ConnectionString` | Azure Service Bus connection string |
| `ServiceBus__QueueName` | Queue name (default: `notifications`) |

#### monitoring

| Variable | Description |
| --- | --- |
| `ConnectionStrings__SqlConnectionString` | **Required** — SQL Server connection string |
| `RabbitMq__Host` / `User` / `Pass` | RabbitMQ credentials |
| `CacheSettings__CacheProvider` | e.g. `Redis`, `MemoryCache` |
| `CacheSettings__RedisConnectionString` | Redis connection string |
| `azure_blob_storage_connection_string` | Azure Blob Storage connection string |
| `azure_blob_storage_container_name` | Blob container name |
| `AUTH_API_URL` | Auth API base URL |
| `CACHE_PARALLEL_TASKS` | Parallel cache tasks (default: `10`) |
| `ipgeo_apikey` | IP geolocation API key |
| `enable_location_api` | Enable location API (boolean) |
| `enable_screenshot` | Enable screenshots (boolean) |
| `screenshot_wait_time_ms` | Screenshot wait (default: `2000`) |
| `enable_screenshot_storage_account` | Store screenshots in blob storage (boolean) |
| `Downsampling__Active` | Enable downsampling (boolean) |
| `Downsampling__IntervalInSeconds` | Downsampling interval (default: `60`) |
| `DOTNET_SYSTEM_GLOBALIZATION_INVARIANT` | Globalization invariant mode (boolean) |
| `CHECK_MONITOR_AFTER_CREATION` | Check monitor after creation (boolean) |
| `QueueType` | e.g. `RABBITMQ`, `SERVICEBUS` |
| `ServiceBus__ConnectionString` | Azure Service Bus connection string |
| `ServiceBus__QueueName` | Queue name (default: `notifications`) |

#### auth

| Variable | Description |
| --- | --- |
| `ConnectionStrings__SqlConnectionString` | **Required** — SQL Server connection string |
| `CacheSettings__CacheProvider` | e.g. `MemoryCache`, `Redis` |
| `DownstreamApi__BaseUrl` | Default: `https://graph.microsoft.com/beta` |
| `DownstreamApi__Scopes` | e.g. `User.Read` |
| `smtpHost` / `smtpPort` / `smtpUsername` / `smtpPassword` / `smtpFrom` | SMTP settings |
| `enableSsl` | SMTP SSL (boolean) |
| `MOBILE_API_KEY` | Mobile auth API key |
| `DOTNET_SYSTEM_GLOBALIZATION_INVARIANT` | Globalization invariant mode (boolean) |

#### notification

| Variable | Description |
| --- | --- |
| `ConnectionStrings__SqlConnectionString` | **Required** — SQL Server connection string |
| `RabbitMq__Host` / `User` / `Pass` | RabbitMQ credentials |
| `CacheSettings__CacheProvider` | e.g. `MemoryCache`, `Redis` |
| `slack-webhookurl` | Slack webhook URL |
| `AesKey` / `AesIV` | AES encryption key and IV |
| `AUTH_API_URL` | Auth API base URL |
| `PUSHY_API_KEY` | Pushy API key |
| `DOTNET_SYSTEM_GLOBALIZATION_INVARIANT` | Globalization invariant mode (boolean) |

#### finops-api

| Variable | Description |
| --- | --- |
| `ConnectionStrings__SqlConnectionString` | **Required** — SQL Server connection string |
| `ASPNETCORE_ENVIRONMENT` | e.g. `Development`, `Production` |
| `Sentry__Enabled` / `Sentry__Dsn` / `Sentry__Environment` | Sentry settings |
| `SwaggerUICredentials__username` / `password` | Swagger UI credentials |
| `AzureAd__ClientId` / `TenantId` / `ClientSecret` / `Instance` | Azure AD SSO |
| `Azure__TenantId` | **Required for cost ingestion** — service principal tenant |
| `Azure__ClientId` | **Required for cost ingestion** — application (client) ID |
| `Azure__ClientSecret` | **Required for cost ingestion** — client secret |
| `Jwt__Key` / `Jwt__Issuers` / `Jwt__Audiences` | JWT settings |
| `Logging__LogLevel__Default` | Default log level |
| `Logging__LogLevel__Microsoft.IdentityModel.LoggingExtensions.IdentityLoggerAdapter` | Identity Model log level |
| `ENABLE_LOG_CLEANUP` | Enable log cleanup (boolean) |
| `AI__ApiURl` / `AI__ApiKey` / `AI__ApiKeyHeaderName` | Optional AI integration |
| `WeeklyAnalysis__Enabled` | Enable weekly analysis (boolean) |
| `WeeklyAnalysis__DayOfWeekUtc` | Day of week in UTC (e.g. `Sunday`) |
| `WeeklyAnalysis__HourUtc` / `WeeklyAnalysis__MinuteUtc` | Schedule time in UTC |

## Uninstall

```bash
helm uninstall alerthawk
```

## Useful Links

- [Artifact Hub — AlertHawk charts](https://artifacthub.io/packages/search?repo=alerthawk)
- [alerthawk chart](https://artifacthub.io/packages/helm/alerthawk/alerthawk)
- [ClickHouse subchart](https://artifacthub.io/packages/helm/clickhouse-alerthawk/clickhouse)
- [AlertHawk main repository](https://github.com/thiagoloureiro/AlertHawk)
- Helm repo: `https://thiagoloureiro.github.io/AlertHawk.Chart/`
