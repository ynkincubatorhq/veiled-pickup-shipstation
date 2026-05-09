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


def _require_access_code() -> None:
    """Gate the app behind a shared access code.

    The code is read from st.secrets["app_password"]. On Streamlit Cloud,
    set it in the deploy's Advanced settings -> Secrets. Locally, put it
    in .streamlit/secrets.toml (gitignored). Once entered, the unlock
    persists for the session.
    """
    if st.session_state.get("authed"):
        return

    st.title("Pickup orders -> ShipStation")
    st.caption("Enter the access code to continue.")
    code = st.text_input("Access code", type="password", label_visibility="collapsed")
    if not code:
        st.stop()

    expected = ""
    try:
        expected = st.secrets.get("app_password", "")
    except (FileNotFoundError, Exception):  # noqa: BLE001 -- secrets.toml missing
        expected = ""

    if not expected:
        st.error(
            "Access code is not configured. Contact the app owner — "
            "`app_password` needs to be set in Streamlit Cloud secrets."
        )
        st.stop()

    if code != expected:
        st.error("Incorrect access code.")
        st.stop()

    st.session_state.authed = True
    st.rerun()


_require_access_code()

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
