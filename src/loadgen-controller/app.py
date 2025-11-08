#!/usr/bin/env python3
"""
Load Generator Controller API

Flask API for managing the load generator Kubernetes deployment.
Provides endpoints to read/update configuration and restart the load generator pod.
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import datetime
import os
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for frontend

# Kubernetes configuration
DEPLOYMENT_NAME = os.getenv("DEPLOYMENT_NAME", "loadgenerator")
NAMESPACE = os.getenv("NAMESPACE", "default")
CONTAINER_NAME = os.getenv("CONTAINER_NAME", "main")

# Load Kubernetes config
try:
    config.load_incluster_config()
    logger.info("Loaded in-cluster Kubernetes config")
except config.ConfigException:
    try:
        config.load_kube_config()
        logger.info("Loaded kubeconfig from local environment")
    except config.ConfigException:
        logger.error("Could not load Kubernetes configuration")
        raise

v1_apps = client.AppsV1Api()


# Shape metadata for UI
SHAPE_METADATA = {
    "cyclic": {
        "name": "Cyclic Ramp (Triangular)",
        "description": "Linear ramp up and down between min/max users with configurable plateaus",
        "parameters": [
            {"name": "SHAPE_RAMP_MIN_USERS", "type": "int", "default": 10, "min": 0, "label": "Minimum Users"},
            {"name": "SHAPE_RAMP_MAX_USERS", "type": "int", "default": 100, "min": 1, "label": "Maximum Users"},
            {"name": "SHAPE_RAMP_SPAWN_RATE", "type": "float", "default": 5.0, "min": 0.01, "step": 0.01, "label": "Spawn Rate (users/sec)"},
            {"name": "SHAPE_RAMP_HOLD_MAX_SEC", "type": "int", "default": 0, "min": 0, "label": "Hold at Max (seconds)"},
            {"name": "SHAPE_RAMP_HOLD_MIN_SEC", "type": "int", "default": 0, "min": 0, "label": "Hold at Min (seconds)"},
            {"name": "SHAPE_RAMP_DURATION_SEC", "type": "int", "default": 0, "min": 0, "label": "Total Duration (0=infinite)"}
        ]
    },
    "stages": {
        "name": "Stages (K6-style)",
        "description": "Pre-defined stages with specific user counts, durations, and spawn rates",
        "parameters": [
            {
                "name": "STAGES_JSON",
                "type": "json",
                "default": [
                    {"duration": 60, "users": 10, "spawn_rate": 10},
                    {"duration": 120, "users": 50, "spawn_rate": 10},
                    {"duration": 180, "users": 100, "spawn_rate": 10},
                    {"duration": 240, "users": 30, "spawn_rate": 10}
                ],
                "label": "Stages Configuration",
                "description": "Array of stages: [{duration, users, spawn_rate}, ...]"
            }
        ]
    },
    "spike": {
        "name": "Spike Testing",
        "description": "Sudden dramatic increase in users, then back to baseline",
        "parameters": [
            {"name": "SPIKE_NORMAL_USERS", "type": "int", "default": 10, "min": 0, "label": "Normal Users (baseline)"},
            {"name": "SPIKE_MAX_USERS", "type": "int", "default": 100, "min": 1, "label": "Spike Users (peak)"},
            {"name": "SPIKE_START_SEC", "type": "int", "default": 180, "min": 0, "label": "Spike Start (seconds)"},
            {"name": "SPIKE_DURATION_SEC", "type": "int", "default": 60, "min": 1, "label": "Spike Duration (seconds)"},
            {"name": "SPIKE_TOTAL_DURATION_SEC", "type": "int", "default": 600, "min": 0, "label": "Total Duration (0=infinite)"}
        ]
    },
    "sinusoidal": {
        "name": "Sinusoidal Wave",
        "description": "Smooth sinusoidal oscillation for realistic traffic variations",
        "parameters": [
            {"name": "SINE_MIN_USERS", "type": "int", "default": 10, "min": 0, "label": "Minimum Users"},
            {"name": "SINE_MAX_USERS", "type": "int", "default": 100, "min": 1, "label": "Maximum Users"},
            {"name": "SINE_PERIOD_SEC", "type": "int", "default": 300, "min": 1, "label": "Period (seconds)"},
            {"name": "SINE_PHASE_OFFSET", "type": "float", "default": 0, "step": 0.1, "label": "Phase Offset (radians)"},
            {"name": "SINE_DURATION_SEC", "type": "int", "default": 0, "min": 0, "label": "Total Duration (0=infinite)"}
        ]
    },
    "step": {
        "name": "Step Load",
        "description": "Gradual increase in fixed increments at regular intervals",
        "parameters": [
            {"name": "STEP_STARTING_USERS", "type": "int", "default": 10, "min": 0, "label": "Starting Users"},
            {"name": "STEP_LOAD_INCREMENT", "type": "int", "default": 10, "min": 1, "label": "User Increment per Step"},
            {"name": "STEP_TIME_SEC", "type": "int", "default": 30, "min": 1, "label": "Time Between Steps (seconds)"},
            {"name": "STEP_MAX_USERS", "type": "int", "default": 0, "min": 0, "label": "Max Users (0=no limit)"},
            {"name": "STEP_SPAWN_RATE", "type": "float", "default": 10, "min": 0.1, "step": 0.1, "label": "Spawn Rate"},
            {"name": "STEP_DURATION_SEC", "type": "int", "default": 600, "min": 0, "label": "Total Duration (0=infinite)"}
        ]
    }
}


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200


@app.route('/api/shapes', methods=['GET'])
def get_shapes():
    """Get list of available load shapes with metadata"""
    return jsonify({
        "status": "success",
        "shapes": SHAPE_METADATA
    })


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current load generator configuration from deployment"""
    try:
        deployment = v1_apps.read_namespaced_deployment(
            name=DEPLOYMENT_NAME,
            namespace=NAMESPACE
        )

        # Extract environment variables from the main container
        env_vars = {}
        for container in deployment.spec.template.spec.containers:
            if container.name == CONTAINER_NAME:
                if container.env:
                    for env in container.env:
                        env_vars[env.name] = env.value

        # Get current shape type
        current_shape = env_vars.get("LOAD_SHAPE_TYPE", "cyclic")

        return jsonify({
            "status": "success",
            "config": env_vars,
            "current_shape": current_shape,
            "deployment_name": DEPLOYMENT_NAME,
            "namespace": NAMESPACE
        })

    except ApiException as e:
        logger.error(f"Kubernetes API error: {e}")
        return jsonify({
            "status": "error",
            "message": f"Failed to read deployment: {e.reason}"
        }), e.status

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/config', methods=['PUT'])
def update_config():
    """Update load generator configuration and restart deployment"""
    try:
        new_config = request.json
        logger.info(f"Received config update: {new_config}")

        # Validation
        if not new_config:
            return jsonify({
                "status": "error",
                "message": "Empty configuration provided"
            }), 400

        # Read current deployment
        deployment = v1_apps.read_namespaced_deployment(
            name=DEPLOYMENT_NAME,
            namespace=NAMESPACE
        )

        # Find the main container and update environment variables
        container_found = False
        for container in deployment.spec.template.spec.containers:
            if container.name == CONTAINER_NAME:
                container_found = True

                # Create env map for easy access
                env_map = {}
                if container.env:
                    env_map = {e.name: e for e in container.env}
                else:
                    container.env = []

                # Update or add environment variables
                for key, value in new_config.items():
                    # Convert value to string
                    value_str = json.dumps(value) if isinstance(value, (dict, list)) else str(value)

                    if key in env_map:
                        # Update existing env var
                        env_map[key].value = value_str
                    else:
                        # Add new env var
                        new_env = client.V1EnvVar(name=key, value=value_str)
                        container.env.append(new_env)
                        logger.info(f"Added new env var: {key}={value_str}")

        if not container_found:
            return jsonify({
                "status": "error",
                "message": f"Container '{CONTAINER_NAME}' not found in deployment"
            }), 404

        # Add restart annotation to trigger rollout
        now = datetime.datetime.utcnow().isoformat() + "Z"
        if not deployment.spec.template.metadata.annotations:
            deployment.spec.template.metadata.annotations = {}
        deployment.spec.template.metadata.annotations['kubectl.kubernetes.io/restartedAt'] = now

        # Patch the deployment
        v1_apps.patch_namespaced_deployment(
            name=DEPLOYMENT_NAME,
            namespace=NAMESPACE,
            body=deployment
        )

        logger.info(f"Successfully updated deployment {DEPLOYMENT_NAME}")

        return jsonify({
            "status": "success",
            "message": "Configuration updated and deployment restarting",
            "restarted_at": now
        })

    except ApiException as e:
        logger.error(f"Kubernetes API error: {e}")
        return jsonify({
            "status": "error",
            "message": f"Failed to update deployment: {e.reason}"
        }), e.status

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/restart', methods=['POST'])
def restart_deployment():
    """Restart the load generator deployment without config changes"""
    try:
        # Read current deployment
        deployment = v1_apps.read_namespaced_deployment(
            name=DEPLOYMENT_NAME,
            namespace=NAMESPACE
        )

        # Add restart annotation
        now = datetime.datetime.utcnow().isoformat() + "Z"
        if not deployment.spec.template.metadata.annotations:
            deployment.spec.template.metadata.annotations = {}
        deployment.spec.template.metadata.annotations['kubectl.kubernetes.io/restartedAt'] = now

        # Patch the deployment
        v1_apps.patch_namespaced_deployment(
            name=DEPLOYMENT_NAME,
            namespace=NAMESPACE,
            body=deployment
        )

        logger.info(f"Successfully restarted deployment {DEPLOYMENT_NAME}")

        return jsonify({
            "status": "success",
            "message": "Deployment restarting",
            "restarted_at": now
        })

    except ApiException as e:
        logger.error(f"Kubernetes API error: {e}")
        return jsonify({
            "status": "error",
            "message": f"Failed to restart deployment: {e.reason}"
        }), e.status

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/')
def index():
    """Serve static frontend (if exists)"""
    try:
        return send_from_directory('static', 'index.html')
    except FileNotFoundError:
        return jsonify({
            "status": "ok",
            "message": "Load Generator Controller API",
            "endpoints": {
                "/health": "Health check",
                "/api/shapes": "Get available load shapes",
                "/api/config": "GET current config, PUT to update",
                "/api/restart": "POST to restart deployment"
            }
        })


if __name__ == '__main__':
    port = int(os.getenv("PORT", "8080"))
    logger.info(f"Starting Load Generator Controller on port {port}")
    logger.info(f"Managing deployment: {DEPLOYMENT_NAME} in namespace: {NAMESPACE}")
    app.run(host='0.0.0.0', port=port, debug=False)
