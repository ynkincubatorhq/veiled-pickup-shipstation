"""Map a Shopify orders_export.csv into a ShipStation import CSV.

Shopify exports one row per line item, with order/customer info only on the
first row of each order. ShipStation uses the same shape, so this module
forward-fills order-level fields, filters to pickup orders, and rewrites each
row into the ShipStation column layout.
"""
from __future__ import annotations

import io
from datetime import datetime

import pandas as pd

# Opt in to the future ffill behavior (no silent dtype downcasting). This
# silences a FutureWarning emitted by pandas >= 2.2 when forward-filling
# object columns.
pd.set_option("future.no_silent_downcasting", True)

from config import (
    ORDER_SOURCE,
    PICKUP_TAGS,
    SHIPPING_SERVICE,
    SHIPSTATION_COLUMNS,
    STORE_ADDRESS,
)

# Shopify columns whose value lives only on the first row of each order.
ORDER_LEVEL_COLS = [
    "Email",
    "Financial Status",
    "Fulfillment Status",
    "Paid at",
    "Created at",
    "Total",
    "Subtotal",
    "Shipping",
    "Taxes",
    "Shipping Method",
    "Notes",
    "Billing Name",
    "Billing Street",
    "Billing Address1",
    "Billing Address2",
    "Billing Company",
    "Billing City",
    "Billing Zip",
    "Billing Province",
    "Billing Country",
    "Billing Phone",
    "Phone",
    "Tags",
]


def _safe(value) -> str:
    """Return '' for NaN/None, otherwise the string value."""
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value)


def _split_name(full_name: str) -> tuple[str, str]:
    name = _safe(full_name).strip()
    if not name:
        return "", ""
    parts = name.split(maxsplit=1)
    return (parts[0], parts[1]) if len(parts) == 2 else (parts[0], "")


def _parse_tags(tags_value) -> list[str]:
    raw = _safe(tags_value)
    if not raw:
        return []
    return [t.strip() for t in raw.split(",") if t.strip()]


def _format_date(value) -> str:
    """Shopify gives e.g. '2026-05-08 11:21:58 -0400'. ShipStation accepts a
    plain MM/DD/YYYY which is what its sample uses."""
    raw = _safe(value)
    if not raw:
        return ""
    try:
        return datetime.strptime(raw[:10], "%Y-%m-%d").strftime("%m/%d/%Y")
    except ValueError:
        return raw


def _propagate_order_level(df: pd.DataFrame) -> pd.DataFrame:
    """Forward-fill order-level fields within each order group so every line
    item row has the order/customer info attached to it."""
    df = df.copy()
    df["Name"] = df["Name"].ffill()
    for col in ORDER_LEVEL_COLS:
        if col in df.columns:
            df[col] = df.groupby("Name")[col].transform(lambda s: s.ffill())
    return df


def filter_pickup_orders(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only rows for orders that:
      - are unfulfilled (so we exclude 'Ready for pickup' and fulfilled ones)
      - have at least one of the pickup-location tags
    """
    df = _propagate_order_level(df)
    fulfillment = df.get("Fulfillment Status", pd.Series([""] * len(df)))
    is_unfulfilled = fulfillment.fillna("").astype(str).str.lower() == "unfulfilled"
    has_pickup_tag = df["Tags"].apply(
        lambda t: bool(set(_parse_tags(t)) & PICKUP_TAGS)
    )
    return df[is_unfulfilled & has_pickup_tag].copy()


def to_shipstation(shopify_df: pd.DataFrame) -> pd.DataFrame:
    """Convert filtered Shopify rows to ShipStation rows (one row per item)."""
    rows = []
    for _, r in shopify_df.iterrows():
        billing_name = _safe(r.get("Billing Name"))
        first, last = _split_name(billing_name)
        store_name = STORE_ADDRESS["name"]
        store_first, store_last = _split_name(store_name)

        rows.append({
            "Order #": _safe(r.get("Name")),
            "Order Date": _format_date(r.get("Created at")),
            "Date Paid": _format_date(r.get("Paid at")),
            "Order Total": _safe(r.get("Total")),
            "Amount Paid": _safe(r.get("Total")),
            "Tax": _safe(r.get("Taxes")),
            "Shipping Paid": _safe(r.get("Shipping")),
            "Shipping Service": SHIPPING_SERVICE,
            "Height(in)": "",
            "Length(in)": "",
            "Width(in)": "",
            "Weight(oz)": "",
            "Custom Field 1": "",
            "Custom Field 2": "",
            "Custom Field 3": ", ".join(_parse_tags(r.get("Tags"))),
            "Order Source": ORDER_SOURCE,
            "Notes to the Buyer": "",
            "Notes from the Buyer": _safe(r.get("Notes")),
            "Internal Notes": "",
            "Gift Message": "",
            "Gift Flag": "FALSE",
            "Buyer Full Name": billing_name,
            "Buyer First Name": first,
            "Buyer Last Name": last,
            "Buyer Email": _safe(r.get("Email")),
            "Buyer Phone": _safe(r.get("Billing Phone")) or _safe(r.get("Phone")),
            "Buyer Username": _safe(r.get("Email")),
            "Recipient Full Name": store_name,
            "Recipient First Name": store_first,
            "Recipient Last Name": store_last,
            "Recipient Phone": STORE_ADDRESS["phone"],
            "Recipient Company": STORE_ADDRESS["company"],
            "Address Line 1": STORE_ADDRESS["address_line_1"],
            "Address Line 2": STORE_ADDRESS["address_line_2"],
            "Address Line 3": STORE_ADDRESS["address_line_3"],
            "City": STORE_ADDRESS["city"],
            "State": STORE_ADDRESS["state"],
            "Postal Code": STORE_ADDRESS["postal_code"],
            "Country Code": STORE_ADDRESS["country_code"],
            "Item SKU": _safe(r.get("Lineitem sku")),
            "Item Name / Title": _safe(r.get("Lineitem name")),
            "Item Quantity": _safe(r.get("Lineitem quantity")),
            "Item Unit Price": _safe(r.get("Lineitem price")),
            "Item Weight (oz)": "",
            "Item Options": "",
            "Item Warehouse Location": "",
            "Item Marketplace ID": "",
        })

    return pd.DataFrame(rows, columns=SHIPSTATION_COLUMNS)


def process(csv_bytes: bytes) -> tuple[pd.DataFrame, dict]:
    """Top-level entry point: bytes in, (DataFrame, stats) out."""
    df = pd.read_csv(io.BytesIO(csv_bytes), dtype=str)
    filtered = filter_pickup_orders(df)
    out = to_shipstation(filtered)

    input_orders = (
        df["Name"].ffill().nunique() if "Name" in df.columns and len(df) else 0
    )
    stats = {
        "input_rows": int(len(df)),
        "input_orders": int(input_orders),
        "output_orders": int(out["Order #"].nunique()) if not out.empty else 0,
        "output_rows": int(len(out)),
    }
    return out, stats
