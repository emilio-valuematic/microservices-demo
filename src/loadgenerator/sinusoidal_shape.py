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

class SinusoidalWaveShape(LoadTestShape):
    """
    Smooth sinusoidal wave pattern for realistic traffic variations.

    Configuration:
    - SINE_MIN_USERS: minimum user count (default: 10)
    - SINE_MAX_USERS: maximum user count (default: 100)
    - SINE_PERIOD_SEC: period of one complete cycle in seconds (default: 300)
    - SINE_PHASE_OFFSET: phase offset in radians (default: 0)
    - SINE_DURATION_SEC: total test duration (default: 0 for infinite)
    """
    def __init__(self):
        super().__init__()
        self.min_users = int(os.getenv("SINE_MIN_USERS", "10"))
        self.max_users = int(os.getenv("SINE_MAX_USERS", "100"))
        self.period = float(os.getenv("SINE_PERIOD_SEC", "300"))
        self.phase_offset = float(os.getenv("SINE_PHASE_OFFSET", "0"))
        self.time_limit = float(os.getenv("SINE_DURATION_SEC", "0"))
        self.noise_percent = float(os.getenv("NOISE_PERCENT", "0"))

        if self.period <= 0:
            raise ValueError("SINE_PERIOD_SEC must be positive")

    def tick(self) -> Optional[Tuple[int, float]]:
        run_time = self.get_run_time()

        if self.time_limit > 0 and run_time > self.time_limit:
            return None

        amplitude = (self.max_users - self.min_users) / 2
        offset = self.min_users + amplitude
        user_count = offset + amplitude * math.sin(2 * math.pi * run_time / self.period + self.phase_offset)

        ideal_users = int(user_count)
        # Apply noise
        user_count = add_noise(ideal_users, self.noise_percent)
        print(f"Shape: Sinusoidal, Ideal: {ideal_users}, Noisy: {user_count}", flush=True)

        return (user_count, 10)
