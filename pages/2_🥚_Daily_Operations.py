import os
import sys
from datetime import datetime

import streamlit as st

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from components.custom_charts import egg_quality_donut
from components.metric_cards import alert_card, metric_row, section_header
from utils.db_manager import append_daily_record, load_latest_record
from utils.kpi_calculations import (
    EGG_PRICE_KES,
    FEED_PRICE_PER_KG,
    feed_conversion_ratio,
    hen_day_production,
    live_birds,
)

st.markdown(
    """
    <div class="page-heading">
        <h1>🥚 Daily Operations</h1>
        <p>Log today's farm activity and recalculate biological and financial KPIs in real time.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


def save_daily_log(eggs, cracked, dirty, feed_kg, water_l, dead_birds, latest):
    birds_at_start = live_birds(latest["birds_alive_start"], latest["mortality"])
    day_age = int(latest["day_age"]) + 1
    good_eggs = eggs - cracked - dirty
    append_daily_record(
        {
            "date": datetime.now(),
            "day_age": day_age,
            "week_age": day_age // 7,
            "birds_alive_start": birds_at_start,
            "eggs_collected": eggs,
            "cracked_eggs": cracked,
            "dirty_eggs": dirty,
            "good_eggs": good_eggs,
            "feed_consumed_kg": round(feed_kg, 2),
            "water_consumed_liters": round(water_l, 2),
            "mortality": dead_birds,
            "daily_revenue_kes": (good_eggs // 30) * EGG_PRICE_KES,
            "daily_feed_cost_kes": round(feed_kg * FEED_PRICE_PER_KG, 2),
        }
    )
    st.cache_data.clear()
    return {
        "birds_at_start": birds_at_start,
        "day_age": day_age,
        "week_age": day_age // 7,
        "good_eggs": good_eggs,
        "cracked": cracked,
        "dirty": dirty,
        "production": hen_day_production(eggs, birds_at_start),
        "fcr": feed_conversion_ratio(feed_kg, good_eggs),
        "mortality_rate": hen_day_production(dead_birds, birds_at_start),
        "revenue": (good_eggs // 30) * EGG_PRICE_KES,
    }


latest = load_latest_record()
if latest is None:
    st.error("No baseline data found. Seed the database first.")
    st.stop()

start_birds = live_birds(latest["birds_alive_start"], latest["mortality"])

with st.form("daily_ops_form", clear_on_submit=True):
    section_header("Today's Farm Log")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            '<p style="color:#10B981; font-weight:600;">Flock Status</p>',
            unsafe_allow_html=True,
        )
        st.metric("Birds Alive (Start)", f"{start_birds:,}")
        dead_birds = st.number_input(
            "Mortality (Dead Birds)", min_value=0, max_value=50, value=0, step=1
        )

    with col2:
        st.markdown(
            '<p style="color:#10B981; font-weight:600;">Egg Collection</p>',
            unsafe_allow_html=True,
        )
        eggs_total = st.number_input(
            "Total Eggs Collected",
            min_value=0,
            max_value=max(1, start_birds),
            value=int(start_birds * 0.92),
            step=1,
        )
        eggs_cracked = st.number_input(
            "Cracked Eggs", min_value=0, max_value=max(1, eggs_total), value=5, step=1
        )
        eggs_dirty = st.number_input(
            "Dirty Eggs", min_value=0, max_value=max(1, eggs_total), value=8, step=1
        )

    with col3:
        st.markdown(
            '<p style="color:#10B981; font-weight:600;">Feed & Water</p>',
            unsafe_allow_html=True,
        )
        feed_kg = st.number_input(
            "Feed Issued (kg)",
            min_value=0.0,
            value=round(start_birds * 0.115, 1),
            step=0.5,
        )
        water_l = st.number_input(
            "Water Consumed (Liters)",
            min_value=0.0,
            value=round(start_birds * 0.23, 1),
            step=0.5,
        )

    with col4:
        st.markdown(
            '<p style="color:#10B981; font-weight:600;">Submission</p>',
            unsafe_allow_html=True,
        )
        st.write("Review the entries above before saving.")
        submitted = st.form_submit_button(
            "💾 Calculate & Save to Farm Log",
            width="stretch",
            type="primary",
        )

if not submitted:
    st.info("Complete the form and submit to calculate today's KPIs.")
    st.stop()

if eggs_cracked + eggs_dirty > eggs_total:
    st.error("Cracked and dirty eggs cannot exceed total eggs collected.")
    st.stop()

with st.spinner("Calculating biological and financial KPIs..."):
    results = save_daily_log(
        eggs_total, eggs_cracked, eggs_dirty, feed_kg, water_l, dead_birds, latest
    )

st.success(
    f"Saved week {results['week_age']}, day {results['day_age']} to the farm log."
)

section_header("Real-Time KPI Update")
metric_row(
    [
        {
            "title": "Hen-Day Production",
            "value": f"{results['production']:.1f}%",
            "subtext": "Target above 90%",
            "tone": "positive" if results["production"] >= 90 else "negative",
        },
        {
            "title": "Daily FCR",
            "value": f"{results['fcr']:.2f}",
            "subtext": "Target below 2.3",
            "tone": "positive" if results["fcr"] <= 2.3 else "negative",
        },
        {
            "title": "Mortality Rate",
            "value": f"{results['mortality_rate']:.2f}%",
            "subtext": "Target below 0.10%",
            "tone": "positive" if results["mortality_rate"] < 0.1 else "negative",
        },
        {
            "title": "Today's Revenue",
            "value": f"KES {results['revenue']:,}",
            "subtext": f"{results['good_eggs']} good eggs",
        },
    ]
)

st.markdown("<br>", unsafe_allow_html=True)
chart_col, insight_col = st.columns([1, 1.2])

with chart_col:
    section_header("Egg Quality Breakdown")
    st.plotly_chart(
        egg_quality_donut(
            results["good_eggs"], results["cracked"], results["dirty"]
        ),
        width="stretch",
    )

with insight_col:
    section_header("AI Farm Insights & Alerts")
    insights = []
    if results["production"] < 85:
        insights.append(
            ("⚠️", "Production Drop", "Below 85%. Check heat, water supply and disease stress.", "warning")
        )
    if results["fcr"] > 2.4:
        insights.append(
            ("📉", "Feed Efficiency", f"FCR {results['fcr']:.2f}. Check feed quality and trough wastage.", "negative")
        )
    if results["mortality_rate"] > 0.15:
        insights.append(
            ("🚨", "Mortality Alert", "Isolate affected birds and consult your vet.", "negative")
        )
    total_eggs = results["good_eggs"] + results["cracked"] + results["dirty"]
    if total_eggs and (results["cracked"] + results["dirty"]) / total_eggs > 0.02:
        insights.append(
            ("🥚", "Egg Quality", "Check nest box padding and collection frequency.", "warning")
        )
    if not insights:
        insights.append(
            ("✅", "Optimal Performance", "All systems green. Flock is within breed parameters.", "positive")
        )
    for icon, title, body, tone in insights:
        alert_card(icon, title, body, tone)
