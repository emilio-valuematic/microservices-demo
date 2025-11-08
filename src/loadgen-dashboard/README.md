# Load Generator Dashboard

React-based web dashboard for controlling the Locust load generator with visual configuration of load shapes.

## Features

- **Visual Shape Selection**: Choose from 5 different load patterns (Cyclic, Stages, Spike, Sinusoidal, Step)
- **Dynamic Parameter Forms**: Form fields adapt based on selected shape
- **Noise Configuration**: Slider to add randomness (0-100%) to user counts
- **Real-time Configuration**: View current deployment settings
- **One-Click Apply**: Update configuration and automatically restart the load generator
- **SYDA UI Styling**: Dark theme with cyan/purple accents matching SYDA UI design system

## Load Shape Patterns

### 1. Cyclic Ramp (Triangular)
Linear ramp up and down between min/max users with configurable plateaus at peaks and valleys.

**Use Case:** Simulating periodic traffic patterns with controllable ramp speeds

### 2. Stages (K6-style)
Pre-defined stages with specific user counts, durations, and spawn rates.

**Use Case:** Complex test scenarios with multiple phases (ramp-up, sustain, ramp-down)

### 3. Spike Testing
Sudden dramatic increase in users from baseline to peak, then back to baseline.

**Use Case:** Testing system resilience and auto-scaling response to traffic surges

### 4. Sinusoidal Wave
Smooth sinusoidal oscillation for realistic traffic variations.

**Use Case:** Natural day/night or weekday/weekend traffic patterns

### 5. Step Load
Gradual increase in fixed increments at regular intervals.

**Use Case:** Capacity planning and identifying performance degradation thresholds

## Technology Stack

- **React 18.2**: Modern React with hooks
- **React Bootstrap 2.7**: UI components
- **Axios**: HTTP client for API calls
- **React Toastify**: Toast notifications
- **React Feather**: Icon library

## Development

### Prerequisites
- Node.js 18+ and npm
- Access to load generator controller API

### Local Setup

```bash
cd src/loadgen-dashboard

# Install dependencies
npm install

# Set API URL (optional, defaults to http://localhost:8080)
export REACT_APP_API_URL=http://localhost:8080

# Start development server
npm start
```

The dashboard will open at `http://localhost:3000`

### Build for Production

```bash
npm run build
```

Build artifacts will be in the `build/` directory.

## Docker Build

```bash
cd src/loadgen-dashboard
docker build -t loadgen-dashboard:latest .
```

The Dockerfile uses multi-stage build:
1. **Stage 1**: Build React app with Node.js
2. **Stage 2**: Serve with nginx

## Deployment

The dashboard is deployed in Kubernetes as:
- **Deployment**: nginx serving static React build
- **Service**: LoadBalancer exposing port 80

Deploy using kustomize:

```bash
kubectl apply -k kustomize/base/
```

### Access Dashboard

After deployment:

```bash
# Get external IP
kubectl get svc loadgen-dashboard

# Access dashboard
# http://<EXTERNAL-IP>
```

For local development with port-forward:

```bash
kubectl port-forward svc/loadgen-dashboard 8081:80
# Access at http://localhost:8081
```

## Configuration

### Environment Variables

- `REACT_APP_API_URL`: URL of the load generator controller API
  - Default: `http://localhost:8080`
  - In Kubernetes: `http://loadgen-controller:8080`

## UI Components

### Main Components

- **App.js**: Main application component with state management
- **ShapeSelector**: Grid of selectable load shape cards
- **ParameterForm**: Dynamic form generator based on shape parameters
- **StagesEditor**: Special editor for JSON-based stages configuration

### Styling

The dashboard matches SYDA UI design system:
- **Colors**: Dark navy background (#0a192f) with cyan (#64ffda) and purple (#8b5cf6) accents
- **Typography**: Open Sans for body text, Mulish for headings, SF Mono for code
- **Effects**: Glassmorphism, glow effects on cards and buttons
- **Theme**: Fully dark mode with high contrast

## Usage

1. **Select Load Shape**: Click on desired pattern card
2. **Configure Parameters**: Fill in shape-specific parameters
3. **Adjust Noise**: Use slider to add randomness (optional)
4. **Apply Configuration**: Click "Apply Configuration & Restart" button
5. **Monitor**: Toast notifications show success/error status

## Troubleshooting

### Dashboard not loading
```bash
# Check dashboard pod status
kubectl get pods -l app=loadgen-dashboard

# Check logs
kubectl logs -l app=loadgen-dashboard
```

### API connection errors
```bash
# Verify controller service is running
kubectl get svc loadgen-controller

# Test API from dashboard pod
kubectl exec -it <dashboard-pod> -- wget -O- http://loadgen-controller:8080/health
```

### Configuration not applying
```bash
# Check controller logs for errors
kubectl logs -l app=loadgen-controller

# Verify RBAC permissions
kubectl auth can-i patch deployment/loadgenerator --as=system:serviceaccount:default:loadgen-controller
```

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
