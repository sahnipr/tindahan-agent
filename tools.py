"""In-process sandbox APIs. Prices are integer Philippine centavos."""
from copy import deepcopy
import time
import uuid
from threading import RLock


class ToolError(Exception):
    pass


class Sandbox:
    def __init__(self, clock=time.time):
        self.clock = clock
        self.lock = RLock()
        self.products = [
            dict(sku='sardines', name='Mega Sardines 155g can', aliases=['sardinas', 'mega sardines', 'sardines'], catalog_price=2400),
            dict(sku='coffee', name='Kopiko Brown 27.5g sachet', aliases=['kopiko brown', 'kopiko', 'kape', 'coffee'], catalog_price=800),
            dict(sku='noodles', name='Lucky Me Pancit Canton Original 60g pack', aliases=['pancit canton', 'lucky me', 'noodles'], catalog_price=1400),
        ]
        self.prices = {'sardines': 2600, 'coffee': 800, 'noodles': 1400}
        self.inventory = {'sardines': 100, 'coffee': 200, 'noodles': 5}
        self.quotes, self.orders = {}, {}
        self.pricing_available = True

    def catalog(self):
        return deepcopy(self.products)

    def stock(self, sku):
        with self.lock:
            if sku not in self.inventory:
                raise ToolError('Unknown SKU')
            return {'sku': sku, 'available': self.inventory[sku]}

    def quote(self, owner, items):
        with self.lock:
            if not self.pricing_available:
                raise ToolError('Live pricing unavailable; please try again later.')
            if not items or any(s not in self.prices or type(q) is not int or not 1 <= q <= 999 for s, q in items.items()):
                raise ToolError('Invalid order items')
            for sku, qty in items.items():
                if self.stock(sku)['available'] < qty:
                    raise ToolError(f"Only {self.inventory[sku]} units of {sku} available. Please revise quantities.")
            lines = [dict(sku=s, quantity=q, unit_price=self.prices[s], subtotal=q*self.prices[s]) for s, q in items.items()]
            quote = dict(id=uuid.uuid4().hex[:12], owner=owner, lines=lines,
                         total=sum(x['subtotal'] for x in lines), currency='PHP', expires_at=self.clock()+300)
            self.quotes[quote['id']] = quote
            return deepcopy(quote)

    def place_order(self, owner, quote_id):
        """Atomic validation + stock decrement; quote ID is the idempotency key.

        Called only by Agent after confirmation. Production must authenticate
        service calls and persist this transaction and idempotency key.
        """
        with self.lock:
            q = self.quotes.get(quote_id)
            if not q or q['owner'] != owner:
                raise ToolError('Quote not found for this owner')
            if quote_id in self.orders:
                return deepcopy(self.orders[quote_id])
            if self.clock() >= q['expires_at']:
                raise ToolError('Quote expired. Request a new quote and confirm again.')
            if not self.pricing_available:
                raise ToolError('Live pricing unavailable; order not placed.')
            if any(self.prices[x['sku']] != x['unit_price'] for x in q['lines']):
                raise ToolError('Price changed. Request a new quote and confirm again.')
            if any(self.inventory[x['sku']] < x['quantity'] for x in q['lines']):
                raise ToolError('Stock changed. Request a new quote and confirm again.')
            for x in q['lines']:
                self.inventory[x['sku']] -= x['quantity']
            order = dict(id='ORD-'+uuid.uuid4().hex[:8], quote_id=quote_id, owner=owner,
                         total=q['total'], currency='PHP', status='placed')
            self.orders[quote_id] = order
            return deepcopy(order)
