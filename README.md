# 🏙️ AptRank NYC

> Find your perfect New York apartment by scoring proximity to your frequent places, neighborhood safety, and your personal preference — all in one clean dashboard.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red?logo=streamlit)
![Plotly](https://img.shields.io/badge/Plotly-5.20+-purple?logo=plotly)

---

## Features

- Add any apartment address and rate it personally (1–10)
- Add your frequent places: work, family, friends, leisure spots
- Set custom weights per category (work matters more than leisure? set it)
- Composite scoring: proximity (40%) + personal rating (35%) + safety (15%) + balance bonus (10%)
- Safety penalty for risky neighborhoods, diversity penalty if an apartment is far from high-priority places
- Interactive Plotly map showing all apartments and places color-coded by score
- AI-generated 2-sentence explanation per apartment using Claude
- Stacked bar and radar charts for visual score breakdown
- Distance matrix across all apartments and places

---

## Local setup

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/apartment-ranker-nyc.git
cd apartment-ranker-nyc

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your Anthropic API key
# Create .streamlit/secrets.toml and add:
# ANTHROPIC_API_KEY = "sk-ant-..."

# 5. Run the app
streamlit run app.py
```

---

## Deploy to Streamlit Cloud

1. Push this repo to GitHub (make sure `.streamlit/secrets.toml` is in `.gitignore`)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **New app** → select your repo → set main file to `app.py`
4. Under **Advanced settings → Secrets**, paste:
   ```
   ANTHROPIC_API_KEY = "sk-ant-your-key-here"
   ```
5. Click **Deploy**

---

## Scoring formula

```
final_score = (
    personal_rating × 0.35 +
    weighted_proximity × 0.40 +
    neighborhood_safety × 0.15 +
    balance_bonus × 0.10
) × safety_multiplier
```

**Weighted proximity** uses exponential decay: `score = 10 × exp(-distance_km / 4)`, so apartments within 1–2km score very high and it falls off smoothly beyond that.

**Safety multiplier**: 1.0 for safe areas (≥6), 0.85 for mixed (≥4), 0.70 for high-risk areas.

**Diversity penalty**: if the apartment is more than 10km from any high-weight place (weight ≥ 4), a small penalty is applied to avoid picking something that looks good on average but is actually far from what matters most.

---

## Tech stack

| Layer | Tool |
|---|---|
| UI | Streamlit |
| Maps & charts | Plotly |
| Geocoding | Geopy + Nominatim (OpenStreetMap) |
| AI explanations | Anthropic Claude API |
| Data | Pandas, NumPy |

---

## Extending the app

- Swap Nominatim for Google Maps Geocoding API for higher accuracy
- Add real NYC crime data via [NYC Open Data](https://data.cityofnewyork.us)
- Add rent price as a scoring factor
- Add commute time via Google Maps Directions API
- Save/load apartment lists with SQLite or a JSON file

---

## License

MIT
