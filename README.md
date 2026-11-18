# LayerFarm Intelligence

A Streamlit decision-support app for a commercial layer farm. It turns a simple daily farm log into live production, health and profitability signals, then lets you forecast risk and run what-if pricing scenarios. The bundled demo models a 1,000-bird Hy-Line Brown flock in Kiambu, Kenya over a 90-day greenfield cycle.

## What the app does

| Page | Purpose |
| --- | --- |
| **🏠 Home** (`app.py`) | Landing page with the current flock snap-shot: live birds, hen-day production, daily FCR, 30-day net profit, and a short advisory. Links to every workspace page. |
| **📊 Dashboard** | The operational view: four KPI cards, a 7-day egg collection trend, and a gauge comparing hen-day production with the 91% Hy-Line Brown breed target. |
| **🥚 Daily Operations** | Data-entry form for mortality, eggs collected, cracked/dirty eggs, feed and water. On submit it derives good eggs, revenue, feed cost, hen-day production, FCR and mortality rate, saves the row to SQLite, and renders egg-quality and alert cards. |
| **💰 Financials** | Revenue, operating costs, net profit and margin across the whole dataset; a per-tray cost build-up waterfall; a 30-day revenue-vs-cost chart; and an outstanding credit-sales ledger with an add-sale form. |
| **🔮 Simulator & Forecasts** | Two tabs. *Simulator* adjusts flock size, production %, feed bag price and egg tray price to project monthly revenue, costs, profit, margin and break-even price. *Forecast* projects 30-day egg output with an expanding confidence band, estimates the feed stock-out date (50 bags × 70 kg assumed in stock), and flags anomalous days where water intake spiked while egg output fell. |

All figures use simulated Kenyan-shilling assumptions, so the app is a working demo rather than a live accounting system.

## Technology

- **Python 3.12**
- **Streamlit 1.65** — page routing via `st.navigation`, widgets, caching
- **Plotly 7** — themed interactive charts
- **pandas 2.x / NumPy 1.x** — data handling and the forecast/statistics math
- **SQLite** — embedded local database, no server required

## Quick start

```bash
pip install -r requirements.txt
python data/seed_data.py
streamlit run app.py
```

Open <http://localhost:8501>. Use **🔄 Reset Demo Data** in the sidebar at any time to delete and regenerate the clean 90-day baseline (useful after experimenting with the data-entry or credit forms).

> If you edit `.streamlit/config.toml`, restart the Streamlit server. Theme and client settings are read once at startup; page code hot-reloads, config does not.

## Project structure

```
layerfarm-intelligence/
├── .streamlit/config.toml        dark theme, port 8501, browser settings
├── assets/
│   ├── style.css                 glassmorphic cards, hero, sidebar and chart styling
│   └── images/                   reserved for logos and farm imagery
├── components/
│   ├── __init__.py
│   ├── metric_cards.py           KPI cards, alerts, section headers, feature cards
│   ├── custom_charts.py          themed Plotly chart builders
│   └── navigation.py             sidebar branding, page registration, demo reset
├── data/
│   ├── database.db               generated SQLite database
│   └── seed_data.py              90-day deterministic baseline generator
├── pages/
│   ├── 1_📊_Dashboard.py
│   ├── 2_🥚_Daily_Operations.py
│   ├── 3_💰_Financials.py
│   └── 4_🔮_Simulator.py
├── utils/
│   ├── __init__.py
│   ├── kpi_calculations.py       all KPI, financial, forecast and anomaly math
│   └── db_manager.py             connections, queries and inserts
├── app.py                        entry point, navigation setup and Home page
├── requirements.txt
└── README.md
```

`app.py` is the single entry point: it loads the theme, renders the shared sidebar, registers pages with `st.navigation`, and runs the selected page. Page files contain only their own view logic; shared calculations and UI live in `utils/` and `components/`.

## Data model

`data/database.db` contains three tables, created on demand:

- **`daily_records`** — `date`, `day_age`, `week_age`, `birds_alive_start`, `eggs_collected`, `cracked_eggs`, `dirty_eggs`, `good_eggs`, `feed_consumed_kg`, `water_consumed_liters`, `mortality`, `daily_revenue_kes`, `daily_feed_cost_kes`.
- **`farm_settings`** — `farm_name`, `location`, `breed`, `initial_birds`, `current_birds`. Displayed in the Home hero and sidebar.
- **`credit_sales`** — `id`, `date`, `buyer_name`, `trays_sold`, `price_per_tray`, `total_amount`, `status`. Created when the Financials page first loads; `Outstanding` rows make up accounts receivable.

`seed_data.py` starts at day age 140 (week 20, point of lay), simulates 90 days using a Hy-Line Brown production curve with small daily noise, and uses a fixed random seed so the baseline is reproducible.

## KPIs and assumptions

| Metric | Definition |
| --- | --- |
| Hen-Day Production | `eggs collected / birds alive at start × 100`; breed target 91% |
| FCR | `feed consumed (kg) / egg mass (kg)`, with 60 g per egg; target below 2.3 |
| Live birds | `birds alive at start − mortality` |
| Good eggs | `collected − cracked − dirty` |
| Revenue | `good eggs // 30 × KES 450` per tray |
| Feed cost | `feed kg × KES 65` |
| Other costs | 25% of feed cost (labor, vet, transport) |
| Net profit | revenue − (feed + other costs) |
| Feed stock-out | 3,500 kg assumed stock ÷ average daily feed consumption |
| Anomaly | water z-score > 1.5 **and** egg z-score < −1.5 against the recorded history |
| Forecast | 30-day rolling mean with a band that widens from 0.5× to 2.5× the standard deviation |

Rates, prices and targets are constants at the top of `utils/kpi_calculations.py` (`EGG_PRICE_KES`, `FEED_PRICE_PER_KG`, `OTHER_COST_RATIO`, `BREED_TARGET_PROD`, `FEED_STOCK_KG`, etc.). Change them there to re-tune every page at once. Simulator-specific defaults (70 kg feed bag, 115 g feed/bird/day, 30-day month) are arguments of `simulate_month()`.

## Typical workflow

1. Reset the demo data if needed.
2. Open **Daily Operations** and log a day's mortality, eggs, cracked/dirty eggs, feed and water. Confirm the instant KPI and insight cards.
3. Check **Dashboard** for the updated trend and breed benchmark.
4. Review **Financials** for margin and unit economics; log a credit sale if a buyer paid later.
5. Open **Simulator & Forecasts** to test a feed or egg price change and review stock-out and anomaly warnings.

## Troubleshooting

- **Sidebar navigation not visible** — restart `streamlit run app.py` after changing `.streamlit/config.toml`, then refresh the browser. Navigation is registered in `app.py` and rendered by Streamlit in the sidebar.
- **"Database not found"** — run `python data/seed_data.py` from the project folder, or use the sidebar reset button.
- **Charts render but styling looks wrong** — `assets/style.css` is loaded from an absolute path by `components/navigation.py`; confirm the file exists.
- **Stale numbers after entering data** — the app caches data with `@st.cache_data`; the entry forms call `st.cache_data.clear()` after a successful save, and the reset button does the same.
