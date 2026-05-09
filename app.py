"""Streamlit UI: drop a Shopify orders_export.csv, get a ShipStation import CSV."""
from __future__ import annotations

from datetime import datetime

import streamlit as st

from mapper import process

st.set_page_config(
    page_title="Pickup orders to ShipStation",
    page_icon=":package:",
    layout="centered",
)

st.title("Pickup orders -> ShipStation")
st.caption(
    "Upload the Shopify orders export. Pickup orders that are NOT 'Ready for "
    "pickup' get rewritten into the ShipStation import format."
)

with st.expander("How to use", expanded=False):
    st.markdown(
        "1. In Shopify Admin, filter Orders by `Fulfillment status: Unfulfilled` "
        "and `Delivery method: Pickup in store`.\n"
        "2. Bulk-select the orders, click **Export**, choose the orders CSV.\n"
        "3. Drop the file below.\n"
        "4. Download the resulting CSV and import it in ShipStation under "
        "**Orders -> Import Orders**."
    )

uploaded = st.file_uploader(
    "Shopify orders_export.csv",
    type=["csv"],
    accept_multiple_files=False,
)

if uploaded is None:
    st.stop()

with st.spinner("Mapping orders..."):
    csv_bytes = uploaded.getvalue()
    out_df, stats = process(csv_bytes)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Input rows", stats["input_rows"])
c2.metric("Input orders", stats["input_orders"])
c3.metric("Pickup orders", stats["output_orders"])
c4.metric("Output rows", stats["output_rows"])

if out_df.empty:
    st.warning(
        "No pickup orders matched. Double-check the export contains `Tags` and "
        "`Fulfillment Status` columns and that orders carry one of: "
        "`pickupmolablvd`, `pickupcliftononly`, `cliftonpickupsplit`."
    )
    st.stop()

st.subheader("Preview")
st.dataframe(out_df.head(50), use_container_width=True)

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_out = out_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download ShipStation CSV",
    data=csv_out,
    file_name=f"shipstation_pickup_{stamp}.csv",
    mime="text/csv",
    use_container_width=True,
)
