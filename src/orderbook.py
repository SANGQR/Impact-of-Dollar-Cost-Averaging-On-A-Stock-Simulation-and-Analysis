import heapq
from dataclasses import dataclass

@dataclass
class Order:
    side: str # 'buy' or 'sell'
    price: float
    quantity: int
    agent_id: int

class OrderBook:
    def __init__(self, initial_price: float):
        self.buy_orders: list = [] # Max-heap for buy orders
        self.sell_orders: list = [] # Min-heap for sell orders
        self.last_price: float = initial_price
        self.spread_history = []
        self._counter = 0

    def submit_order(self, order: Order):
        self._counter += 1
        if order.side == 'buy':
            heapq.heappush(self.buy_orders, (-order.price, self._counter, order))
        if order.side == 'sell':
            heapq.heappush(self.sell_orders, (order.price, self._counter, order))
    
    def match_orders(self):
        fills = []
        while self.buy_orders and self.sell_orders:
            best_buy = self.buy_orders[0][2]
            best_sell = self.sell_orders[0][2]
            if best_buy.price < best_sell.price:
                break # No match possible

            # Match orders
            fill_price = (best_buy.price + best_sell.price) / 2
            fill_quantity = min(best_buy.quantity, best_sell.quantity)
            self.last_price = fill_price
            fills.append((fill_price, fill_quantity))

            # Update quantities
            best_buy.quantity -= fill_quantity
            best_sell.quantity -= fill_quantity
            if best_buy.quantity == 0:
                heapq.heappop(self.buy_orders) # Remove fully filled buy order
            if best_sell.quantity == 0:
                heapq.heappop(self.sell_orders) # Remove fully filled sell order
            
        return fills

    def clear(self):
        self.buy_orders.clear()
        self.sell_orders.clear()

    @property
    def mid_price(self):
        if not self.buy_orders or not self.sell_orders:
            return self.last_price
        return (self.buy_orders[0][2].price + self.sell_orders[0][2].price) / 2

    @property
    def spread(self):
        if not self.buy_orders or not self.sell_orders:
            return None
        return self.sell_orders[0][2].price - self.buy_orders[0][2].price
    
    @property
    def best_bid(self):
        return self.buy_orders[0][2].price if self.buy_orders else None
    
    @property
    def best_ask(self):
        return self.sell_orders[0][2].price if self.sell_orders else None
    
