from datetime import datetime, timedelta

import numpy as np
import pandas as pd

AVG_EGG_WEIGHT_KG = 0.06
EGGS_PER_TRAY = 30
EGG_PRICE_KES = 450
FEED_PRICE_PER_KG = 65
OTHER_COST_RATIO = 0.25
BREED_TARGET_PROD = 91.0
FEED_STOCK_KG = 50 * 70


def safe_divide(numerator, denominator, default=0.0):
    return numerator / denominator if denominator else default


def hen_day_production(eggs, birds):
    return safe_divide(eggs, birds) * 100


def feed_conversion_ratio(feed_kg, eggs):
    egg_mass_kg = eggs * AVG_EGG_WEIGHT_KG
    return safe_divide(feed_kg, egg_mass_kg)


def live_birds(birds_at_start, mortality):
    return max(0, int(birds_at_start) - int(mortality))


def snapshot(df):
    if df is None or df.empty:
        return None
    latest = df.iloc[0]
    previous = df.iloc[1] if len(df) > 1 else latest
    production = hen_day_production(
        latest["eggs_collected"], latest["birds_alive_start"]
    )
    previous_production = hen_day_production(
        previous["eggs_collected"], previous["birds_alive_start"]
    )
    return {
        "latest": latest,
        "production": production,
        "production_change": production - previous_production,
        "live_birds": live_birds(latest["birds_alive_start"], latest["mortality"]),
        "fcr": feed_conversion_ratio(
            latest["feed_consumed_kg"], latest["eggs_collected"]
        ),
    }


def financial_summary(df):
    if df is None or df.empty:
        return {
            "revenue": 0.0,
            "feed_cost": 0.0,
            "other_costs": 0.0,
            "total_costs": 0.0,
            "profit": 0.0,
            "margin": 0.0,
            "trays": 0,
            "feed_cost_per_tray": 0.0,
            "other_cost_per_tray": 0.0,
            "profit_per_tray": 0.0,
            "price_per_tray": 0.0,
        }

    revenue = float(df["daily_revenue_kes"].sum())
    feed_cost = float(df["daily_feed_cost_kes"].sum())
    other_costs = feed_cost * OTHER_COST_RATIO
    total_costs = feed_cost + other_costs
    profit = revenue - total_costs
    trays = int(df["good_eggs"].sum() // EGGS_PER_TRAY)

    return {
        "revenue": revenue,
        "feed_cost": feed_cost,
        "other_costs": other_costs,
        "total_costs": total_costs,
        "profit": profit,
        "margin": safe_divide(profit, revenue) * 100,
        "trays": trays,
        "feed_cost_per_tray": safe_divide(feed_cost, trays),
        "other_cost_per_tray": safe_divide(other_costs, trays),
        "profit_per_tray": safe_divide(profit, trays),
        "price_per_tray": safe_divide(revenue, trays),
    }


def detect_anomalies(df):
    if df is None or df.empty:
        return pd.DataFrame()

    scored = df.copy()
    scored["date"] = pd.to_datetime(scored["date"])
    egg_std = scored["eggs_collected"].std(ddof=0) or 1
    water_std = scored["water_consumed_liters"].std(ddof=0) or 1
    egg_mean = scored["eggs_collected"].mean()
    water_mean = scored["water_consumed_liters"].mean()

    scored["egg_zscore"] = (scored["eggs_collected"] - egg_mean) / egg_std
    scored["water_zscore"] = (
        scored["water_consumed_liters"] - water_mean
    ) / water_std
    return scored[
        (scored["water_zscore"] > 1.5) & (scored["egg_zscore"] < -1.5)
    ]


def production_forecast(df, days=30, feed_stock_kg=FEED_STOCK_KG):
    if df is None or df.empty:
        return None

    history = df.tail(30).copy()
    history["date"] = pd.to_datetime(history["date"])
    mean_eggs = history["eggs_collected"].mean()
    std_eggs = history["eggs_collected"].std(ddof=0) or 1

    future_dates = [datetime.now() + timedelta(days=offset) for offset in range(1, days + 1)]
    uncertainty = np.linspace(0.5, 2.5, days)
    base = np.full(days, mean_eggs)

    average_feed = float(df["feed_consumed_kg"].mean())
    days_until_stockout = safe_divide(feed_stock_kg, average_feed)

    return {
        "history": history,
        "dates": future_dates,
        "base": base,
        "upper": base + std_eggs * uncertainty,
        "lower": np.maximum(0, base - std_eggs * uncertainty),
        "days_until_stockout": days_until_stockout,
        "stockout_date": datetime.now() + timedelta(days=int(days_until_stockout)),
        "forecast_revenue": float(history["daily_revenue_kes"].mean()) * days,
    }


def simulate_month(
    flock_size,
    production_pct,
    feed_price_bag,
    egg_price_tray,
    days=30,
    eggs_per_tray=EGGS_PER_TRAY,
    kg_per_bag=70,
    daily_feed_per_bird=0.115,
):
    trays = safe_divide(flock_size * (production_pct / 100) * days, eggs_per_tray)
    revenue = trays * egg_price_tray
    feed_kg = flock_size * daily_feed_per_bird * days
    feed_cost = safe_divide(feed_kg, kg_per_bag) * feed_price_bag
    other_costs = feed_cost * OTHER_COST_RATIO
    total_costs = feed_cost + other_costs
    profit = revenue - total_costs

    return {
        "trays": trays,
        "revenue": revenue,
        "feed_cost": feed_cost,
        "other_costs": other_costs,
        "total_costs": total_costs,
        "profit": profit,
        "margin": safe_divide(profit, revenue) * 100,
        "break_even_price": safe_divide(total_costs, trays),
    }
