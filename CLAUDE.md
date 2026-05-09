# CLAUDE.md — veiled-pickup-shipstation

This file orients AI agents (Claude Code, Cursor, any other code-writing assistant) working in this repository. Humans should keep it accurate; agents read it on every run.

## Read this first

This Project is licensed under the Suraya Methodology and Platform License (see [LICENSE-suraya.md](LICENSE-suraya.md)). The org-wide engineering charter — roles, stack, branch protection, CODEOWNERS rules, AI agent rules — lives in the canonical Suraya repository:

- `https://github.com/surayainc/suraya/blob/main/ENGINEERING_OPERATING_MODEL.md`

This file (CLAUDE.md) is project-specific context layered on top of that operating model. If something here contradicts the operating model, the operating model wins and this file is the bug.

## What this project is

A small Streamlit web app that maps Shopify pickup-order CSV exports into ShipStation v3 import format for Veiled retail operations. The Streamlit UI is the only writer; the mapping logic lives in `mapper.py`. Hosting is Streamlit Community Cloud (subject to migration; not load-bearing on the operating model's hosting standard).

Owner: @kareem-ynk
Stack: Streamlit (Python) + pandas
Hosting: Streamlit Community Cloud (temporary; subject to migration)

## Conventions specific to this project

- Pickup orders are filtered by Shopify tags from the set in `config.PICKUP_TAGS` (`pickupmolablvd`, `pickupcliftononly`, `cliftonpickupsplit`) AND by `Fulfillment Status == unfulfilled`. "Ready for pickup" orders are deliberately dropped.
- Recipient address on every output row is hardcoded to the Veiled Clifton store via `config.STORE_ADDRESS`. Buyer info comes from the Shopify customer's billing block.
- The output column order in `config.SHIPSTATION_COLUMNS` matches ShipStation's v3 sample import template. Don't reorder without re-verifying against ShipStation's expectation.
- The test fixture at `tests/sample_orders_export.csv` is **anonymized** — names, emails, addresses, phones, and payment refs have been replaced with synthetic values that preserve the column shape, order IDs, tags, fulfillment statuses, and line-item counts the tests assert on. Do not commit raw Shopify exports here; future fixtures should follow the same anonymization pattern.

## Things that will trip you up

- Shopify exports put order-level fields only on the first row of each order; subsequent line-item rows leave them blank. `mapper.py` forward-fills before filtering — don't drop that step.
- ShipStation's location-routing reads `Shipping Service`, NOT a separate `Requested Service` column, in this configuration. If a future ShipStation import doesn't route to the correct location, that's the first place to look — flip it in `config.SHIPPING_SERVICE` mapping.
- The `Custom Field 3` column carries the Shopify tags comma-separated; tests assert non-empty. Don't repurpose that column.

## Agent rules for this repository

- Only write to: anywhere except `tests/sample_orders_export.csv` (anonymized fixture is intentional; modifying it could re-introduce real customer data if an agent tries to "regenerate" from a live export — never do that without anonymizing first).
- Never commit raw Shopify exports. Anonymize first via the same surgical PII-replacement pattern used in `tests/sample_orders_export.csv`.
- You never merge your own PR. Open as draft, hand off to a human reviewer.
- Per the operating model, you do not write to production secrets or deploy. Deploys are human-only via Streamlit Community Cloud.
