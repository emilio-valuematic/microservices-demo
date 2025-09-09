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

        if self.spawn_rate <= 0:
            raise ValueError("SHAPE_RAMP_SPAWN_RATE must be positive")
        
        user_delta = self.max_users - self.min_users
        if user_delta < 0:
            raise ValueError("SHAPE_RAMP_MAX_USERS must be >= SHAPE_RAMP_MIN_USERS")
        
        # Il periodo è calcolato in base allo spawn rate. Se il numero di utenti
        # è costante, il periodo non è rilevante.
        self.period_sec = (2 * user_delta / self.spawn_rate) if user_delta > 0 else 0

    def tick(self) -> Optional[Tuple[int, float]]:
        rt = self.get_run_time()
        if self.duration_sec > 0 and rt > self.duration_sec:
            return None

        if self.period_sec == 0:
             return self.min_users, self.spawn_rate
        
        # Calcola il target di utenti usando la forma d'onda triangolare,
        # dove il periodo è derivato dallo spawn rate.
        p = (rt % self.period_sec) / self.period_sec
        tri = 2 * abs(2 * p - 1)
        amp = max(0, self.max_users - self.min_users)
        users = self.min_users + amp * (1.0 - tri)
        
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
