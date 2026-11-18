import os

import streamlit as st

from utils.db_manager import DB_PATH, load_farm_settings

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CSS_PATH = os.path.join(BASE_DIR, "assets", "style.css")


def apply_theme():
    if os.path.exists(CSS_PATH):
        with open(CSS_PATH, encoding="utf-8") as css_file:
            st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)


def build_pages(home_page):
    return {
        "home": st.Page(home_page, title="Home", icon="🏠"),
        "dashboard": st.Page(
            "pages/1_📊_Dashboard.py", title="Dashboard", icon="📊"
        ),
        "operations": st.Page(
            "pages/2_🥚_Daily_Operations.py",
            title="Daily Operations",
            icon="🥚",
        ),
        "financials": st.Page(
            "pages/3_💰_Financials.py", title="Financials", icon="💰"
        ),
        "simulator": st.Page(
            "pages/4_🔮_Simulator.py",
            title="Simulator & Forecasts",
            icon="🔮",
        ),
    }


def render_sidebar():
    settings = load_farm_settings()
    with st.sidebar:
        st.markdown(
            """
            <div class="brand-block">
                <div class="brand-egg">🥚</div>
                <div class="brand-name">LayerFarm</div>
                <div class="brand-tagline">INTELLIGENCE</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="nav-caption">WORKSPACE</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="glass-card" style="padding: 16px;">
                <p class="card-title" style="margin-bottom: 8px;">Active Farm</p>
                <p style="color: #F8FAFC; font-size: 0.95rem; font-weight: 600; margin: 0 0 4px 0;">
                    {settings.get('farm_name', 'Demo Farm')}
                </p>
                <p style="color: #CBD5E1; font-size: 0.8rem; margin: 0;">📍 {settings.get('location', 'Kiambu, Kenya')}</p>
                <p style="color: #CBD5E1; font-size: 0.8rem; margin: 4px 0 0 0;">🐔 {settings.get('breed', 'Hy-Line Brown')}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.session_state.get("reset_done"):
            st.session_state["reset_done"] = False
            st.success("Demo data restored to 90 days.")

        if st.button("🔄 Reset Demo Data", width="stretch"):
            from data.seed_data import seed_database

            seed_database(DB_PATH)
            st.cache_data.clear()
            st.session_state["reset_done"] = True
            st.rerun()
