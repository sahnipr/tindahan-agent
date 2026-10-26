# Assumed pricing rules

These rules were created for this submission; no original pricing.md was supplied.

1. Currency is PHP. All internal amounts are integer centavos; display two decimals.
2. Catalog prices may be stale and must never be used as final order prices.
3. The quote tool reads the authoritative live price source, validates stock, and issues an immutable quote with a five-minute expiry. No offline price fallback.
4. Display each product, unit, quantity, live unit price, line subtotal, and total before requesting confirmation. Disclose any difference from catalog pricing.
5. An owner confirms with `CONFIRM <quote-id>` or `KUMPIRMA <quote-id>`. Generic “yes”, “oo”, and “sige” do not authorize checkout.
6. Checkout atomically validates ownership, expiry, current prices and inventory, then decrements stock and records an order. Any price change (up or down) rejects the quote: request a new proposal and confirmation. Do not silently charge a changed total.
7. Stock is not reserved while waiting. Insufficient stock rejects the entire basket. No partial fulfillment, substitutions, case conversion, discounts, credit terms, delivery charge or additional tax in this sandbox. Prices are assumed tax-inclusive.
8. A quote ID is an idempotency key. Repeating checkout returns the original order without another stock decrement. A completed order remains retrievable by the tool after quote expiry.
9. Pricing outages block quoting and checkout. Never guess a price.

The separate live price source is an explicit architectural assumption. If the real integration only provides an unreliable catalog and no authoritative quote/checkout guarantee, automated placement must remain disabled and an agent must verify the price with a human.
