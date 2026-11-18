import html

import streamlit as st

TONE_COLORS = {
    "positive": "#10B981",
    "negative": "#EF4444",
    "warning": "#F59E0B",
    "info": "#3B82F6",
}


def _escape(value):
    return html.escape(str(value))


def section_header(text):
    st.markdown(
        f'<div class="section-header">{_escape(text)}</div>',
        unsafe_allow_html=True,
    )


def metric_card(title, value, subtext="", tone="positive"):
    subtext_class = "negative" if tone in ("negative", "warning") else ""
    st.markdown(
        f"""
        <div class="glass-card">
            <div class="card-title">{_escape(title)}</div>
            <div class="card-value">{_escape(value)}</div>
            <div class="card-subtext {subtext_class}">{_escape(subtext)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_row(cards):
    columns = st.columns(len(cards))
    for column, card in zip(columns, cards):
        with column:
            metric_card(**card)


def alert_card(icon, title, body, tone="positive"):
    color = TONE_COLORS.get(tone, TONE_COLORS["positive"])
    st.markdown(
        f"""
        <div class="glass-card" style="border-left: 4px solid {color}; margin-bottom: 15px; padding: 16px;">
            <h4 style="color: #F8FAFC; margin: 0 0 8px 0;">{_escape(icon)} {_escape(title)}</h4>
            <p style="color: #CBD5E1; margin: 0; line-height: 1.6; font-size: 0.95rem;">{_escape(body)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def feature_card(icon, title, body):
    st.markdown(
        f"""
        <div class="glass-card" style="height: 100%;">
            <div style="font-size: 2rem; margin-bottom: 12px;">{_escape(icon)}</div>
            <div class="card-title" style="font-size: 1rem; margin-bottom: 8px;">{_escape(title)}</div>
            <p style="color: #CBD5E1; margin: 0; line-height: 1.6; font-size: 0.9rem;">{_escape(body)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
