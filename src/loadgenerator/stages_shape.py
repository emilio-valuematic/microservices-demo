import os
import random
import json
from typing import Optional, Tuple
from locust import LoadTestShape

def add_noise(user_count: int, noise_percent: float) -> int:
    """
    Add gaussian noise to user count based on noise percentage.

    Args:
        user_count: Base user count
        noise_percent: Noise level as percentage (0-100)

    Returns:
        User count with noise applied (never negative)
    """
    if noise_percent > 0:
        std_dev = user_count * noise_percent / 100
        noise = random.gauss(0, std_dev)
        return max(0, int(user_count + noise))
    return int(user_count)

class StagesShape(LoadTestShape):
    """
    A load test shape with pre-defined stages (K6-style).
    Each stage defines duration, user count, and spawn rate.

    Configuration via STAGES_JSON env var (JSON array of stages):
    [
        {"duration": 60, "users": 10, "spawn_rate": 10},
        {"duration": 120, "users": 50, "spawn_rate": 10},
        {"duration": 180, "users": 100, "spawn_rate": 10},
        {"duration": 240, "users": 30, "spawn_rate": 10}
    ]
    """
    def __init__(self):
        super().__init__()
        self.noise_percent = float(os.getenv("NOISE_PERCENT", "0"))

        stages_json = os.getenv("STAGES_JSON", '[{"duration": 60, "users": 10, "spawn_rate": 10}]')
        try:
            self.stages = json.loads(stages_json)
        except json.JSONDecodeError:
            print(f"Error parsing STAGES_JSON: {stages_json}")
            self.stages = [{"duration": 60, "users": 10, "spawn_rate": 10}]

        for stage in self.stages:
            if "duration" not in stage or "users" not in stage or "spawn_rate" not in stage:
                raise ValueError("Each stage must have duration, users, and spawn_rate")

    def tick(self) -> Optional[Tuple[int, float]]:
        run_time = self.get_run_time()

        for stage in self.stages:
            if run_time < stage["duration"]:
                ideal_users = stage["users"]
                users = add_noise(ideal_users, self.noise_percent)
                print(f"Shape: Stages, Ideal: {ideal_users}, Noisy: {users}", flush=True)
                return (users, stage["spawn_rate"])

        return None
