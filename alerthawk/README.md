# Helm Chart for AlertHawk Components

[![Artifact Hub](https://img.shields.io/endpoint?url=https://artifacthub.io/badge/repository/alerthawk)](https://artifacthub.io/packages/search?repo=alerthawk)

This Helm chart deploys AlertHawk components as Kubernetes deployments and services.

## Components Deployed

- `alerthawk-monitoring`
- `alerthawk-auth`
- `alerthawk-notification`
- `alerthawk-ui`
- `alerthawk-metrics-api`

## Prerequisites

- Kubernetes cluster
- Helm 3.x installed

### External Dependencies

#### ClickHouse (Required for metrics-api)

The `alerthawk-metrics-api` component requires ClickHouse to be installed. Note that `alerthawk-metrics-api` also requires a SQL Server database (see SQL Server section below). You have two options:

**Option 1: Install ClickHouse as part of this chart (Recommended)**

Set `clickhouse.enabled: true` in your `values.yaml` file. This will automatically install ClickHouse as a subchart from the repository: `https://thiagoloureiro.github.io/clickhouse.chart/`

```yaml
clickhouse:
  enabled: true
  # Additional ClickHouse configuration can be added here
```

After installation, configure the `CLICKHOUSE_CONNECTION_STRING` environment variable in the `metrics-api` section of `values.yaml` to point to the installed ClickHouse instance.

**Option 2: Use an external ClickHouse instance**

Set `clickhouse.enabled: false` in your `values.yaml` file and install ClickHouse separately:

```bash
helm repo add clickhouse https://thiagoloureiro.github.io/clickhouse.chart/
helm repo update
helm install my-clickhouse clickhouse/clickhouse
```

Then configure the `CLICKHOUSE_CONNECTION_STRING` environment variable in the `metrics-api` section of `values.yaml` to point to your external ClickHouse instance.

**Reference:** https://artifacthub.io/packages/helm/clickhouse-alerthawk/clickhouse

#### SQL Server (Required for auth, notification, monitoring, and metrics-api)

The `alerthawk-auth`, `alerthawk-notification`, `alerthawk-monitoring`, and `alerthawk-metrics-api` components require a SQL Server database. Configure the connection string using the `ConnectionStrings__SqlConnectionString` environment variable in the respective service sections of `values.yaml`.

#### Azure AD SSO (Optional)

If Single Sign-On (SSO) with Azure AD is required for any service, configure the following environment variables in the respective service sections:

- `AzureAd__ClientId`: Your Azure AD application (client) ID
- `AzureAd__TenantId`: Your Azure AD tenant ID
- `AzureAd__ClientSecret`: Your Azure AD application client secret
- `AzureAd__Instance`: Azure AD instance URL (e.g., `https://login.microsoftonline.com/`)
- `AzureAd__CallbackPath`: Callback path for OIDC authentication (default: `/signin-oidc`)

## Installation

1. Add the Helm repository:
   ```bash
   helm repo add alerthawk https://thiagoloureiro.github.io/AlertHawk.Chart/
   helm repo update
   ```

2. Configure your `values.yaml` file with the required environment variables (see Configuration section below).

3. Install the chart:
   ```bash
   helm install alerthawk . -f values.yaml
   ```

## Configuration

### ClickHouse Configuration

The chart supports optional ClickHouse installation as a subchart. Configure it in the `clickhouse` section of `values.yaml`:

- `clickhouse.enabled`: Set to `true` to install ClickHouse as a subchart, or `false` to use an external instance (default: `false`)
- Additional ClickHouse subchart values can be configured under the `clickhouse` section. See the [ClickHouse chart documentation](https://artifacthub.io/packages/helm/clickhouse-alerthawk/clickhouse) for available options.

When `clickhouse.enabled` is `true`, configure the `CLICKHOUSE_CONNECTION_STRING` in the `metrics-api.env` section to point to the installed instance (typically `http://clickhouse:8123/default`).

### Environment Variables

#### Common Variables

- `ASPNETCORE_ENVIRONMENT`: ASP.NET Core environment (e.g., `Development`, `Production`)
- `Sentry__Enabled`: Enable/disable Sentry error tracking (boolean)
- `Sentry__Dsn`: Sentry DSN URL for error reporting
- `Sentry__Environment`: Sentry environment name
- `SwaggerUICredentials__username`: Username for Swagger UI access
- `SwaggerUICredentials__password`: Password for Swagger UI access
- `Jwt__Key`: JWT signing key
- `Jwt__Issuers`: JWT issuer(s), comma-separated
- `Jwt__Audiences`: JWT audience(s), comma-separated
- `Logging__LogLevel__Default`: Default log level (e.g., `Warning`, `Information`)
- `Logging__LogLevel__Microsoft.IdentityModel.LoggingExtensions.IdentityLoggerAdapter`: Log level for Identity Model logging

#### metrics-api

- `CLICKHOUSE_CONNECTION_STRING`: **Required** - ClickHouse database connection string
- `ConnectionStrings__SqlConnectionString`: **Required** - SQL Server database connection string
- `RabbitMq__Host`: RabbitMQ host address
- `RabbitMq__User`: RabbitMQ username
- `RabbitMq__Pass`: RabbitMQ password
- `QueueType`: Queue type (e.g., `RABBITMQ`, `SERVICEBUS`)
- `ServiceBus__ConnectionString`: Azure Service Bus connection string
- `ServiceBus__QueueName`: Service Bus queue name (default: `notifications`)

#### monitoring

- `ConnectionStrings__SqlConnectionString`: **Required** - SQL Server connection string
- `RabbitMq__Host`: RabbitMQ host address
- `RabbitMq__User`: RabbitMQ username
- `RabbitMq__Pass`: RabbitMQ password
- `CacheSettings__CacheProvider`: Cache provider type (e.g., `Redis`, `MemoryCache`)
- `CacheSettings__RedisConnectionString`: Redis connection string (if using Redis cache)
- `azure_blob_storage_connection_string`: Azure Blob Storage connection string
- `azure_blob_storage_container_name`: Azure Blob Storage container name
- `AUTH_API_URL`: URL address of the authentication API
- `CACHE_PARALLEL_TASKS`: Number of parallel cache tasks (default: 10)
- `ipgeo_apikey`: API key for IP geolocation service
- `enable_location_api`: Enable/disable location API (boolean)
- `enable_screenshot`: Enable/disable screenshot functionality (boolean)
- `screenshot_wait_time_ms`: Screenshot wait time in milliseconds (default: 2000)
- `enable_screenshot_storage_account`: Enable/disable screenshot storage account (boolean)
- `Downsampling__Active`: Enable/disable downsampling (boolean)
- `Downsampling__IntervalInSeconds`: Downsampling interval in seconds (default: 60)
- `DOTNET_SYSTEM_GLOBALIZATION_INVARIANT`: Disable globalization invariant mode (boolean)
- `CHECK_MONITOR_AFTER_CREATION`: Check monitor after creation (boolean)
- `QueueType`: Queue type (e.g., `RABBITMQ`, `SERVICEBUS`)
- `ServiceBus__ConnectionString`: Azure Service Bus connection string
- `ServiceBus__QueueName`: Service Bus queue name (default: `notifications`)

#### auth

- `ConnectionStrings__SqlConnectionString`: **Required** - SQL Server connection string
- `CacheSettings__CacheProvider`: Cache provider type (e.g., `MemoryCache`, `Redis`)
- `DownstreamApi__BaseUrl`: Downstream API base URL (default: `https://graph.microsoft.com/beta`)
- `DownstreamApi__Scopes`: Downstream API scopes (e.g., `User.Read`)
- `smtpHost`: SMTP server host
- `smtpPort`: SMTP server port
- `smtpUsername`: SMTP username
- `smtpPassword`: SMTP password
- `smtpFrom`: SMTP sender email address
- `enableSsl`: Enable SSL for SMTP (boolean)
- `MOBILE_API_KEY`: API key for mobile authentication
- `DOTNET_SYSTEM_GLOBALIZATION_INVARIANT`: Disable globalization invariant mode (boolean)

#### notification

- `ConnectionStrings__SqlConnectionString`: **Required** - SQL Server connection string
- `RabbitMq__Host`: RabbitMQ host address
- `RabbitMq__User`: RabbitMQ username
- `RabbitMq__Pass`: RabbitMQ password
- `CacheSettings__CacheProvider`: Cache provider type (e.g., `MemoryCache`, `Redis`)
- `slack-webhookurl`: Slack webhook URL for notifications
- `AesKey`: AES encryption key
- `AesIV`: AES initialization vector
- `AUTH_API_URL`: URL address of the authentication API
- `PUSHY_API_KEY`: Pushy API key for push notifications
- `DOTNET_SYSTEM_GLOBALIZATION_INVARIANT`: Disable globalization invariant mode (boolean)
