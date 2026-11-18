import sqlite3
import pandas as pd
import numpy as np
import os

def seed_database(db_path="data/database.db"):
    """Generates 90 days of realistic Kenyan layer farm data."""
    
    # Ensure data directory exists
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    
    # Delete existing DB to start fresh
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    
    # Farm Parameters (Kenyan Context)
    initial_birds = 1000
    start_day_age = 140 # 20 Weeks (Point of lay for Hy-Line Brown)
    days_to_simulate = 90
    
    # Financial parameters (KES)
    egg_price_per_tray = 450 
    eggs_per_tray = 30
    feed_price_per_kg = 65 # Approx KES 65/kg for quality layer mash
    
    data = []
    current_birds = initial_birds
    
    np.random.seed(42) # For reproducible "random" farm fluctuations
    
    for i in range(days_to_simulate):
        day_age = start_day_age + i
        week_age = day_age // 7
        
        # 1. Biological Curves (Hy-Line Brown Standard)
        # Production curve: Starts ~5%, peaks at ~94% around week 28-30
        if week_age < 24:
            base_prod = 0.05 + (week_age - 20) * 0.15
        elif week_age < 32:
            base_prod = 0.85 + np.sin((week_age - 24) * 0.4) * 0.09
        else:
            base_prod = 0.92 - (week_age - 32) * 0.005
            
        # Add realistic daily noise (+/- 2%)
        daily_prod = max(0, min(1, base_prod + np.random.normal(0, 0.015)))
        
        # 2. Feed Intake Curve (g/bird/day)
        base_feed_intake = 90 + (week_age - 20) * 2.5
        if week_age > 30: base_feed_intake = 115 
        
        # 3. Calculate Daily Metrics
        eggs_collected = int(current_birds * daily_prod)
        feed_consumed_kg = (current_birds * base_feed_intake * (1 + np.random.normal(0, 0.02))) / 1000
        
        # 4. Quality & Mortality
        cracked_eggs = int(eggs_collected * np.random.uniform(0.005, 0.015))
        dirty_eggs = int(eggs_collected * np.random.uniform(0.01, 0.02))
        
        # Mortality: ~0.05% per week during peak
        daily_mortality_rate = 0.0005 + np.random.uniform(0, 0.0002)
        dead_birds = np.random.choice([0, 1], p=[1-daily_mortality_rate, daily_mortality_rate])
        
        # Water intake (approx 2x feed intake in liters)
        water_consumed = feed_consumed_kg * 2.0 * (1 + np.random.normal(0, 0.05))
        
        # 5. Financials
        good_eggs = eggs_collected - cracked_eggs - dirty_eggs
        trays_sold = good_eggs // eggs_per_tray
        daily_revenue = trays_sold * egg_price_per_tray
        daily_feed_cost = feed_consumed_kg * feed_price_per_kg
        
        data.append({
            "date": pd.Timestamp.today() - pd.Timedelta(days=(days_to_simulate - 1 - i)),
            "day_age": day_age,
            "week_age": week_age,
            "birds_alive_start": current_birds,
            "eggs_collected": eggs_collected,
            "cracked_eggs": cracked_eggs,
            "dirty_eggs": dirty_eggs,
            "good_eggs": good_eggs,
            "feed_consumed_kg": round(feed_consumed_kg, 2),
            "water_consumed_liters": round(water_consumed, 2),
            "mortality": dead_birds,
            "daily_revenue_kes": daily_revenue,
            "daily_feed_cost_kes": round(daily_feed_cost, 2)
        })
        
        # Update flock size for next day
        current_birds -= dead_birds

    df = pd.DataFrame(data)
    df.to_sql('daily_records', conn, if_exists='replace', index=False)
    
    # Create a settings table for farm metadata
    settings = pd.DataFrame([{
        "farm_name": "Kiambu Greenfields Ltd",
        "location": "Kiambu, Kenya",
        "breed": "Hy-Line Brown",
        "initial_birds": initial_birds,
        "current_birds": current_birds
    }])
    settings.to_sql('farm_settings', conn, if_exists='replace', index=False)
    
    conn.close()
    print(f"✅ Database seeded successfully at {db_path} with {len(df)} days of data.")

if __name__ == "__main__":
    seed_database()