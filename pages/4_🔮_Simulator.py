import os
import sys

import numpy as np
import streamlit as st

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from components.custom_charts import (
    actual_vs_simulated,
    anomaly_chart,
    forecast_chart,
)
from components.metric_cards import alert_card, metric_row, section_header
from utils.db_manager import database_exists, load_daily_records
from utils.kpi_calculations import (
    detect_anomalies,
    financial_summary,
    production_forecast,
    simulate_month,
)

@st.cache_data
def cached_data():
    return load_daily_records()


if not database_exists():
    st.error("Database not found. Run `python data/seed_data.py` first.")
    st.stop()

records = cached_data()
if records.empty:
    st.info("No records yet. Seed the database first.")
    st.stop()

actual = financial_summary(records.head(30))
actual_birds = int(records.head(30)["birds_alive_start"].mean())
actual_production = (
    records.head(30)["eggs_collected"].sum() / max(1, actual_birds * 30) * 100
)

st.markdown(
    """
    <div class="page-heading">
        <h1>🔮 Simulator & Forecasts</h1>
        <p>Test pricing and flock scenarios, then look ahead at feed stock and production risk.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

simulator_tab, forecast_tab = st.tabs(["🎛️ What-If Simulator", "📈 Forecast & Alerts"])

with simulator_tab:
    control_col, result_col = st.columns([1, 1.5])

    with control_col:
        section_header("Simulation Parameters")
        flock_size = st.slider(
            "🐔 Flock Size (Birds)",
            min_value=500,
            max_value=5000,
            value=min(5000, max(500, actual_birds)),
            step=100,
        )
        production_pct = st.slider(
            "🥚 Hen-Day Production (%)",
            min_value=60.0,
            max_value=98.0,
            value=float(np.clip(actual_production, 60.0, 98.0)),
            step=0.5,
        )
        feed_price_bag = st.slider(
            "🌾 Feed Price (KES per 70kg Bag)",
            min_value=3000,
            max_value=6000,
            value=4200,
            step=50,
        )
        egg_price_tray = st.slider(
            "🍳 Egg Price (KES per Tray)",
            min_value=300,
            max_value=700,
            value=450,
            step=10,
        )
        st.info("Tip: raise feed price to KES 5,000 to see the impact on profit.")

    with result_col:
        simulated = simulate_month(
            flock_size, production_pct, feed_price_bag, egg_price_tray
        )
        section_header("Simulated Monthly Financials")
        metric_row(
            [
                {
                    "title": "Projected Revenue",
                    "value": f"KES {simulated['revenue']:,.0f}",
                    "subtext": f"{simulated['trays']:,.0f} trays / month",
                },
                {
                    "title": "Projected Costs",
                    "value": f"KES {simulated['total_costs']:,.0f}",
                    "subtext": f"Feed: KES {simulated['feed_cost']:,.0f}",
                    "tone": "negative",
                },
                {
                    "title": "Net Profit",
                    "value": f"KES {simulated['profit']:,.0f}",
                    "subtext": f"Margin {simulated['margin']:.1f}%",
                    "tone": "positive" if simulated["profit"] >= 0 else "negative",
                },
            ]
        )
        st.markdown("<br>", unsafe_allow_html=True)

        if egg_price_tray < simulated["break_even_price"]:
            alert_card(
                "🚨",
                "Loss Alert",
                f"At KES {egg_price_tray}/tray you are below the break-even price of "
                f"KES {simulated['break_even_price']:.0f}/tray. Projected loss: "
                f"KES {abs(simulated['profit']):,.0f} per month.",
                "negative",
            )
        else:
            alert_card(
                "✅",
                "Profitable Scenario",
                f"Selling KES {egg_price_tray - simulated['break_even_price']:.0f} above "
                f"break-even. Projected profit: KES {simulated['profit']:,.0f} per month.",
                "positive",
            )

        section_header("Actual vs Simulated")
        st.plotly_chart(
            actual_vs_simulated(actual, simulated), width="stretch"
        )

with forecast_tab:
    forecast = production_forecast(records)
    anomalies = detect_anomalies(records)

    metric_row(
        [
            {
                "title": "Forecasted 30-Day Revenue",
                "value": f"KES {forecast['forecast_revenue']:,.0f}",
                "subtext": "Based on current flock performance",
            },
            {
                "title": "Projected Stock-Out",
                "value": forecast["stockout_date"].strftime("%b %d, %Y"),
                "subtext": f"{int(forecast['days_until_stockout'])} days of feed remaining",
                "tone": "negative" if forecast["days_until_stockout"] < 14 else "positive",
            },
            {
                "title": "Anomalies Detected",
                "value": f"{len(anomalies)} Events",
                "subtext": "Historical stress / health flags",
                "tone": "negative" if not anomalies.empty else "positive",
            },
        ]
    )

    st.markdown("<br>", unsafe_allow_html=True)
    section_header("30-Day Egg Production Forecast")
    st.plotly_chart(forecast_chart(forecast), width="stretch")

    st.markdown("<br>", unsafe_allow_html=True)
    section_header("Anomaly Detection")
    st.markdown(
        '<p style="color:#94A3B8; font-size:0.9rem;">Flags days when water intake spiked while egg production dropped — often heat stress, illness or a leaking water line.</p>',
        unsafe_allow_html=True,
    )

    if anomalies.empty:
        alert_card(
            "✅",
            "No anomalies detected",
            "Water and egg production stayed within normal variation across the recorded period.",
            "positive",
        )
    else:
        st.plotly_chart(anomaly_chart(records, anomalies), width="stretch")
        for _, row in anomalies.iterrows():
            alert_card(
                "⚠️",
                f"Anomaly on {row['date'].strftime('%b %d, %Y')}",
                f"Water spiked to {row['water_consumed_liters']:.1f} L while eggs fell to "
                f"{int(row['eggs_collected'])}. Check for leaks or heat stress.",
                "negative",
            )
