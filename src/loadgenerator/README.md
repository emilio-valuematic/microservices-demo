## Load Generator: Cyclic Ramp (Triangular) Load Shape

This directory contains the Locust-based load generator for the microservices demo. In addition to the existing user flows, it now supports a cyclic ramp (triangular) LoadTestShape that continuously ramps users up and down between configurable bounds.

### What is the Cyclic Ramp Shape?
- **Idea**: Model load as a repeating triangle wave (linear ramp up, then linear ramp down).
- **Effect**: Users oscillate between a minimum and a maximum with a fixed period.
- **Implementation**: A `LoadTestShape` named `CyclicRampShape` in `locustfile.py`.
- **Note**: When a `LoadTestShape` is present, Locust ignores `-u` and `-r` CLI flags.

Shape definition (for time `t` in seconds):
```
users(t) = min_users + (max_users - min_users) * (1 - tri(p))
where p = (t % period_sec) / period_sec and tri(p) = 2 * |2p - 1|
```

### Configuration via environment variables
Set these to control the wave. Defaults are shown in parentheses.
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


