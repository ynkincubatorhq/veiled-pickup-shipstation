"""Sanity checks against the user's sample Shopify export."""
from pathlib import Path

import pandas as pd
import pytest

from config import PICKUP_TAGS, SHIPPING_SERVICE, SHIPSTATION_COLUMNS, STORE_ADDRESS
from mapper import filter_pickup_orders, process, to_shipstation

SAMPLE = Path(__file__).parent / "sample_orders_export.csv"


@pytest.fixture(scope="module")
def shopify_df() -> pd.DataFrame:
    return pd.read_csv(SAMPLE, dtype=str)


def test_every_filtered_row_has_pickup_tag(shopify_df):
    out = filter_pickup_orders(shopify_df)
    assert not out.empty, "sample should contain at least one pickup order"
    for tags in out["Tags"]:
        tag_set = {t.strip() for t in str(tags).split(",")}
        assert tag_set & PICKUP_TAGS, f"row missing pickup tag: {tags!r}"


def test_filter_drops_ready_for_pickup(shopify_df):
    out = filter_pickup_orders(shopify_df)
    statuses = {str(s).lower() for s in out["Fulfillment Status"]}
    assert statuses == {"unfulfilled"}


def test_shipstation_columns_match_template(shopify_df):
    out = to_shipstation(filter_pickup_orders(shopify_df))
    assert list(out.columns) == SHIPSTATION_COLUMNS


def test_recipient_is_store_address(shopify_df):
    out = to_shipstation(filter_pickup_orders(shopify_df))
    assert (out["Address Line 1"] == STORE_ADDRESS["address_line_1"]).all()
    assert (out["City"] == STORE_ADDRESS["city"]).all()
    assert (out["State"] == STORE_ADDRESS["state"]).all()
    assert (out["Postal Code"] == STORE_ADDRESS["postal_code"]).all()


def test_shipping_service_is_set(shopify_df):
    out = to_shipstation(filter_pickup_orders(shopify_df))
    assert (out["Shipping Service"] == SHIPPING_SERVICE).all()


def test_custom_field_3_contains_tags(shopify_df):
    out = to_shipstation(filter_pickup_orders(shopify_df))
    # Each row should carry a non-empty Custom Field 3 with at least one tag
    assert out["Custom Field 3"].str.len().gt(0).all()


def test_one_row_per_lineitem(shopify_df):
    """Order 862263 in the sample has many line items; ensure they survive."""
    out = to_shipstation(filter_pickup_orders(shopify_df))
    counts = out["Order #"].value_counts()
    # 862263 is the 37-item bulk order in the screenshot
    assert counts.get("862263", 0) >= 30


def test_process_returns_stats(shopify_df):
    csv_bytes = SAMPLE.read_bytes()
    out, stats = process(csv_bytes)
    assert stats["output_orders"] > 0
    assert stats["output_rows"] >= stats["output_orders"]
    assert len(out) == stats["output_rows"]
