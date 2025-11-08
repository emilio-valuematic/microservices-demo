import os
import random
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

class SpikeShape(LoadTestShape):
    """
    Spike testing pattern - sudden dramatic increase in users, then back to baseline.

    Configuration:
    - SPIKE_NORMAL_USERS: baseline user count (default: 10)
    - SPIKE_MAX_USERS: peak user count during spike (default: 100)
    - SPIKE_START_SEC: when to start spike in seconds (default: 180)
    - SPIKE_DURATION_SEC: how long spike lasts (default: 60)
    - SPIKE_TOTAL_DURATION_SEC: total test duration (default: 600, 0 for infinite)
    """
    def __init__(self):
        super().__init__()
        self.normal_users = int(os.getenv("SPIKE_NORMAL_USERS", "10"))
        self.spike_users = int(os.getenv("SPIKE_MAX_USERS", "100"))
        self.spike_start = float(os.getenv("SPIKE_START_SEC", "180"))
        self.spike_duration = float(os.getenv("SPIKE_DURATION_SEC", "60"))
        self.time_limit = float(os.getenv("SPIKE_TOTAL_DURATION_SEC", "600"))
        self.noise_percent = float(os.getenv("NOISE_PERCENT", "0"))

    def tick(self) -> Optional[Tuple[int, float]]:
        run_time = self.get_run_time()

        if self.time_limit > 0 and run_time > self.time_limit:
            return None

        if self.spike_start <= run_time < (self.spike_start + self.spike_duration):
            ideal_users = self.spike_users
            users = add_noise(ideal_users, self.noise_percent)
            print(f"Shape: Spike, Ideal: {ideal_users}, Noisy: {users}", flush=True)
            return (users, 50)
        else:
            ideal_users = self.normal_users
            users = add_noise(ideal_users, self.noise_percent)
            print(f"Shape: Spike, Ideal: {ideal_users}, Noisy: {users}", flush=True)
            return (users, 10)
