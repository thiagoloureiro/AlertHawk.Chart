# Helm Chart for AlertHawk Components

This Helm chart deploys AlertHawk components as Kubernetes deployments and services.

## Components Deployed

- `alerthawk-monitoring`
- `alerthawk-auth`
- `alerthawk-notification`
- `alerthawk-ui`

## Prerequisites

- Kubernetes cluster
- Helm 3.x installed

## Installation

1. Add the Helm repository:
   ```bash
   helm repo add alerthawk https://thiagoloureiro.github.io/AlertHawk.Chart/
   helm repo update
