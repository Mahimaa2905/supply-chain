
import os
import pandas as pd
import streamlit as st
import plotly.express as px

from databricks import sql
from databricks.sdk import WorkspaceClient
from databricks.sdk.core import Config


# ---------------- APP CONFIGURATION ----------------

st.set_page_config(
    page_title="Supply Chain 360",
    page_icon="📦",
    layout="wide"
)

st.title("📦 Supply Chain 360")
st.caption("End-to-End Supply Chain Analytics & Performance")

WAREHOUSE_ID = os.getenv("DATABRICKS_WAREHOUSE_ID")
JOB_ID = os.getenv("SUPPLY_CHAIN_JOB_ID")

TABLES = {
    "suppliers": "workspace.gold.gold_supplier_performance",
    "shipments": "workspace.gold.gold_shipment_analytics",
    "products": "workspace.gold.gold_product_analytics",
    "delivery": "workspace.gold.gold_delivery_performance",
    "inventory": "workspace.gold.gold_inventory_reorder",
    "monthly": "workspace.gold.gold_monthly_supply_chain"
}


# ---------------- DATABRICKS CONNECTION ----------------

@st.cache_resource
def get_workspace_client():
    return WorkspaceClient()


def get_connection():
    if not WAREHOUSE_ID:
        raise ValueError(
            "SQL Warehouse resource is missing. "
            "Check the app resources and app.yaml."
        )

    cfg = Config()
    host = cfg.host.replace("https://", "").replace("http://", "")

    return sql.connect(
        server_hostname=host,
        http_path=f"/sql/1.0/warehouses/{WAREHOUSE_ID}",
        credentials_provider=lambda: cfg.authenticate
    )


@st.cache_data(ttl=300)
def load_table(table_name):
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table_name}")
            return cursor.fetchall_arrow().to_pandas()
    finally:
        conn.close()


def load_all_data():
    return {
        name: load_table(table)
        for name, table in TABLES.items()
    }


# ---------------- SIDEBAR ----------------

st.sidebar.title("Supply Chain 360")

page = st.sidebar.radio(
    "Navigation",
    ["Executive Overview", "Operational Analysis"]
)

st.sidebar.divider()
st.sidebar.subheader("Pipeline Management")

st.sidebar.caption(
    "Run the complete Azure Blob → Bronze → Silver → "
    "Quarantine → Gold pipeline."
)

if JOB_ID:

    if st.sidebar.button(
        "▶ Run Supply Chain Pipeline",
        type="primary",
        use_container_width=True
    ):
        try:
            client = get_workspace_client()

            run = client.jobs.run_now(
                job_id=int(JOB_ID)
            )

            st.session_state["run_id"] = run.run_id

            st.sidebar.success(
                f"Pipeline started. Run ID: {run.run_id}"
            )

        except Exception as e:
            st.sidebar.error(f"Job execution failed: {e}")

else:
    st.sidebar.warning("Job resource is not configured.")

if "run_id" in st.session_state:

    st.sidebar.write(
        f"Latest Run ID: {st.session_state['run_id']}"
    )

    if st.sidebar.button("Refresh Job Status"):

        try:
            client = get_workspace_client()

            run = client.jobs.get_run(
                run_id=int(st.session_state["run_id"])
            )

            state = run.state

            lifecycle = getattr(
                state.life_cycle_state, "value",
                str(state.life_cycle_state)
            )

            result = getattr(
                state.result_state, "value",
                str(state.result_state)
            ) if state.result_state else "Not finished"

            st.session_state["job_lifecycle"] = lifecycle
            st.session_state["job_result"] = result

        except Exception as e:
            st.sidebar.error(str(e))

    if "job_lifecycle" in st.session_state:
        st.sidebar.write(
            f"**Lifecycle:** {st.session_state['job_lifecycle']}"
        )
        st.sidebar.write(
            f"**Result:** {st.session_state['job_result']}"
        )


if st.sidebar.button("Refresh Gold Data"):
    st.cache_data.clear()
    st.rerun()


# ---------------- LOAD GOLD TABLES ----------------

try:
    with st.spinner("Loading Gold analytics..."):
        data = load_all_data()

    suppliers = data["suppliers"]
    shipments = data["shipments"]
    products = data["products"]
    delivery = data["delivery"]
    inventory = data["inventory"]
    monthly = data["monthly"]

except Exception as e:
    st.error("Unable to load Gold tables.")
    st.exception(e)

    st.info(
        "Check SQL Warehouse permission, SELECT permissions "
        "on all six Gold tables, and the app resource configuration."
    )
    st.stop()


# ====================================================
# PAGE 1: EXECUTIVE OVERVIEW
# ====================================================

if page == "Executive Overview":

    st.header("Executive Overview")

    total_shipments = len(shipments)

    total_units = (
        shipments["quantity"].sum()
        if "quantity" in shipments.columns else 0
    )

    total_suppliers = shipments["supplier_id"].nunique()
    total_products = shipments["product_id"].nunique()

    on_time = (
        shipments["delivery_performance"] == "ON TIME"
    ).sum()

    delayed = (
        shipments["delivery_performance"] == "DELAYED"
    ).sum()

    on_time_percentage = (
        on_time / total_shipments * 100
        if total_shipments else 0
    )

    # KPI CARDS

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total Shipments", f"{total_shipments:,}")
    c2.metric("Units Shipped", f"{total_units:,.0f}")
    c3.metric("Active Suppliers", f"{total_suppliers:,}")
    c4.metric("Products Shipped", f"{total_products:,}")

    c5, c6, c7 = st.columns(3)

    c5.metric("On-Time Delivery", f"{on_time_percentage:.2f}%")
    c6.metric("Delayed Shipments", f"{delayed:,}")
    c7.metric("On-Time Shipments", f"{on_time:,}")

    # FINANCIAL VALUE BY CURRENCY

    st.subheader("Shipment Value by Currency")

    value_currency = (
        shipments.groupby("currency", as_index=False)
        ["total_amount"].sum()
    )

    st.dataframe(
        value_currency,
        use_container_width=True,
        hide_index=True
    )

    st.caption("Different currencies are not combined.")

    # MONTHLY TREND

    left, right = st.columns(2)

    with left:

        st.subheader("Monthly Shipment Trend")

        trend = (
            monthly.groupby("shipment_month", as_index=False)
            ["total_shipments"].sum()
            .sort_values("shipment_month")
        )

        fig = px.line(
            trend,
            x="shipment_month",
            y="total_shipments",
            markers=True
        )

        st.plotly_chart(fig, use_container_width=True)

    with right:

        st.subheader("Shipment Status")

        status = (
            shipments["shipment_status"]
            .value_counts()
            .reset_index()
        )

        status.columns = ["Status", "Count"]

        fig = px.pie(
            status,
            names="Status",
            values="Count",
            hole=0.5
        )

        st.plotly_chart(fig, use_container_width=True)

    # TOP SUPPLIERS

    left, right = st.columns(2)

    with left:

        st.subheader("Top 10 Suppliers")

        top_suppliers = (
            suppliers.groupby("supplier_name", as_index=False)
            ["total_shipments"].sum()
            .nlargest(10, "total_shipments")
        )

        fig = px.bar(
            top_suppliers,
            x="total_shipments",
            y="supplier_name",
            orientation="h"
        )

        st.plotly_chart(fig, use_container_width=True)

    with right:

        st.subheader("Top 10 Products")

        top_products = (
            products.groupby("product_name", as_index=False)
            ["total_units_shipped"].sum()
            .nlargest(10, "total_units_shipped")
        )

        fig = px.bar(
            top_products,
            x="total_units_shipped",
            y="product_name",
            orientation="h"
        )

        st.plotly_chart(fig, use_container_width=True)


# ====================================================
# PAGE 2: OPERATIONAL ANALYSIS
# ====================================================

else:

    st.header("Operational Performance & Analysis")

    # SHIPMENT FILTERS

    st.subheader("Shipment Explorer")

    filtered = shipments.copy()

    c1, c2, c3 = st.columns(3)

    currencies = (
        ["All"] +
        sorted(filtered["currency"].dropna().unique().tolist())
    )

    selected_currency = c1.selectbox(
        "Currency", currencies
    )

    if selected_currency != "All":
        filtered = filtered[
            filtered["currency"] == selected_currency
        ]

    statuses = (
        ["All"] +
        sorted(filtered["shipment_status"].dropna().unique().tolist())
    )

    selected_status = c2.selectbox(
        "Shipment Status", statuses
    )

    if selected_status != "All":
        filtered = filtered[
            filtered["shipment_status"] == selected_status
        ]

    modes = (
        ["All"] +
        sorted(filtered["transport_mode"].dropna().unique().tolist())
    )

    selected_mode = c3.selectbox(
        "Transport Mode", modes
    )

    if selected_mode != "All":
        filtered = filtered[
            filtered["transport_mode"] == selected_mode
        ]

    st.metric("Matching Shipments", f"{len(filtered):,}")

    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True
    )

    # DELIVERY PERFORMANCE

    st.subheader("Delivery Performance by Transport Mode")

    delivery_summary = (
        delivery.groupby("transport_mode", as_index=False)
        .agg(
            on_time=("on_time_shipments", "sum"),
            total=("total_shipments", "sum")
        )
    )

    delivery_summary["on_time_percentage"] = (
        delivery_summary["on_time"] /
        delivery_summary["total"] * 100
    )

    fig = px.bar(
        delivery_summary,
        x="transport_mode",
        y="on_time_percentage",
        title="On-Time Delivery by Transport Mode"
    )

    st.plotly_chart(fig, use_container_width=True)

    # PRODUCT CATEGORY

    st.subheader("Product Category Analysis")

    category_summary = (
        products.groupby("category", as_index=False)
        ["total_units_shipped"].sum()
    )

    fig = px.bar(
        category_summary,
        x="category",
        y="total_units_shipped"
    )

    st.plotly_chart(fig, use_container_width=True)

    # INVENTORY REVIEW

    st.subheader("Inventory Reorder Review")

    st.info(
        "This is a historical reorder review. Actual stock-on-hand "
        "information is not available in this dataset."
    )

    if "reorder_review_status" in inventory.columns:

        review_status = (
            ["All"] +
            sorted(
                inventory["reorder_review_status"]
                .dropna().unique().tolist()
            )
        )

        selected_review = st.selectbox(
            "Reorder Review Status", review_status
        )

        inventory_view = inventory.copy()

        if selected_review != "All":
            inventory_view = inventory_view[
                inventory_view["reorder_review_status"] == selected_review
            ]

        st.dataframe(
            inventory_view,
            use_container_width=True,
            hide_index=True
        )

    # SUPPLIER DETAILS

    st.subheader("Supplier Performance")

    st.dataframe(
        suppliers,
        use_container_width=True,
        hide_index=True
    )


st.divider()
st.caption("Supply Chain 360 | Powered by Databricks")
