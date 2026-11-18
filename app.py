import os
import sys
from datetime import datetime

import streamlit as st

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from components.metric_cards import alert_card, feature_card, metric_row, section_header
from components.navigation import apply_theme, build_pages, render_sidebar
from utils.db_manager import database_exists, load_daily_records, load_farm_settings
from utils.kpi_calculations import financial_summary, snapshot

st.set_page_config(
    page_title="LayerFarm Intelligence",
    page_icon="🥚",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data
def cached_data():
    return load_daily_records(), load_farm_settings()


def home_page():
    if not database_exists():
        st.error("Database not found. Run `python data/seed_data.py` first.")
        return

    records, settings = cached_data()
    today = snapshot(records)
    finances = financial_summary(records.head(30))

    st.markdown(
        f"""
        <div class="hero">
            <h1>🥚 LayerFarm Intelligence</h1>
            <p>
                {settings.get('farm_name', 'Demo Farm')} &nbsp;•&nbsp;
                {settings.get('location', 'Kiambu, Kenya')} &nbsp;•&nbsp;
                {settings.get('breed', 'Hy-Line Brown')}<br>
                Live production, health and profitability signals for your laying flock —
                updated from the farm log, not a spreadsheet.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    section_header("Farm at a glance")
    if today:
        metric_row(
            [
                {
                    "title": "Live Flock",
                    "value": f"{today['live_birds']:,}",
                    "subtext": f"Mortality today: {int(today['latest']['mortality'])}",
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
    else:
        st.info("No records yet. Log your first day under Daily Operations.")

    st.markdown("<br>", unsafe_allow_html=True)
    section_header("Explore the workspace")

    feature_col1, feature_col2 = st.columns(2)
    with feature_col1:
        feature_card(
            "📊",
            "Dashboard",
            "KPI cards, seven-day production trend and the breed benchmark gauge.",
        )
        st.page_link(pages["dashboard"], label="Open Dashboard →")
        feature_card(
            "💰",
            "Financials",
            "Revenue, unit economics, operating costs and the credit sales ledger.",
        )
        st.page_link(pages["financials"], label="Open Financials →")

    with feature_col2:
        feature_card(
            "🥚",
            "Daily Operations",
            "Enter eggs, feed, water and mortality; KPIs recalculate instantly.",
        )
        st.page_link(pages["operations"], label="Open Daily Operations →")
        feature_card(
            "🔮",
            "Simulator & Forecasts",
            "What-if pricing, feed stock-out dates and anomaly alerts.",
        )
        st.page_link(pages["simulator"], label="Open Simulator →")

    st.markdown("<br>", unsafe_allow_html=True)
    section_header("Latest farm insight")
    if today:
        alert_card(
            "✅" if today["production"] >= 90 else "⚠️",
            "Production signal",
            (
                f"Week {int(today['latest']['week_age'])} flock is at "
                f"{today['production']:.1f}% hen-day production against a 91% breed target. "
                f"Feed intake is {float(today['latest']['feed_consumed_kg']):.1f} kg for the day. "
                "Keep water lines flushed during afternoon heat."
            ),
            "positive" if today["production"] >= 90 else "warning",
        )

    st.markdown(
        f"<p style='color:#64748B; font-size:0.8rem; text-align:center;'>Last updated {datetime.now().strftime('%b %d, %Y • %H:%M')}</p>",
        unsafe_allow_html=True,
    )


apply_theme()
render_sidebar()

pages = build_pages(home_page)
selected_page = st.navigation(list(pages.values()), position="sidebar")
selected_page.run()
