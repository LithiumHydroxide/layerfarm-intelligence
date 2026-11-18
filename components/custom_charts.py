import pandas as pd
import plotly.graph_objects as go

from utils.kpi_calculations import BREED_TARGET_PROD

COLORS = {
    "emerald": "#10B981",
    "blue": "#3B82F6",
    "cyan": "#06B6D4",
    "amber": "#F59E0B",
    "red": "#EF4444",
    "slate": "#94A3B8",
}


def _theme(height=350, legend=False, margins=None, **overrides):
    layout = {
        "template": "plotly_dark",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "paper_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": "#F8FAFC"},
        "height": height,
        "margin": margins or dict(l=20, r=20, t=30, b=20),
        "hoverlabel": {"bgcolor": "#1E293B", "bordercolor": "#334155"},
    }
    if legend:
        layout["legend"] = dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        )
    layout.update(overrides)
    return layout


def _chronological(df, days):
    frame = df.head(days).copy()
    frame["date"] = pd.to_datetime(frame["date"])
    return frame.sort_values("date")


def production_trend(df, days=7):
    recent = _chronological(df, days)
    fig = go.Figure(
        go.Scatter(
            x=recent["date"],
            y=recent["eggs_collected"],
            mode="lines+markers",
            fill="tozeroy",
            fillcolor="rgba(16, 185, 129, 0.15)",
            line=dict(color=COLORS["emerald"], width=3),
            marker=dict(size=6),
            name="Eggs Collected",
            hovertemplate="<b>%{x|%b %d}</b><br>Eggs: %{y}<extra></extra>",
        )
    )
    fig.update_layout(
        **_theme(
            xaxis=dict(showgrid=False, color=COLORS["slate"]),
            yaxis=dict(
                showgrid=True,
                gridcolor="rgba(255,255,255,0.05)",
                color=COLORS["slate"],
                title={"text": "Eggs", "font": {"size": 12}},
            ),
        )
    )
    return fig


def production_gauge(value, target=BREED_TARGET_PROD):
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=value,
            number={"suffix": "%", "font": {"color": "#F8FAFC", "size": 40}},
            delta={
                "reference": target,
                "increasing": {"color": COLORS["emerald"]},
                "decreasing": {"color": COLORS["red"]},
            },
            gauge={
                "axis": {"range": [0, 100], "tickcolor": COLORS["slate"]},
                "bar": {"color": COLORS["emerald"], "thickness": 0.2},
                "bgcolor": "rgba(0,0,0,0)",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 70], "color": "rgba(239, 68, 68, 0.1)"},
                    {"range": [70, 85], "color": "rgba(251, 191, 36, 0.1)"},
                    {"range": [85, 100], "color": "rgba(16, 185, 129, 0.1)"},
                ],
                "threshold": {
                    "line": {"color": COLORS["amber"], "width": 4},
                    "thickness": 0.8,
                    "value": target,
                },
            },
        )
    )
    fig.update_layout(
        **_theme(
            margins=dict(l=20, r=20, t=50, b=20),
            annotations=[
                {
                    "text": f"Target: {target:.0f}%",
                    "x": 0.5,
                    "y": 0.15,
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {"color": COLORS["slate"], "size": 14},
                }
            ],
        )
    )
    return fig


def egg_quality_donut(good, cracked, dirty):
    fig = go.Figure(
        go.Pie(
            labels=["Good Eggs", "Cracked", "Dirty"],
            values=[good, cracked, dirty],
            hole=0.45,
            marker=dict(
                colors=[COLORS["emerald"], COLORS["red"], COLORS["amber"]]
            ),
            hoverinfo="label+percent+value",
            textinfo="label+percent",
        )
    )
    fig.update_layout(**_theme(showlegend=False))
    return fig


def revenue_cost_chart(df, days=30):
    recent = _chronological(df, days)
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=recent["date"],
            y=recent["daily_feed_cost_kes"] * 1.25,
            name="Daily Costs",
            marker_color=COLORS["red"],
            opacity=0.8,
            hovertemplate="<b>%{x|%b %d}</b><br>Costs: KES %{y:,.0f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=recent["date"],
            y=recent["daily_revenue_kes"],
            name="Daily Revenue",
            line=dict(color=COLORS["emerald"], width=3),
            fill="tozeroy",
            fillcolor="rgba(16, 185, 129, 0.1)",
            hovertemplate="<b>%{x|%b %d}</b><br>Revenue: KES %{y:,.0f}<extra></extra>",
        )
    )
    fig.update_layout(
        **_theme(
            height=400,
            legend=True,
            barmode="overlay",
            xaxis=dict(showgrid=False, color=COLORS["slate"]),
            yaxis=dict(
                showgrid=True,
                gridcolor="rgba(255,255,255,0.05)",
                color=COLORS["slate"],
                tickprefix="KES ",
            ),
        )
    )
    return fig


def unit_economics_waterfall(summary):
    fig = go.Figure(
        go.Waterfall(
            name="Cost Build-up",
            orientation="v",
            measure=["relative", "relative", "relative", "total", "relative", "total"],
            x=["Feed Cost", "Labor & Vet", "Transport", "Total Costs", "Net Profit", "Selling Price"],
            textposition="outside",
            text=[
                f"KES {summary['feed_cost_per_tray']:.0f}",
                f"KES {summary['other_cost_per_tray'] * 0.6:.0f}",
                f"KES {summary['other_cost_per_tray'] * 0.4:.0f}",
                f"KES {summary['total_costs'] / max(1, summary['trays']):.0f}",
                f"KES {summary['profit_per_tray']:.0f}",
                f"KES {summary['price_per_tray']:.0f}",
            ],
            y=[
                summary["feed_cost_per_tray"],
                summary["other_cost_per_tray"] * 0.6,
                summary["other_cost_per_tray"] * 0.4,
                summary["feed_cost_per_tray"] + summary["other_cost_per_tray"],
                summary["profit_per_tray"],
                summary["price_per_tray"],
            ],
            connector={"line": {"color": "rgba(255,255,255,0.2)"}},
            increasing={"marker": {"color": COLORS["emerald"]}},
            decreasing={"marker": {"color": COLORS["red"]}},
            totals={"marker": {"color": COLORS["blue"]}},
        )
    )
    fig.update_layout(
        **_theme(
            height=400,
            showlegend=False,
            xaxis=dict(showgrid=False, color=COLORS["slate"]),
            yaxis=dict(showgrid=False, visible=False),
        )
    )
    return fig


def forecast_chart(forecast):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=forecast["dates"],
            y=forecast["upper"],
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=forecast["dates"],
            y=forecast["lower"],
            mode="lines",
            line=dict(width=0),
            fill="tonexty",
            fillcolor="rgba(16, 185, 129, 0.15)",
            showlegend=False,
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=forecast["dates"],
            y=forecast["base"],
            mode="lines",
            line=dict(color=COLORS["emerald"], width=3, dash="dash"),
            name="Forecasted Eggs",
            hovertemplate="<b>%{x|%b %d}</b><br>Forecast: %{y:.0f} eggs<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=forecast["history"]["date"],
            y=forecast["history"]["eggs_collected"],
            mode="lines",
            line=dict(color=COLORS["blue"], width=2),
            name="Actual (Last 30 Days)",
            hovertemplate="<b>%{x|%b %d}</b><br>Actual: %{y} eggs<extra></extra>",
        )
    )
    fig.update_layout(
        **_theme(
            height=450,
            legend=True,
            xaxis=dict(showgrid=False, color=COLORS["slate"]),
            yaxis=dict(
                showgrid=True,
                gridcolor="rgba(255,255,255,0.05)",
                color=COLORS["slate"],
            ),
        )
    )
    return fig


def anomaly_chart(df, anomalies):
    history = df.copy()
    history["date"] = pd.to_datetime(history["date"])
    history = history.sort_values("date")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=history["date"],
            y=history["eggs_collected"],
            mode="lines",
            line=dict(color=COLORS["blue"], width=2),
            name="Eggs Collected",
            yaxis="y1",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=history["date"],
            y=history["water_consumed_liters"],
            mode="lines",
            line=dict(color=COLORS["cyan"], width=2, dash="dot"),
            name="Water Consumed (L)",
            yaxis="y2",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=anomalies["date"],
            y=anomalies["eggs_collected"],
            mode="markers",
            marker=dict(
                color=COLORS["red"],
                size=14,
                symbol="x",
                line=dict(width=2, color="white"),
            ),
            name="Anomaly Detected",
            yaxis="y1",
            hovertemplate="<b>&#9888; ANOMALY</b><br>Date: %{x|%b %d}<br>Eggs: %{y}<extra></extra>",
        )
    )
    fig.update_layout(
        **_theme(
            height=400,
            legend=True,
            margins=dict(l=50, r=50, t=30, b=20),
            xaxis=dict(showgrid=False, color=COLORS["slate"]),
            yaxis=dict(
                title="Eggs",
                color=COLORS["blue"],
                showgrid=True,
                gridcolor="rgba(255,255,255,0.05)",
            ),
            yaxis2=dict(
                title="Water (Liters)",
                color=COLORS["cyan"],
                overlaying="y",
                side="right",
                showgrid=False,
            ),
        )
    )
    return fig


def actual_vs_simulated(actual, simulated):
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=["Revenue", "Total Costs", "Net Profit"],
            y=[actual["revenue"], actual["total_costs"], actual["profit"]],
            name="Actual (Last 30 Days)",
            marker_color=[COLORS["blue"], COLORS["amber"], COLORS["emerald"]],
            opacity=0.6,
            hovertemplate="<b>Actual</b><br>%{x}: KES %{y:,.0f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            x=["Revenue", "Total Costs", "Net Profit"],
            y=[simulated["revenue"], simulated["total_costs"], simulated["profit"]],
            name="Simulated (Next 30 Days)",
            marker_color=["#60A5FA", "#FBBF24", "#34D399"],
            hovertemplate="<b>Simulated</b><br>%{x}: KES %{y:,.0f}<extra></extra>",
        )
    )
    fig.update_layout(
        **_theme(
            height=400,
            legend=True,
            barmode="group",
            xaxis=dict(showgrid=False, color="#F8FAFC", tickfont=dict(size=14)),
            yaxis=dict(
                showgrid=True,
                gridcolor="rgba(255,255,255,0.05)",
                color=COLORS["slate"],
                tickprefix="KES ",
            ),
        )
    )
    return fig
