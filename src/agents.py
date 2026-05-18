from random import random

import numpy as np

from .orderbook import Order

class RandomAgent:
    def __init__(self, agent_id: int, seed: int = None):
        self.agent_id = agent_id
        self.rng = np.random.default_rng(seed)
    
    def action(self, last_sale):
        # where momentum is (price_now - price_past) / price_past (divided to normalize into percentage)
        # Randomly decide to buy, sell, or do nothing

        action = self.rng.choice(['buy', 'sell', 'hold'])

        if action == 'hold':
            return None
        
        # price offset from mid: exponential distribution (most near mid, some far)
        price = self.rng.lognormal(mean=np.log(last_sale), sigma=0.01)
        size = max(1, round(self.rng.lognormal(mean=2, sigma=1)))
        # e^2 ≈ 7 shares average, long tail of larger orders

        return Order(side=action, price=round(price, 2),
                     quantity=size, agent_id=self.agent_id)

class DCAAgent:
    def __init__(self, agent_id: int, budget: float, seed: int = None):
        self.agent_id = agent_id
        self.budget = budget
        self.rng = np.random.default_rng(seed)
    
    def buy(self, last_sale):

        # Simulate a fixed buy every month.
        num_shares = max(1, round(self.budget / last_sale))
        price = last_sale * (1 + 0.015)
        #DCA Agents play orders above last sale to ensure they get filled
        
        return Order(side='buy', price=round(price, 2), quantity=num_shares, agent_id=self.agent_id)

    def action(self, last_sale):
        return self.buy(last_sale)