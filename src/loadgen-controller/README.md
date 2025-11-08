# Load Generator Controller API

Flask-based REST API for managing the Locust load generator deployment in Kubernetes.

## Features

- Get list of available load shapes with parameter metadata
- Read current load generator configuration
- Update configuration and automatically restart the deployment
- Manual deployment restart endpoint
- RBAC-based security with minimal required permissions

## API Endpoints

### `GET /health`
Health check endpoint

**Response:**
```json
{
  "status": "healthy"
}
```

### `GET /api/shapes`
Get available load shapes with their parameters

**Response:**
```json
{
  "status": "success",
  "shapes": {
    "cyclic": {
      "name": "Cyclic Ramp (Triangular)",
      "description": "...",
      "parameters": [...]
    },
    ...
  }
}
```

### `GET /api/config`
Get current load generator configuration

**Response:**
```json
{
  "status": "success",
  "config": {
    "LOAD_SHAPE_TYPE": "cyclic",
    "NOISE_PERCENT": "0",
    ...
  },
  "current_shape": "cyclic",
  "deployment_name": "loadgenerator",
  "namespace": "default"
}
```

### `PUT /api/config`
Update configuration and restart deployment

**Request Body:**
```json
{
  "LOAD_SHAPE_TYPE": "spike",
  "NOISE_PERCENT": "10",
  "SPIKE_NORMAL_USERS": "10",
  "SPIKE_MAX_USERS": "100",
  "SPIKE_START_SEC": "180",
  "SPIKE_DURATION_SEC": "60"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Configuration updated and deployment restarting",
  "restarted_at": "2025-01-31T10:30:00Z"
}
```

### `POST /api/restart`
Restart deployment without configuration changes

**Response:**
```json
{
  "status": "success",
  "message": "Deployment restarting",
  "restarted_at": "2025-01-31T10:30:00Z"
}
```

## Environment Variables

- `DEPLOYMENT_NAME`: Name of the load generator deployment (default: `loadgenerator`)
- `NAMESPACE`: Kubernetes namespace (default: `default`)
- `CONTAINER_NAME`: Name of the main container in deployment (default: `main`)
- `PORT`: Port to run the API server (default: `8080`)

## Development

### Local Setup

```bash
cd src/loadgen-controller

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run locally (requires kubeconfig)
python app.py
```

### Build Docker Image

```bash
cd src/loadgen-controller
docker build -t loadgen-controller:latest .
```

### Run with Docker

```bash
docker run -p 8080:8080 \
  -v ~/.kube/config:/root/.kube/config:ro \
  -e DEPLOYMENT_NAME=loadgenerator \
  -e NAMESPACE=default \
  loadgen-controller:latest
```

## Deployment

The controller is deployed in Kubernetes with:
- **ServiceAccount**: `loadgen-controller`
- **Role**: Permissions to read/patch deployments and list pods
- **RoleBinding**: Binds role to service account
- **Deployment**: Runs the Flask API
- **Service**: Exposes the API within the cluster

Deploy using kustomize:

```bash
kubectl apply -k kustomize/base/
```

## Security

- Runs as non-root user (UID 1000)
- Minimal RBAC permissions (only deployment read/patch)
- Input validation on configuration updates
- Kubernetes API errors properly handled

## Troubleshooting

### Check controller logs
```bash
kubectl logs -l app=loadgen-controller
```

### Test API from within cluster
```bash
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl http://loadgen-controller:8080/health
```

### Verify RBAC permissions
```bash
kubectl auth can-i patch deployment/loadgenerator --as=system:serviceaccount:default:loadgen-controller
```
