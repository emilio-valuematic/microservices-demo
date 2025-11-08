import os
import random
import math
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

class StepLoadShape(LoadTestShape):
    """
    Step load pattern - gradual increase in fixed increments at regular intervals.

    Configuration:
    - STEP_TIME_SEC: time between steps in seconds (default: 30)
    - STEP_LOAD_INCREMENT: user increase at each step (default: 10)
    - STEP_STARTING_USERS: initial user count (default: 10)
    - STEP_MAX_USERS: maximum user count (optional, 0 for no limit)
    - STEP_SPAWN_RATE: spawn rate for adding users (default: 10)
    - STEP_DURATION_SEC: total test duration (default: 600, 0 for infinite)
    """
    def __init__(self):
        super().__init__()
        self.step_time = float(os.getenv("STEP_TIME_SEC", "30"))
        self.step_load = int(os.getenv("STEP_LOAD_INCREMENT", "10"))
        self.starting_users = int(os.getenv("STEP_STARTING_USERS", "10"))
        self.max_users = int(os.getenv("STEP_MAX_USERS", "0"))  # 0 = no limit
        self.spawn_rate = float(os.getenv("STEP_SPAWN_RATE", "10"))
        self.time_limit = float(os.getenv("STEP_DURATION_SEC", "600"))
        self.noise_percent = float(os.getenv("NOISE_PERCENT", "0"))

        if self.step_time <= 0:
            raise ValueError("STEP_TIME_SEC must be positive")

    def tick(self) -> Optional[Tuple[int, float]]:
        run_time = self.get_run_time()

        if self.time_limit > 0 and run_time > self.time_limit:
            return None

        current_step = math.floor(run_time / self.step_time)
        user_count = self.starting_users + (current_step * self.step_load)

        # Apply max limit if set
        if self.max_users > 0:
            user_count = min(user_count, self.max_users)

        ideal_users = user_count
        # Apply noise
        user_count = add_noise(user_count, self.noise_percent)
        print(f"Shape: Step, Ideal: {ideal_users}, Noisy: {user_count}", flush=True)

        return (user_count, self.spawn_rate)
