## Load Generator: Multi-Shape Load Testing with Noise

This directory contains the Locust-based load generator for the microservices demo. It supports **5 different load shape patterns** with configurable noise for realistic traffic simulation.

### Available Load Shapes

Select a shape using the `LOAD_SHAPE_TYPE` environment variable:

#### 1. **Cyclic Ramp** (default: `cyclic`)
Triangular wave with linear ramp up/down and configurable plateaus at peaks/valleys.

**Use case**: Periodic traffic, oscillating load patterns

#### 2. **Stages** (`stages`)
K6-style multi-phase testing with pre-defined stages (duration, users, spawn_rate).

**Use case**: Complex scenarios with multiple phases, realistic business cycles

#### 3. **Spike** (`spike`)
Sudden dramatic traffic surge from baseline to peak, then recovery to baseline.

**Use case**: Resilience testing, Black Friday simulation, autoscaler validation

#### 4. **Sinusoidal Wave** (`sinusoidal`)
Smooth sine wave oscillation for natural traffic variations.

**Use case**: Day/night patterns, weekday/weekend cycles

#### 5. **Step Load** (`step`)
Incremental user increases at regular intervals.

**Use case**: Capacity planning, threshold identification

### Noise Feature

All shapes support **configurable noise** (0-100%) via `NOISE_PERCENT` to add gaussian randomness to user counts, simulating realistic traffic unpredictability.

## Quick Start

### Select a Load Shape

```bash
# Set shape type
export LOAD_SHAPE_TYPE=spike  # Options: cyclic, stages, spike, sinusoidal, step

# Add noise for realism
export NOISE_PERCENT=10  # 0-100%
```

### Configuration via environment variables

**Common to all shapes:**
- **LOAD_SHAPE_TYPE** ("cyclic"): Shape pattern to use
- **NOISE_PERCENT** ("0"): Gaussian noise level 0-100%

**Cyclic Ramp parameters:**
- **SHAPE_RAMP_MIN_USERS** ("10"): minimum number of users
- **SHAPE_RAMP_MAX_USERS** ("100"): maximum number of users
- **SHAPE_RAMP_SPAWN_RATE** ("5"): users spawned per second. This parameter **defines the ramp's slope** and dynamically calculates the wave's period.
- **SHAPE_RAMP_DURATION_SEC** ("0"): total test duration in seconds; 0 means run indefinitely

The wave's period is now calculated as: `period_sec = 2 * (max_users - min_users) / spawn_rate`.

### Approximating a sinusoidal load
- A triangle wave approximates a sine: choose `min/max` to set amplitude and adjust `SHAPE_RAMP_SPAWN_RATE` to control the period. A lower spawn rate will result in a wider (longer) wave.

### Local usage
You can run Locust directly, providing your target host and any desired env vars.

```bash
export SHAPE_RAMP_MIN_USERS=20
export SHAPE_RAMP_MAX_USERS=200
export SHAPE_RAMP_SPAWN_RATE=0.5 # This will result in a period of 2 * 180 / 0.5 = 720 seconds
export SHAPE_RAMP_DURATION_SEC=900   # 0 to run indefinitely

locust -f src/loadgenerator/locustfile.py \
  --headless --host=http://localhost:8080
```

If multiple shapes are defined in `locustfile.py`, select this one explicitly:

```bash
locust -f src/loadgenerator/locustfile.py \
  --headless --host=http://localhost:8080 \
  --shape-class CyclicRampShape
```

### Kubernetes usage
`kustomize/base/loadgenerator.yaml` sets the following env vars on the `loadgenerator` Deployment. Tune these values to adjust the wave in-cluster.

```yaml
        - name: SHAPE_RAMP_MIN_USERS
          value: "20"
        - name: SHAPE_RAMP_MAX_USERS
          value: "200"
        - name: SHAPE_RAMP_SPAWN_RATE
          value: "0.5"
        - name: SHAPE_RAMP_DURATION_SEC
          value: "0"
```

Apply changes via Kustomize as usual:

```bash
kubectl apply -k kustomize
```

### Container image notes
- The Dockerfile installs `locust`, `locust-plugins`, and test dependencies.
- Build and push your image, then update the `image:` in the `loadgenerator` Deployment (or use your existing image management flow):

```bash
cd src/loadgenerator
docker build -t docker.io/<your-user>/loadgenerator:ramp .
docker push docker.io/<your-user>/loadgenerator:ramp
```

### Where to look in code
- `src/loadgenerator/locustfile.py`: contains `CyclicRampShape` and user tasks
- `src/loadgenerator/Dockerfile`: build steps for the load generator image
- `kustomize/base/loadgenerator.yaml`: Deployment with environment variables for shape control


