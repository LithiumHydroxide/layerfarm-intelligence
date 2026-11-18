import os
import sys
from datetime import datetime

import streamlit as st

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from components.custom_charts import revenue_cost_chart, unit_economics_waterfall
from components.metric_cards import metric_row, section_header
from utils.db_manager import (
    append_credit_sale,
    database_exists,
    load_credit_sales,
    load_daily_records,
)
from utils.kpi_calculations import EGGS_PER_TRAY, financial_summary

@st.cache_data(ttl=60)
def cached_data():
    return load_daily_records(), load_credit_sales()


if not database_exists():
    st.error("Database not found. Run `python data/seed_data.py` first.")
    st.stop()

records, credit_sales = cached_data()
credit_message = st.session_state.get("credit_message")
if credit_message:
    del st.session_state["credit_message"]
    st.success(credit_message)

finances = financial_summary(records)
outstanding = float(
    credit_sales.loc[
        credit_sales["status"] == "Outstanding", "total_amount"
    ].sum()
) if not credit_sales.empty else 0.0

st.markdown(
    """
    <div class="page-heading">
        <h1>💰 Financial Intelligence</h1>
        <p>Unit economics, profitability trends and the credit sales ledger.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

metric_row(
    [
        {
            "title": "Total Revenue",
            "value": f"KES {finances['revenue']:,.0f}",
            "subtext": f"{finances['trays']:,} trays sold",
        },
        {
            "title": "Operating Costs",
            "value": f"KES {finances['total_costs']:,.0f}",
            "subtext": "Feed + labor + vet",
            "tone": "negative",
        },
        {
            "title": "Net Profit",
            "value": f"KES {finances['profit']:,.0f}",
            "subtext": f"Margin {finances['margin']:.1f}%",
            "tone": "positive" if finances["profit"] >= 0 else "negative",
        },
        {
            "title": "Accounts Receivable",
            "value": f"KES {outstanding:,.0f}",
            "subtext": "Outstanding credit sales",
            "tone": "negative" if outstanding > 0 else "positive",
        },
    ]
)

st.markdown("<br>", unsafe_allow_html=True)
waterfall_col, trend_col = st.columns([1, 1.2])

with waterfall_col:
    section_header("Unit Economics: Cost Build-up per Tray")
    st.plotly_chart(unit_economics_waterfall(finances), width="stretch")

with trend_col:
    section_header("30-Day Revenue vs Operating Costs")
    st.plotly_chart(revenue_cost_chart(records, 30), width="stretch")

st.markdown("<br>", unsafe_allow_html=True)
section_header("Credit Sales & Accounts Receivable")
ledger_col, form_col = st.columns([1.5, 1])

with form_col:
    st.markdown(
        '<p style="color:#94A3B8; font-size:0.9rem;">Log a sale on credit to a wholesaler or retailer.</p>',
        unsafe_allow_html=True,
    )
    with st.form("credit_sale_form", clear_on_submit=True):
        buyer = st.text_input("Buyer Name", placeholder="e.g. Nakuru Wholesalers")
        trays = st.number_input("Number of Trays", min_value=1, value=50, step=10)
        price = st.number_input("Price per Tray (KES)", min_value=300, value=450, step=10)
        submitted_credit = st.form_submit_button(
            "💾 Log Credit Sale", width="stretch", type="primary"
        )

        if submitted_credit:
            if not buyer.strip():
                st.error("Enter the buyer name.")
            else:
                total_amount = trays * price
                append_credit_sale(
                    {
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "buyer_name": buyer.strip(),
                        "trays_sold": trays,
                        "price_per_tray": price,
                        "total_amount": total_amount,
                        "status": "Outstanding",
                    }
                )
                st.cache_data.clear()
                st.session_state["credit_message"] = (
                    f"Logged KES {total_amount:,.0f} credit sale to {buyer}."
                )
                st.rerun()

with ledger_col:
    if credit_sales.empty:
        st.info("No credit sales recorded yet. Use the form to log the first one.")
    else:
        st.dataframe(
            credit_sales[
                ["date", "buyer_name", "trays_sold", "total_amount", "status"]
            ].head(10),
            width="stretch",
            hide_index=True,
            column_config={
                "date": "Date",
                "buyer_name": "Buyer",
                "trays_sold": "Trays",
                "total_amount": st.column_config.NumberColumn("Amount (KES)"),
                "status": "Status",
            },
        )

st.caption(f"Tray size: {EGGS_PER_TRAY} eggs • other costs modelled at 25% of feed cost")
