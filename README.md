# Pickup orders -> ShipStation

Streamlit app that turns a Shopify orders export into a ShipStation import CSV
for in-store pickup orders that ShipStation isn't pulling automatically.

## What it does

1. Reads a Shopify `orders_export.csv` (one row per line item).
2. Forward-fills order-level fields (Shopify only puts them on the first row of
   each order).
3. Keeps only orders that are:
   - `Fulfillment Status` = `unfulfilled` (so "Ready for pickup" orders are
     dropped), AND
   - tagged with one of `pickupmolablvd`, `pickupcliftononly`,
     `cliftonpickupsplit`.
4. Rewrites each row into the ShipStation v3 import column layout, with:
   - Recipient = Veiled Clifton store address
   - Buyer = Shopify customer's billing info
   - `Shipping Service` = `Veiled Clifton`
   - `Custom Field 3` = the order's Shopify tags, comma-separated
   - `Order Source` = `Shopify`

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
mkdir -p .streamlit
echo 'app_password = "<your-code>"' > .streamlit/secrets.toml
streamlit run app.py
```

Open the URL Streamlit prints, enter the access code, drop a CSV, hit
download, upload to ShipStation under **Orders -> Import Orders**.

`.streamlit/secrets.toml` is gitignored and never leaves your machine.
The deployed app reads `app_password` from Streamlit Cloud's deploy
secrets; the value there is the canonical access code.

## Tests

```bash
pytest -q
```

The test suite uses a sanitized sample export at
`tests/sample_orders_export.csv`.

## Configuration

`config.py` holds the store address, pickup-tag set, and ShipStation column
order. Edit those values rather than hardcoding inside `mapper.py`.

## Files

- `app.py` - Streamlit UI
- `mapper.py` - filter + column mapping (the actual work)
- `config.py` - tunables (store address, tag list, column order)
- `tests/test_mapper.py` - sanity checks against the sample export
