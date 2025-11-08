# Load Generator Dashboard System

Complete solution for dynamically controlling Locust load generator with multiple load shape patterns through a web UI.

## Overview

This system extends the microservices-demo load generator with:
- **5 load shape patterns** (Cyclic, Stages, Spike, Sinusoidal, Step)
- **Configurable noise** (0-100%) for realistic traffic randomness
- **Web dashboard** for visual configuration
- **REST API** for Kubernetes integration
- **Automatic pod restart** on configuration changes

## Architecture

```
┌─────────────────┐      ┌──────────────────────┐      ┌─────────────────┐
│                 │      │                      │      │                 │
│  Dashboard UI   │─────>│  Controller API      │─────>│  Load Generator │
│  (React + nginx)│      │  (Flask + K8s client)│      │  (Locust)       │
│                 │      │                      │      │                 │
└─────────────────┘      └──────────────────────┘      └─────────────────┘
        │                         │                             │
        │                         │                             │
        v                         v                             v
  Static Frontend          Kubernetes API               Frontend Service
  Port 80                  Patches Deployment           (e-commerce app)
                           Triggers Restart
```

### Components

1. **Load Generator** (`src/loadgenerator/`)
   - Extended Locust with 5 LoadTestShape classes
   - Configurable via environment variables
   - Dynamic shape selection

2. **Controller API** (`src/loadgen-controller/`)
   - Flask REST API
   - Kubernetes Python client
   - RBAC-secured deployment management

3. **Dashboard UI** (`src/loadgen-dashboard/`)
   - React 18 single-page application
   - SYDA UI design system (dark theme)
   - Real-time configuration updates

## Load Shape Patterns

| Pattern | Description | Use Case |
|---------|-------------|----------|
| **Cyclic Ramp** | Triangular wave with configurable plateaus | Periodic traffic, oscillating load |
| **Stages** | K6-style multi-phase testing | Complex scenarios, realistic business cycles |
| **Spike** | Sudden traffic surge and recovery | Resilience testing, Black Friday simulation |
| **Sinusoidal** | Smooth sine wave oscillation | Day/night patterns, natural variations |
| **Step Load** | Incremental user increases | Capacity planning, threshold identification |

All patterns support **configurable noise** (0-100%) to add gaussian randomness to user counts.

## Quick Start

### 1. Prerequisites

- Kubernetes cluster (minikube, kind, or cloud)
- kubectl configured
- Docker for building images (optional if using pre-built images)

### 2. Deploy Everything

```bash
# Apply all manifests
kubectl apply -k kustomize/base/

# Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app=loadgen-dashboard --timeout=120s
kubectl wait --for=condition=ready pod -l app=loadgen-controller --timeout=120s
kubectl wait --for=condition=ready pod -l app=loadgenerator --timeout=120s
```

### 3. Access Dashboard

```bash
# Get dashboard external IP
kubectl get svc loadgen-dashboard

# Or use port-forward for local access
kubectl port-forward svc/loadgen-dashboard 8081:80
```

Open browser to http://localhost:8081

### 4. Configure Load

1. Select a load shape pattern
2. Adjust parameters (min/max users, duration, etc.)
3. Set noise level (0-100%)
4. Click "Apply Configuration & Restart"
5. Watch your autoscaler respond!

## Configuration Examples

### Example 1: Spike Test

Simulates a traffic spike at 3 minutes:

```yaml
LOAD_SHAPE_TYPE: "spike"
SPIKE_NORMAL_USERS: "10"
SPIKE_MAX_USERS: "200"
SPIKE_START_SEC: "180"
SPIKE_DURATION_SEC: "60"
SPIKE_TOTAL_DURATION_SEC: "600"
NOISE_PERCENT: "5"
```

### Example 2: Daily Pattern (Sinusoidal)

Simulates 12-hour day/night cycle:

```yaml
LOAD_SHAPE_TYPE: "sinusoidal"
SINE_MIN_USERS: "20"
SINE_MAX_USERS: "150"
SINE_PERIOD_SEC: "43200"  # 12 hours
SINE_DURATION_SEC: "0"     # Infinite
NOISE_PERCENT: "10"
```

### Example 3: Complex Stages

Multi-phase test scenario:

```yaml
LOAD_SHAPE_TYPE: "stages"
STAGES_JSON: |
  [
    {"duration": 120, "users": 10, "spawn_rate": 5},
    {"duration": 300, "users": 50, "spawn_rate": 10},
    {"duration": 600, "users": 150, "spawn_rate": 20},
    {"duration": 900, "users": 100, "spawn_rate": 10},
    {"duration": 1200, "users": 10, "spawn_rate": 5}
  ]
NOISE_PERCENT: "8"
```

## Building Images

### Load Generator

```bash
cd src/loadgenerator
docker build -t YOUR_REGISTRY/loadgenerator:v1.0 .
docker push YOUR_REGISTRY/loadgenerator:v1.0

# Update kustomize/base/loadgenerator.yaml with new image
```

### Controller

```bash
cd src/loadgen-controller
docker build -t YOUR_REGISTRY/loadgen-controller:v1.0 .
docker push YOUR_REGISTRY/loadgen-controller:v1.0

# Update kustomize/base/loadgen-controller.yaml with new image
```

### Dashboard

```bash
cd src/loadgen-dashboard
docker build -t YOUR_REGISTRY/loadgen-dashboard:v1.0 .
docker push YOUR_REGISTRY/loadgen-dashboard:v1.0

# Update kustomize/base/loadgen-dashboard.yaml with new image
```

## Development

### Local Development Setup

#### Controller API

```bash
cd src/loadgen-controller
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

#### Dashboard

```bash
cd src/loadgen-dashboard
npm install
export REACT_APP_API_URL=http://localhost:8080
npm start
```

#### Load Generator

```bash
cd src/loadgenerator
pip install -r requirements.txt

# Test shapes locally
export LOAD_SHAPE_TYPE=spike
export SPIKE_NORMAL_USERS=5
export SPIKE_MAX_USERS=50
export NOISE_PERCENT=10

locust -f locustfile.py --headless --host=http://frontend:80
```

## Security

### RBAC Permissions

The controller service account has minimal permissions:

```yaml
rules:
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "patch", "update"]
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]
```

### Container Security

- All containers run as non-root users
- Read-only root filesystems where possible
- No privileged containers
- Capabilities dropped

### Network Security

- Controller API is ClusterIP (internal only by default)
- Dashboard can be LoadBalancer or Ingress with TLS
- Consider adding authentication for production use

## Monitoring

### View Load Generator Logs

```bash
kubectl logs -l app=loadgenerator -f
```

### Check Controller API

```bash
kubectl logs -l app=loadgen-controller -f
```

### Monitor Configuration Changes

```bash
# Watch deployment annotations
kubectl get deployment loadgenerator -o jsonpath='{.spec.template.metadata.annotations}' | jq
```

### View Current Config

```bash
# Via API
kubectl exec -it deploy/loadgen-controller -- curl localhost:8080/api/config | jq

# Via environment variables
kubectl get deployment loadgenerator -o jsonpath='{.spec.template.spec.containers[0].env}' | jq
```

## Troubleshooting

### Pod not restarting after config change

```bash
# Check controller logs
kubectl logs -l app=loadgen-controller --tail=50

# Manually trigger restart
kubectl exec -it deploy/loadgen-controller -- \
  curl -X POST localhost:8080/api/restart
```

### Dashboard shows connection error

```bash
# Verify services
kubectl get svc loadgen-controller loadgen-dashboard

# Test API connectivity from dashboard pod
kubectl exec -it deploy/loadgen-dashboard -- \
  wget -O- http://loadgen-controller:8080/health
```

### Shape not applying correctly

```bash
# Check load generator logs for shape initialization
kubectl logs -l app=loadgenerator | grep "Using load shape"

# Verify environment variables
kubectl get deployment loadgenerator \
  -o jsonpath='{.spec.template.spec.containers[0].env}' | jq
```

### RBAC permission denied

```bash
# Verify role binding
kubectl get rolebinding loadgen-controller -o yaml

# Test permissions
kubectl auth can-i patch deployment/loadgenerator \
  --as=system:serviceaccount:default:loadgen-controller
```

## Demo Script

Perfect for showing autoscaler adaptation:

1. **Baseline**: Start with `cyclic` shape, low noise (0-5%)
2. **Spike Test**: Switch to `spike` shape to trigger autoscaler scale-up
3. **Steady State**: Switch to `stages` with gradual ramp to show scale-down
4. **Realistic Load**: Enable `sinusoidal` with 10-15% noise for natural patterns

## File Structure

```
microservices-demo/
├── src/
│   ├── loadgenerator/          # Extended Locust load generator
│   │   ├── locustfile.py       # 5 load shapes + noise support
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── README.md
│   ├── loadgen-controller/     # Flask API controller
│   │   ├── app.py              # REST API + K8s client
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── README.md
│   └── loadgen-dashboard/      # React web UI
│       ├── src/
│       │   ├── App.js          # Main app component
│       │   ├── components/     # React components
│       │   └── utils/          # API client
│       ├── Dockerfile
│       ├── nginx.conf
│       ├── package.json
│       └── README.md
└── kustomize/base/
    ├── loadgenerator.yaml      # Updated with LOAD_SHAPE_TYPE
    ├── loadgen-controller.yaml # Controller deployment + RBAC
    └── loadgen-dashboard.yaml  # Dashboard deployment + service
```

## Contributing

When adding new load shapes:

1. Add `LoadTestShape` class in `src/loadgenerator/locustfile.py`
2. Update `SHAPE_CLASSES` dict with new shape
3. Add metadata in `src/loadgen-controller/app.py` `SHAPE_METADATA`
4. Test locally before building images

## License

Same as parent microservices-demo project (Apache 2.0)

## Credits

- **Base project**: Google Cloud microservices-demo
- **Load testing**: Locust.io
- **UI design**: Inspired by SYDA UI design system
