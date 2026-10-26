"""Conservative bilingual order interpreter and confirmation state machine."""
import re
from tools import ToolError


def money(cents):
    return f'PHP {cents // 100}.{cents % 100:02d}'


class Agent:
    def __init__(self, tools):
        self.tools = tools
        self.pending = {}
        self.completed = {}

    def parse(self, text):
        # Deliberately narrow grammar: each clause must be fully recognized.
        # Rejecting unknown trailing text prevents partial orders/instructions.
        text = text.lower().strip().rstrip('.!?')
        text = re.sub(r'^(?:pabili(?: po)?|paorder(?: po)?|order(?: please)?|please order)\s*[:,]?\s*', '', text)
        text = re.sub(r'\s+(?:po|please|salamat)$', '', text)
        clauses = re.split(r'\s*(?:,|;|\bat\b|\band\b)\s*', text)
        items = {}
        for clause in clauses:
            match = re.fullmatch(r'(\d+)\s+(?:(?:pcs?|pieces?|cans?|packs?|sachets?)\s+)?(.+)', clause)
            if not match:
                raise ToolError('Please specify quantity and product per item, e.g. “2 sardinas, 3 kopiko brown”. Use individual units, not cases.')
            qty, label = int(match[1]), match[2].strip()
            products = [p for p in self.tools.catalog() if label in p['aliases'] or label == p['name'].lower()]
            if len(products) != 1 or not 1 <= qty <= 999:
                raise ToolError(f'Please clarify “{clause}”: use a catalog product and quantity 1–999. No substitutions made.')
            sku = products[0]['sku']
            items[sku] = items.get(sku, 0) + qty
        return items

    def reply(self, owner, text='', photos=None):
        if not isinstance(owner, str) or not owner.strip() or not isinstance(text, str):
            raise ValueError('owner and text must be strings; owner cannot be empty')
        text = text.strip()
        if len(text) > 4000:
            return 'Message too long; please send a shorter order.'
        if photos:
            self.pending.pop(owner, None)
            return 'May photo kayo. Please type product names and quantities; I cannot reliably infer an order from shelf photos.'
        if text.lower() in ('cancel', 'kansela', 'huwag muna'):
            self.pending.pop(owner, None)
            return 'Cancelled the pending proposal. No new order placed.'
        confirmation = re.fullmatch(r'(?:confirm|kumpirma)\s+([a-f0-9]{12})', text.lower())
        if confirmation:
            qid = confirmation[1]
            q = self.pending.get(owner)
            if not q or q['id'] != qid:
                if self.completed.get(owner, {}).get('quote_id') == qid:
                    return f"Already placed: {self.completed[owner]['id']}. No duplicate order."
                return 'No matching pending quote. Please request an order first.'
            if q['total'] > 2000000 and not q.get('confirmed_once'):
                q['confirmed_once'] = True
                return f"Please CONFIRM {qid} again."
            
            try:
                
                order = self.tools.place_order(owner, qid)
            except ToolError as exc:
                self.pending.pop(owner, None)
                return str(exc)
            self.pending.pop(owner, None)
            self.completed[owner] = order
            return f"Order placed: {order['id']}. Total {money(order['total'])}. Salamat!"
        # Any non-confirmation message invalidates the prior proposal, including
        # unclear revisions, preventing confirmation of a superseded basket.
        self.pending.pop(owner, None)
        if text.lower() in ('yes', 'oo', 'sige', 'ok', 'confirm'):
            return 'For safety, request the order again, then reply CONFIRM followed by its exact quote ID.'
        try:
            items = self.parse(text)
            for sku, qty in items.items():
                if self.tools.stock(sku)['available'] < qty:
                    raise ToolError(f"Only {self.tools.stock(sku)['available']} units of {sku} available. Please revise quantities.")
            q = self.tools.quote(owner, items)
        except ToolError as exc:
            return str(exc)
        self.pending[owner] = q
        catalog = {p['sku']: p for p in self.tools.catalog()}
        lines = ['Proposed order (individual units):']
        for x in q['lines']:
            p = catalog[x['sku']]
            lines.append(f"{x['quantity']} × {p['name']} @ {money(x['unit_price'])} = {money(x['subtotal'])}")
            if x['unit_price'] != p['catalog_price']:
                lines.append(f"Catalog price {money(p['catalog_price'])} was stale; live price used above.")
        lines += [f"Total: {money(q['total'])}. No delivery fee or extra tax in this mock.",
                  f"Valid for 5 minutes, subject to stock and price recheck. Reply CONFIRM {q['id']} to place, or CANCEL."]
        return '\n'.join(lines)


