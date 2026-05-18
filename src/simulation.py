import random
import numpy as np
from .orderbook import OrderBook
from .agents    import RandomAgent, DCAAgent

def random_simulation(initial_price=100, num_agents=100, ticks=1000, seed=None, should_stop=None):
    order_book = OrderBook(initial_price)
    rng = np.random.default_rng(seed)
    agents = [RandomAgent(agent_id=i, seed=int(rng.integers(0, 2**31))) for i in range(num_agents)]
    price_history = []

    for _ in range(ticks):
        if should_stop and should_stop():
            break
        order_book.clear()
        for agent in agents:
            order = agent.action(order_book.last_price)
            if order:
                order_book.submit_order(order)
        order_book.match_orders()
        price_history.append(order_book.last_price)
    return order_book, price_history

def dca_simulation(initial_price=100, num_dca_agents=10, num_rand_agents=90, ticks=1000, seed=None, should_stop=None):
    order_book = OrderBook(initial_price)
    rng = np.random.default_rng(seed)
    dca_agents = [DCAAgent(agent_id=i, budget=500, seed=int(rng.integers(0, 2**31))) for i in range(num_dca_agents)]
    rand_agents = [RandomAgent(agent_id=num_dca_agents + i, seed=int(rng.integers(0, 2**31))) for i in range(num_rand_agents)]
    price_history = []

    for _ in range(ticks):
        if should_stop and should_stop():
            break
        order_book.clear()
        if _ % 30 == 0:
            for agent in dca_agents:
                order = agent.action(order_book.last_price)
                if order:
                    order_book.submit_order(order)
        for agent in rand_agents:
            order = agent.action(order_book.last_price)
            if order:
                order_book.submit_order(order)
        order_book.match_orders()
        price_history.append(order_book.last_price)
    return order_book, price_history

def monte_carlo(sim="random", n=50, initial_price=100, ticks=1000, seed=None, should_stop=None, **kwargs):
    rng = np.random.default_rng(seed)
    histories = []

    for _ in range(n):
        if should_stop and should_stop():
            break
        run_seed = int(rng.integers(0, 2**31))
        if sim == "random":
            _, history = random_simulation(
                initial_price=initial_price, ticks=ticks, seed=run_seed,
                should_stop=should_stop, **kwargs)
        else:
            _, history = dca_simulation(
                initial_price=initial_price, ticks=ticks, seed=run_seed,
                should_stop=should_stop, **kwargs)
        histories.append(history)

    if not histories:
        return [], []
    mean = np.mean(histories, axis=0).tolist()
    return mean, histories