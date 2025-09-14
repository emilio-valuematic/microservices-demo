#!/usr/bin/python
#
# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import random
import os, math
from typing import Optional, Tuple
from locust import FastHttpUser, TaskSet, between, LoadTestShape
from faker import Faker
import datetime
fake = Faker()

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
        # Plateau ai picchi (in secondi)
        self.hold_max_sec = float(os.getenv("SHAPE_RAMP_HOLD_MAX_SEC", "0"))
        self.hold_min_sec = float(os.getenv("SHAPE_RAMP_HOLD_MIN_SEC", "0"))

        if self.spawn_rate <= 0:
            raise ValueError("SHAPE_RAMP_SPAWN_RATE must be positive")
        
        # Ensure non-negative minimum users
        if self.min_users < 0:
            self.min_users = 0
        
        user_delta = self.max_users - self.min_users
        if user_delta < 0:
            raise ValueError("SHAPE_RAMP_MAX_USERS must be >= SHAPE_RAMP_MIN_USERS")
        
        # Tempi di salita/discesa e durata del ciclo con hold ai capi
        self.t_up_sec = (user_delta / self.spawn_rate) if user_delta > 0 else 0
        self.t_down_sec = self.t_up_sec
        self.cycle_sec = self.t_up_sec + self.hold_max_sec + self.t_down_sec + self.hold_min_sec

    def tick(self) -> Optional[Tuple[int, float]]:
        rt = self.get_run_time()
        if self.duration_sec > 0 and rt > self.duration_sec:
            return None

        # Se il ciclo è nullo (nessuna rampa e nessun hold), mantieni min_users
        if self.cycle_sec == 0:
             return self.min_users, self.spawn_rate

        # Forma d'onda a tratti: salita → hold max → discesa → hold min
        t = rt % self.cycle_sec
        if t < self.t_up_sec:
            users = self.min_users + self.spawn_rate * t
        elif t < self.t_up_sec + self.hold_max_sec:
            users = self.max_users
        elif t < self.t_up_sec + self.hold_max_sec + self.t_down_sec:
            users = self.max_users - self.spawn_rate * (t - self.t_up_sec - self.hold_max_sec)
        else:
            users = self.min_users

        # Clamp finale per sicurezza
        users = max(self.min_users, min(self.max_users, users))

        return int(round(users)), self.spawn_rate

products = [
    '0PUK6V6EV0',
    '1YMWWN1N4O',
    '2ZYFJ3GM2N',
    '66VCHSJNUP',
    '6E92ZMYYFZ',
    '9SIQT8TOJO',
    'L9ECAV7KIM',
    'LS4PSXUNUM',
    'OLJCESPC7Z']

def index(l):
    l.client.get("/")

def setCurrency(l):
    currencies = ['EUR', 'USD', 'JPY', 'CAD', 'GBP', 'TRY']
    l.client.post("/setCurrency",
        {'currency_code': random.choice(currencies)})

def browseProduct(l):
    l.client.get("/product/" + random.choice(products))

def viewCart(l):
    l.client.get("/cart")

def addToCart(l):
    product = random.choice(products)
    l.client.get("/product/" + product)
    l.client.post("/cart", {
        'product_id': product,
        'quantity': random.randint(1,10)})
    
def empty_cart(l):
    l.client.post('/cart/empty')

def checkout(l):
    addToCart(l)
    current_year = datetime.datetime.now().year+1
    l.client.post("/cart/checkout", {
        'email': fake.email(),
        'street_address': fake.street_address(),
        'zip_code': fake.zipcode(),
        'city': fake.city(),
        'state': fake.state_abbr(),
        'country': fake.country(),
        'credit_card_number': fake.credit_card_number(card_type="visa"),
        'credit_card_expiration_month': random.randint(1, 12),
        'credit_card_expiration_year': random.randint(current_year, current_year + 70),
        'credit_card_cvv': f"{random.randint(100, 999)}",
    })
    
def logout(l):
    l.client.get('/logout')  


class UserBehavior(TaskSet):

    def on_start(self):
        index(self)

    tasks = {index: 1,
        setCurrency: 2,
        browseProduct: 10,
        addToCart: 2,
        viewCart: 3,
        checkout: 1}

class WebsiteUser(FastHttpUser):
    tasks = [UserBehavior]
    wait_time = between(1, 10)
