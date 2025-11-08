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

class CyclicRampShape(LoadTestShape):
    """
    Rampa ciclica triangolare (up/down lineare) la cui pendenza (e quindi periodo)
    è definita da SHAPE_RAMP_SPAWN_RATE.
    """
    def __init__(self):
        super().__init__()
        self.min_users = int(os.getenv("SHAPE_RAMP_MIN_USERS", "10"))
        self.max_users = int(os.getenv("SHAPE_RAMP_MAX_USERS", "100"))
        self.spawn_rate = float(os.getenv("SHAPE_RAMP_SPAWN_RATE", "5"))
        self.duration_sec = float(os.getenv("SHAPE_RAMP_DURATION_SEC", "0"))
        self.hold_max_sec = float(os.getenv("SHAPE_RAMP_HOLD_MAX_SEC", "0"))
        self.hold_min_sec = float(os.getenv("SHAPE_RAMP_HOLD_MIN_SEC", "0"))
        self.noise_percent = float(os.getenv("NOISE_PERCENT", "0"))

        if self.spawn_rate <= 0:
            raise ValueError("SHAPE_RAMP_SPAWN_RATE must be positive")
        
        if self.min_users < 0:
            self.min_users = 0
        
        user_delta = self.max_users - self.min_users
        if user_delta < 0:
            raise ValueError("SHAPE_RAMP_MAX_USERS must be >= SHAPE_RAMP_MIN_USERS")
        
        self.t_up_sec = (user_delta / self.spawn_rate) if user_delta > 0 else 0
        self.t_down_sec = self.t_up_sec
        self.cycle_sec = self.t_up_sec + self.hold_max_sec + self.t_down_sec + self.hold_min_sec

    def tick(self) -> Optional[Tuple[int, float]]:
        rt = self.get_run_time()
        if self.duration_sec > 0 and rt > self.duration_sec:
            return None

        if self.cycle_sec == 0:
             return self.min_users, self.spawn_rate

        t = rt % self.cycle_sec
        if t < self.t_up_sec:
            users = self.min_users + self.spawn_rate * t
        elif t < self.t_up_sec + self.hold_max_sec:
            users = self.max_users
        elif t < self.t_up_sec + self.hold_max_sec + self.t_down_sec:
            users = self.max_users - self.spawn_rate * (t - self.t_up_sec - self.hold_max_sec)
        else:
            users = self.min_users

        users = max(self.min_users, min(self.max_users, users))
        ideal_users = users # Store ideal count before noise

        # Apply noise
        users = add_noise(users, self.noise_percent)
        print(f"Shape: CyclicRamp, Ideal: {ideal_users}, Noisy: {users}", flush=True)

        return int(round(users)), self.spawn_rate
