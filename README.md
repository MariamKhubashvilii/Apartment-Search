# 🏙️ AptRank NYC

**Find just the perfect apartment for you.**

AptRank lets you score apartments against your actual life — your office, your mum's place, your favourite café, your best friend's flat. Add any address, weight what matters to you, and get a ranked list with a clear explanation of every tradeoff.

![Python](https://img.shields.io/badge/Python-3.10+-3776ab?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-ff4b4b?logo=streamlit&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-5.20+-3f4f75?logo=plotly&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

![AptRank screenshot](https://github.com/MariamKhubashvilii/Apartment-Search/main/screenshot.png)

---

## What it does

You have a 10/10 apartment on paper, but it's 45 minutes from your office. You have a 7/10 apartment that's a 10-minute walk to everything you care about. AptRank helps you see that clearly.

You define your world — the places you visit regularly and how much each one matters to you. The app scores every apartment candidate against that picture and ranks them.

---

## Features

- **Weighted scoring** — set importance per category: work, family, friends, leisure. A high work weight means proximity to your office pulls the score up much more than proximity to a café.
- **Composite score** — four factors combined: your personal rating, weighted proximity, neighborhood safety, and a balance bonus for apartments that do well across all three.
- **Smart proximity** — uses exponential decay rather than raw distance. An apartment 1km away scores nearly full marks; 8km away scores much lower. The falloff is smooth, not a hard cutoff.
- **Safety layer** — 40+ NYC neighborhoods have baked-in safety scores. Risky areas apply a score multiplier, not just a footnote.
- **Diversity penalty** — if an apartment looks good on average but is actually far from your highest-priority places, it gets penalized. Averages can hide bad tradeoffs.
- **Address autocomplete** — start typing a neighborhood and clickable suggestions appear.
- **Add from coordinates** — paste a lat/lon from Google Maps and the app reverse-geocodes it to an address. Useful when you find a listing on a map and want to drop it in instantly.
- **Bulk add** — paste a list of addresses and geocode them all at once.
- **Interactive map** — all apartments and places plotted together, color-coded by score (green / yellow / red).
- **Analysis tab** — stacked bar chart showing score composition, radar chart comparing your top 3, and a full distance matrix.

---

## Scoring formula

```
final_score = (
    personal_rating  × 0.35 +
    weighted_proximity × 0.40 +
    neighborhood_safety × 0.15 +
    balance_bonus    × 0.10
) × safety_multiplier
```

**Weighted proximity** — for each frequent place, the proximity score is `10 × exp(−distance_km / 4)`, weighted by the category importance you set. This means:

| Distance | Raw proximity score |
|---|---|
| 0.5 km | ~8.8 |
| 2 km   | ~6.1 |
| 5 km   | ~2.9 |
| 10 km  | ~0.8 |

**Safety multiplier** — applied to the whole score:

| Safety score | Multiplier |
|---|---|
| ≥ 6 (safe) | 1.00 |
| 4–6 (mixed) | 0.85 |
| < 4 (high risk) | 0.70 |

**Diversity penalty** — if the apartment is more than 10 km from any place with a weight ≥ 4, a penalty of up to 1.5 points is subtracted from the proximity score before the final calculation.

**Balance bonus** — a small bonus (0.05 points) is added if the apartment scores ≥ 7 on personal rating, ≥ 6 on proximity, and ≥ 6 on safety simultaneously. Rewards all-rounders.

---

## Local setup

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/apartment-ranker-nyc.git
cd apartment-ranker-nyc

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install
pip install -r requirements.txt

# 4. Run
streamlit run app.py
```

No API keys needed. Geocoding uses OpenStreetMap via Geopy (free, no account required).

---

## Deploy to Streamlit Cloud

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app** → select your repo → set the main file path to `app.py`.
4. Click **Deploy**. That's it.

The app has no secrets or environment variables to configure.

---

## Project structure

```
apartment-ranker-nyc/
├── app.py                  # entire application
├── requirements.txt        # 5 dependencies
├── .streamlit/
│   └── config.toml         # theme (indigo / dark sidebar)
├── .gitignore
└── README.md
```

---

## Tech stack

| Layer | Tool | Why |
|---|---|---|
| UI & server | Streamlit | Fast to build, deploys in one click |
| Maps & charts | Plotly | Interactive, no JS required |
| Geocoding | Geopy + Nominatim | Free, no API key, OpenStreetMap-backed |
| Data wrangling | Pandas, NumPy | Distance matrix, score calculations |

---

## Ideas for extending it

- **Real crime data** — swap the baked-in safety scores for live data from [NYC Open Data](https://data.cityofnewyork.us/Public-Safety/NYPD-Complaint-Data-Historic/qgea-i56i) (free API).
- **Rent as a factor** — add a monthly rent field and include cost-per-score in the ranking.
- **Commute time** — replace straight-line distance with actual transit time via the Google Maps Directions API or OpenRouteService (free tier available).
- **Persistence** — save and reload apartment lists with SQLite so you don't lose your data between sessions.
- **Other cities** — the scoring engine is city-agnostic. Swap the NYC safety lookup for data from any city.

---

## License

MIT — do whatever you want with it.
