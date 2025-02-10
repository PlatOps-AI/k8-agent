# K8s Agent

A lightweight REST API wrapper for kubectl that enables secure, programmatic interaction with Kubernetes clusters. This agent provides a simple HTTP interface to execute kubectl commands while maintaining security through RBAC policies and input validation.

## Core Installation

The K8s Agent can be installed on any Kubernetes cluster. Here's how to set it up:

### Prerequisites
- A running Kubernetes cluster
- `kubectl` configured to access your cluster
- Appropriate permissions to create RBAC resources

### Installation Steps

1. **Set up RBAC**
   First, create the necessary service account and RBAC permissions:
   ```bash
   kubectl apply -f example/rbac.yaml
   ```
   This creates:
   - A `k8s-agent` service account
   - A `pod-replica-viewer` ClusterRole with necessary permissions
   - A ClusterRoleBinding connecting the service account to the role

2. **Deploy the Agent**
   Deploy the K8s Agent and its service:
   ```bash
   kubectl apply -f example/k8s-agent.yaml
   ```

### Configuration Notes

- The agent runs as a deployment with the `k8s-agent` service account
- By default, it exposes port 3000 internally
- The service is configured as LoadBalancer type, but you can modify this based on your needs:
  - For internal access only: Change to `ClusterIP`
  - For NodePort access: Change to `NodePort`
  - For cloud providers: Keep `LoadBalancer`
  - For Ingress: Add appropriate ingress rules

## Sample Playground Setup

The following section describes how to set up a sample testing environment using Istio. This is optional and purely for testing purposes.

### Step 1: Download and install Istio
```bash
# Download Istio
curl -L https://istio.io/downloadIstio | sh -
cd istio-1.24.2

# Create the istio-system namespace first
kubectl create namespace istio-system

# Install Istio with demo profile (includes ingress gateway)
./bin/istioctl install --set profile=demo
```

### Step 2: Deploy the sample app
```bash
# Enable Istio injection for the default namespace
kubectl label namespace default istio-injection=enabled

# Deploy the sample application
kubectl apply -f example/
# Deploy telemetry configurations
kubectl apply -f example/telemetry/
```

## Load Testing

### Step 3: Simulate Traffic

#### Option 1: Single Run
```bash
# Get the Fortio pod name
export FORTIO_POD=$(kubectl get pods -l app=fortio -o jsonpath='{.items[0].metadata.name}')

# Run load test once
kubectl exec -it $FORTIO_POD -- fortio load -c 10 -qps 1000 -t 30s http://productpage:9080/productpage
```

#### Option 2: Continuous Background Load
```bash
# Apply the continuous load CronJob
kubectl apply -f example/cronjobs/

# To check the jobs
kubectl get cronjobs
kubectl get jobs

# To stop the load testing
kubectl delete -f example/cronjob/continuous-load.yaml
```

> **Note:** The CronJob runs every 5 minutes with the following parameters:
> - `-c 3`: 3 concurrent connections
> - `-qps 10`: 10 queries per second
> - `-t 4m`: Runs for 4 minutes (leaving 1 minute gap before next run)

## Monitoring

### Step 4: Prometheus Monitoring Queries

Access the Prometheus UI to monitor your system using these queries:

<details>
<summary>Basic Service Metrics</summary>

```promql
# Request Rate (QPS)
sum(rate(istio_requests_total{destination_service="productpage.default.svc.cluster.local"}[1m]))

# Error Rate
sum(rate(istio_requests_total{destination_service="productpage.default.svc.cluster.local",response_code=~"5.*|4.*"}[1m]))

# Success Rate (percentage)
sum(rate(istio_requests_total{destination_service="productpage.default.svc.cluster.local",response_code="200"}[1m])) / 
sum(rate(istio_requests_total{destination_service="productpage.default.svc.cluster.local"}[1m])) * 100
```
</details>

<details>
<summary>Latency Metrics</summary>

```promql
# Latency Percentiles (P50, P90, P95, P99)
histogram_quantile(0.50, sum(rate(istio_request_duration_milliseconds_bucket{}[5m])) by (destination_service, le))
histogram_quantile(0.90, sum(rate(istio_request_duration_milliseconds_bucket{}[5m])) by (destination_service, le))
histogram_quantile(0.95, sum(rate(istio_request_duration_milliseconds_bucket{}[5m])) by (destination_service, le))
histogram_quantile(0.99, sum(rate(istio_request_duration_milliseconds_bucket{}[5m])) by (destination_service, le))
```
</details>

<details>
<summary>Resource Utilization</summary>

```promql
# Memory Usage
container_memory_working_set_bytes{pod=~"productpage.*"}

# CPU Usage
rate(container_cpu_usage_seconds_total{pod=~"productpage.*"}[1m])

# Container Restarts
sum(kube_pod_container_status_restarts_total{namespace="default"}) by (pod)
```
</details>

<details>
<summary>Network and Traffic</summary>

```promql
# Network Traffic
sum(rate(istio_request_bytes_sum{destination_service="productpage.default.svc.cluster.local"}[1m])) # Incoming
sum(rate(istio_response_bytes_sum{destination_service="productpage.default.svc.cluster.local"}[1m])) # Outgoing

# TCP Connections
sum(irate(istio_tcp_connections_opened_total[5m])) by (destination_service)
sum(irate(istio_tcp_connections_closed_total[5m])) by (destination_service)
```
</details>

<details>
<summary>Service Mesh Insights</summary>

```promql
# Service Dependencies
sum(rate(istio_requests_total{reporter="source"}[5m])) by (source_workload, destination_service)

# Circuit Breaking Events
sum(rate(istio_requests_total{response_flags="UO"}[5m])) # Upstream overflow
sum(rate(istio_requests_total{response_flags="UL"}[5m])) # Upstream connection limit

# Retry Metrics
sum(rate(istio_requests_total{response_flags=~"RX|RR"}[5m])) by (destination_service)
```
</details>

> **Note:** Adjust the time window (e.g., [1m], [5m]) based on your monitoring needs. Shorter windows show recent trends, while longer windows show longer-term patterns.