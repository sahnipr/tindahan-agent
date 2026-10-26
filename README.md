# Tindahan ordering agent

A runnable Python prototype that converts constrained mixed Tagalog/English messages into catalog-backed proposals and places orders only after explicit confirmation. No dependencies, API keys, or paid AI service required. Python 3.10+.

## Run

```sh
python3 demo.py
```

Try `pabili po 2 sardinas at 3 kopiko brown`, then copy the exact `CONFIRM <id>` command printed in the proposal. The total is **PHP 76.00**: 2 × 26.00 + 3 × 8.00. The catalog sardine price of PHP 24.00 is deliberately stale.

```sh
python3 -m unittest discover -s tests -v
python3 replay.py
python3 server.py
```

The optional HTTP sandbox listens at `http://127.0.0.1:8000`:

```sh
curl -X POST http://127.0.0.1:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"owner":"store-001","text":"pabili po 2 sardinas at 3 kopiko brown"}'
```

POST the same owner and `"text":"CONFIRM <returned-id>"` to place it. Mock read/quote endpoints are `/catalog` (`{}`), `/stock` (`{"sku":"sardines"}`), `/quote` (`{"owner":"store-001","items":{"sardines":2}}`). The order tool is an internal Python method invoked through `/chat` after confirmation; there is intentionally no public checkout endpoint. See `schemas/tools.json` for input/output contracts. All state resets on restart.

## What was supplied versus assumed

Only the brief was supplied. `conversations/*.json`, API implementations/contracts, and `pricing.md` here are **invented samples**, not supplied company resources. The three products, brands, variants, prices, available quantities, five-minute expiry, individual-unit ordering and order policy are assumptions. The 2,000 stores are context, not a claimed load test.

`agent.py` orchestrates catalog lookup → parsing/clarification → stock lookup → live quote → owner confirmation → atomic checkout. `tools.py` mocks catalog, stock, quote and order APIs. `server.py` exposes a local testing interface. The HTTP owner ID simulates an authenticated identity; it is not real authentication.

## Stale prices and order safety

Catalog prices are indicative. An added authoritative quote source supplies current prices; differences are disclosed. Checkout rechecks price and stock under one lock. An expired quote, changed price (including a decrease), unavailable pricing source or reduced stock blocks placement. The owner must request a fresh quote and confirm again. See `pricing.md` for all rules and the critical assumption about an authoritative price source.

Quote IDs bind confirmation to the exact basket and owner. A repeated confirmation does not create another order; the tool uses the quote ID as an idempotency key. Revisions, cancellation, photos and unclear non-confirmation messages invalidate the pending quote. Quotes do not reserve stock. No automatic substitutions or partial orders.

## Language and photos: deliberate limits

This is a deterministic agent with a small bilingual parser, **not an LLM or general Tagalog understanding system**. It supports numeric quantities followed by known names/aliases, optional individual-unit words, and comma/semicolon/“at”/“and” separators. Supported prefixes include “pabili po”, “paorder po” and “please order”. For example: `2 cans sardinas, 3 sachets kopiko brown`.

Unknown brands, variants, number words, cases, unclear quantities and unsupported text trigger clarification. Generic “kape” is mapped to the only coffee SKU in this tiny catalog; a larger catalog must disambiguate variants. The parser consumes the whole message rather than extracting a potentially incomplete basket. It does not remember partial clarifications: resend the complete revised basket.

Photo attachments are acknowledged, but image content is not analyzed. The agent asks the owner to type product names and quantities and does not infer stock demand from empty shelves. This is a safe fallback rather than a claim of implemented vision support.

## Validation and tradeoffs

The unit suite covers live versus stale pricing, explicit confirmation, invalidated revisions, photos, unknown units, stock shortages, expiry, pricing outages, owner isolation, cancellation, duplicate checkout and concurrent stock contention. `replay.py` also executes the sample JSON conversations against a fresh sandbox each time. Only the tool transaction is thread-safe; agent turns must be serialized per owner (the supplied HTTP server is single-threaded).

The dependency-free design is easy to inspect and run, but language coverage is narrow, all data is in memory, and mock failures are raised synchronously. It does not provide production authentication, durable idempotency, real network retries/timeouts, store authorization, a messaging integration, or image understanding. Do not expose this sandbox publicly.

## What I would do next

1. Confirm actual product units, pricing authority, tax/delivery terms, and store identity rules with the business.
2. Replace the parser with constrained structured extraction and multilingual evaluation, keeping catalog validation and checkout authorization outside the model. Use OCR/vision only to propose candidates, never infer quantities without confirmation.
3. Persist quotes/orders and enforce atomic stock and idempotency in a database, serialize owner sessions, authenticate webhooks, and add bounded retries/timeouts with safe order-status reconciliation.
4. Add human handoff, monitoring, real conversation evaluations, accessibility/usability testing for confirmation, and load tests for 2,000 stores.

## AI tools declaration and commit history

OpenAI ChatGPT/Codex generated the prototype code, mock data, tests and documentation, and ran the local verification commands in this submission. No other AI service is called by the application. The deterministic parser was chosen to make the example reproducible without credentials. AI assistance is substantive and is disclosed here; the submitter should review and understand the solution before submitting it.

Commits were made incrementally during this build using the environment's Codex author identity. Timestamps were not altered. The included local `.git` history is preserved in the downloadable archive. GitHub publication is a separate step requiring an authenticated GitHub connection; a local repository or archive does not satisfy the public repository requirement by itself.

To publish manually after extracting (GitHub CLI required and authenticated):

```sh
gh repo create tindahan-agent --public --source=. --remote=origin --push
```

If using GitHub Desktop, add this existing repository and publish it with “Keep this code private” unchecked. Push the existing commits rather than uploading only the final files, so the build history remains visible.
