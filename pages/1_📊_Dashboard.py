import os
import sys

import streamlit as st

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from components.custom_charts import production_gauge, production_trend
from components.metric_cards import alert_card, metric_row, section_header
from utils.db_manager import database_exists, load_daily_records, load_farm_settings
from utils.kpi_calculations import (
    BREED_TARGET_PROD,
    financial_summary,
    snapshot,
)


@st.cache_data
def cached_data():
    return load_daily_records(), load_farm_settings()


if not database_exists():
    st.error("Database not found. Run `python data/seed_data.py` first.")
    st.stop()

records, settings = cached_data()
if records.empty:
    st.info("No records yet. Log your first day under Daily Operations.")
    st.stop()

today = snapshot(records)
finances = financial_summary(records.head(30))

st.markdown(
    """
    <div class="page-heading">
        <h1>📊 Farm Dashboard</h1>
        <p>Live biological and financial performance for your laying flock.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

metric_row(
    [
        {
            "title": "Live Flock",
            "value": f"{today['live_birds']:,}",
            "subtext": f"{int(today['latest']['mortality'])} lost today",
            "tone": "negative" if today["latest"]["mortality"] else "positive",
        },
        {
            "title": "Hen-Day Production",
            "value": f"{today['production']:.1f}%",
            "subtext": f"{today['production_change']:+.1f}% vs yesterday",
            "tone": "positive" if today["production_change"] >= 0 else "negative",
        },
        {
            "title": "Daily FCR",
            "value": f"{today['fcr']:.2f}",
            "subtext": "Target below 2.3",
            "tone": "positive" if today["fcr"] <= 2.3 else "negative",
        },
        {
            "title": "30-Day Net Profit",
            "value": f"KES {finances['profit']:,.0f}",
            "subtext": f"Margin {finances['margin']:.1f}%",
            "tone": "positive" if finances["profit"] > 0 else "negative",
        },
    ]
)

st.markdown("<br>", unsafe_allow_html=True)
trend_col, gauge_col = st.columns([1.2, 1])

with trend_col:
    section_header("7-Day Production Trend")
    st.plotly_chart(production_trend(records, 7), width="stretch")

with gauge_col:
    section_header("Production vs Breed Benchmark")
    st.plotly_chart(
        production_gauge(today["production"], BREED_TARGET_PROD), width="stretch"
    )

st.markdown("<br>", unsafe_allow_html=True)
section_header("AI Farm Insight")
status = "above" if today["production"] > BREED_TARGET_PROD else "on par with"
alert_card(
    "💡",
    "Production advisory",
    (
        f"{settings.get('farm_name', 'This farm')} is in week "
        f"{int(today['latest']['week_age'])} and performing {status} the breed standard "
        f"({today['production']:.1f}% vs {BREED_TARGET_PROD:.0f}%). Feed intake is stable at "
        f"{float(today['latest']['feed_consumed_kg']):.1f} kg. Flush water lines daily as "
        "afternoon temperatures rise in Kiambu."
    ),
)

st.caption(
    f"{len(records)} daily records • latest {today['latest']['date']} • source: data/database.db"
)
