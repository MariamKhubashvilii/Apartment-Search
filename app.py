import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import json
import time
from typing import Optional
import os

st.set_page_config(
    page_title="AptRank NYC",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.main-header {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    padding: 2.5rem 2rem;
    border-radius: 16px;
    margin-bottom: 2rem;
    text-align: center;
}
.main-header h1 {
    color: white;
    font-size: 2.8rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: -0.5px;
}
.main-header p {
    color: rgba(255,255,255,0.65);
    font-size: 1rem;
    margin-top: 0.5rem;
}

.metric-card {
    background: white;
    border: 1px solid #eee;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.metric-card .value {
    font-size: 2rem;
    font-weight: 700;
    color: #1a1a2e;
}
.metric-card .label {
    font-size: 0.75rem;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 2px;
}

.apt-card {
    background: white;
    border: 1px solid #eee;
    border-radius: 14px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.05);
    transition: all 0.2s;
}
.apt-card:hover {
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    transform: translateY(-1px);
}
.apt-card.rank-1 { border-left: 4px solid #22c55e; }
.apt-card.rank-2 { border-left: 4px solid #f59e0b; }
.apt-card.rank-3 { border-left: 4px solid #a78bfa; }
.apt-card.rank-other { border-left: 4px solid #e2e8f0; }

.rank-badge {
    font-size: 1.8rem;
    font-weight: 800;
    line-height: 1;
}
.rank-1-color { color: #22c55e; }
.rank-2-color { color: #f59e0b; }
.rank-3-color { color: #a78bfa; }
.rank-other-color { color: #cbd5e1; }

.score-pill {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
}
.score-high { background: #dcfce7; color: #15803d; }
.score-mid  { background: #fef9c3; color: #a16207; }
.score-low  { background: #fee2e2; color: #b91c1c; }

.safety-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 500;
}
.safety-safe   { background: #dcfce7; color: #166534; }
.safety-mixed  { background: #fef9c3; color: #92400e; }
.safety-risky  { background: #fee2e2; color: #991b1b; }

.place-tag {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}
.tag-work    { background: #dbeafe; color: #1d4ed8; }
.tag-family  { background: #fce7f3; color: #be185d; }
.tag-friends { background: #ede9fe; color: #6d28d9; }
.tag-leisure { background: #d1fae5; color: #065f46; }

.ai-box {
    background: linear-gradient(135deg, #f8f7ff, #f0f4ff);
    border: 1px solid #e0e7ff;
    border-radius: 10px;
    padding: 1rem 1.25rem;
    margin-top: 0.75rem;
    font-size: 0.875rem;
    color: #374151;
    line-height: 1.7;
}
.ai-box::before {
    content: "✦ AI insight";
    display: block;
    font-size: 0.7rem;
    font-weight: 600;
    color: #6366f1;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 0.4rem;
}

.section-header {
    font-size: 1.1rem;
    font-weight: 600;
    color: #1a1a2e;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 8px;
}

.stButton > button {
    border-radius: 10px !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
}

div[data-testid="stSidebar"] {
    background: #0f0c29 !important;
}
div[data-testid="stSidebar"] * {
    color: white !important;
}
div[data-testid="stSidebar"] .stSlider > div > div > div {
    background: rgba(255,255,255,0.15) !important;
}
</style>
""", unsafe_allow_html=True)

# ── Session state init ──────────────────────────────────────────────────────────

def init_state():
    if "places" not in st.session_state:
        st.session_state.places = [
            {"id": 1, "name": "Office",    "addr": "Rockefeller Center, New York, NY", "type": "work",    "lat": 40.7587, "lon": -73.9787},
            {"id": 2, "name": "Mum",       "addr": "Jackson Heights, Queens, NY",      "type": "family",  "lat": 40.7557, "lon": -73.8831},
            {"id": 3, "name": "BSF",       "addr": "Williamsburg, Brooklyn, NY",        "type": "friends", "lat": 40.7081, "lon": -73.9571},
            {"id": 4, "name": "Fav café",  "addr": "West Village, New York, NY",        "type": "leisure", "lat": 40.7338, "lon": -74.0059},
        ]
    if "apartments" not in st.session_state:
        st.session_state.apartments = [
            {"id": 1, "name": "Apt A", "addr": "Upper West Side, New York, NY",    "rating": 8, "lat": 40.7870, "lon": -73.9754},
            {"id": 2, "name": "Apt B", "addr": "Bushwick, Brooklyn, NY",            "rating": 9, "lat": 40.6944, "lon": -73.9213},
            {"id": 3, "name": "Apt C", "addr": "Long Island City, Queens, NY",      "rating": 7, "lat": 40.7447, "lon": -73.9485},
        ]
    if "weights" not in st.session_state:
        st.session_state.weights = {"work": 5, "family": 2, "friends": 2, "leisure": 4}
    if "results" not in st.session_state:
        st.session_state.results = []
    if "next_place_id" not in st.session_state:
        st.session_state.next_place_id = 5
    if "next_apt_id" not in st.session_state:
        st.session_state.next_apt_id = 4

init_state()

# ── NYC safety data ─────────────────────────────────────────────────────────────

NYC_SAFETY = {
    "upper west side": 8.2, "upper east side": 8.5, "astoria": 7.1,
    "long island city": 7.3, "williamsburg": 7.0, "park slope": 8.3,
    "brooklyn heights": 8.6, "cobble hill": 8.4, "greenpoint": 7.2,
    "bushwick": 4.8, "crown heights": 5.1, "bed stuy": 5.3,
    "east new york": 3.2, "harlem": 5.5, "east harlem": 4.2,
    "washington heights": 6.1, "inwood": 6.3, "midtown": 7.2,
    "hell's kitchen": 6.5, "chelsea": 8.1, "west village": 9.0,
    "soho": 8.3, "tribeca": 9.1, "financial district": 7.5,
    "lower east side": 6.2, "chinatown": 6.0, "flushing": 6.4,
    "jamaica": 4.1, "bronx": 4.3, "south bronx": 3.0,
    "fordham": 4.2, "staten island": 7.1, "bay ridge": 7.4,
    "sunset park": 5.2, "flatbush": 5.0, "astoria": 7.1,
    "jackson heights": 6.5, "forest hills": 7.8, "riverdale": 7.9,
    "murray hill": 7.6, "gramercy": 8.0, "kips bay": 7.4,
    "nolita": 8.2, "dumbo": 8.5, "red hook": 6.3,
    "gowanus": 6.1, "prospect heights": 7.2, "fort greene": 7.0,
    "clinton hill": 6.8, "boerum hill": 7.5, "carroll gardens": 8.0,
}

def get_safety_score(addr: str) -> float:
    addr_lower = addr.lower()
    for neighborhood, score in NYC_SAFETY.items():
        if neighborhood in addr_lower:
            return score
    return 6.0

def safety_label(score: float) -> tuple[str, str]:
    if score >= 7.5:
        return "Safe", "safety-safe"
    elif score >= 5.5:
        return "Mixed", "safety-mixed"
    else:
        return "Higher risk", "safety-risky"

# ── Geocoding ───────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def geocode(address: str) -> Optional[tuple[float, float]]:
    try:
        geolocator = Nominatim(user_agent="aptrank_nyc_app")
        location = geolocator.geocode(address, timeout=10)
        if location:
            return location.latitude, location.longitude
    except Exception:
        pass
    return None

# ── Scoring engine ───────────────────────────────────────────────────────────────

def compute_score(apt: dict, places: list, weights: dict) -> dict:
    apt_coords = (apt.get("lat", 40.7128), apt.get("lon", -74.0060))
    safety = get_safety_score(apt["addr"])

    # Proximity component — weighted inverse distance
    prox_scores = []
    place_details = []
    total_weight = 0

    for p in places:
        w = weights.get(p["type"], 1)
        p_coords = (p.get("lat", 40.7128), p.get("lon", -74.0060))
        try:
            dist_km = geodesic(apt_coords, p_coords).km
        except Exception:
            dist_km = 5.0
        # Soft inverse: score decreases with distance, max benefit within 1km
        prox = 10 * np.exp(-dist_km / 4.0)
        prox_scores.append(prox * w)
        total_weight += w * 10
        place_details.append({"name": p["name"], "type": p["type"], "dist_km": round(dist_km, 2), "weight": w, "score": round(prox, 2)})

    raw_prox = sum(prox_scores) / total_weight * 10 if total_weight > 0 else 5.0

    # Diversity bonus: penalize if very far from ANY high-weight place
    high_weight_places = [p for p in place_details if p["weight"] >= 4]
    diversity_penalty = 0.0
    if high_weight_places:
        max_dist = max(p["dist_km"] for p in high_weight_places)
        if max_dist > 10:
            diversity_penalty = min(1.5, (max_dist - 10) * 0.15)

    # Safety decay: strong penalty for very unsafe areas
    safety_multiplier = 1.0 if safety >= 6 else 0.85 if safety >= 4 else 0.70

    # Final composite score
    personal_rating = apt["rating"]
    prox_adjusted = max(0, raw_prox - diversity_penalty)

    final = (
        personal_rating * 0.35 +
        prox_adjusted   * 0.40 +
        safety          * 0.15 +
        # Bonus: sweet spot score when all three factors are balanced
        (0.5 if (personal_rating >= 7 and prox_adjusted >= 6 and safety >= 6) else 0) * 0.10
    ) * safety_multiplier

    final = round(min(10, max(0, final)), 2)

    return {
        "final": final,
        "personal_rating": personal_rating,
        "proximity": round(prox_adjusted, 2),
        "safety": safety,
        "diversity_penalty": round(diversity_penalty, 2),
        "place_details": place_details,
    }

# ── explanation ───────────────────────────────────────────────────────────────


def get_ai_explanation(apt, scores, rank, total):
    reasons = []
    
    if scores["personal_rating"] >= 8:
        reasons.append(f"you rated it highly at {scores['personal_rating']}/10")
    elif scores["personal_rating"] <= 5:
        reasons.append(f"your personal rating is low ({scores['personal_rating']}/10)")

    if scores["proximity"] >= 7:
        reasons.append("it's well-located relative to your frequent places")
    elif scores["proximity"] <= 4:
        reasons.append("it's quite far from some of your key spots")

    slbl, _ = safety_label(scores["safety"])
    if scores["safety"] >= 7.5:
        reasons.append("the neighborhood is safe")
    elif scores["safety"] < 5:
        reasons.append(f"the area carries higher risk ({slbl})")

    if scores["diversity_penalty"] > 0:
        reasons.append(f"a distance penalty of {scores['diversity_penalty']} was applied for being far from a high-priority place")

    if rank == 1:
        opener = "Top pick overall"
    elif rank == total:
        opener = "Lowest ranked"
    else:
        opener = f"Ranked #{rank}"

    return f"{opener} — {'; '.join(reasons)}." if reasons else f"Score of {scores['final']}/10 across rating, proximity, and safety."

# ── Sidebar ─────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 🏙️ AptRank NYC")
    st.markdown("---")

    api_key = st.text_input("Anthropic API Key", type="password", help="For AI explanations")

    st.markdown("### ⚖️ Category weights")
    for cat, icon in [("work", "💼"), ("family", "🏠"), ("friends", "👥"), ("leisure", "☕")]:
        st.session_state.weights[cat] = st.slider(
            f"{icon} {cat.capitalize()}",
            1, 10,
            st.session_state.weights[cat],
            key=f"w_{cat}"
        )

    st.markdown("---")
    st.markdown("### ℹ️ Scoring formula")
    st.markdown("""
    - **35%** your personal rating  
    - **40%** weighted proximity  
    - **15%** neighborhood safety  
    - **10%** balance bonus  
    - Safety penalty for risky areas  
    - Diversity penalty if far from high-weight places
    """)

# ── Main layout ──────────────────────────────────────────────────────────────────

st.markdown("""
<div class="main-header">
    <h1>🏙️ AptRank NYC</h1>
    <p>Find your ideal apartment by scoring proximity, safety, and personal preference</p>
</div>
""", unsafe_allow_html=True)

# Top metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""<div class="metric-card"><div class="value">{len(st.session_state.apartments)}</div><div class="label">Apartments</div></div>""", unsafe_allow_html=True)
with col2:
    st.markdown(f"""<div class="metric-card"><div class="value">{len(st.session_state.places)}</div><div class="label">Frequent places</div></div>""", unsafe_allow_html=True)
with col3:
    avg_w = round(sum(st.session_state.weights.values()) / len(st.session_state.weights), 1)
    st.markdown(f"""<div class="metric-card"><div class="value">{avg_w}</div><div class="label">Avg weight</div></div>""", unsafe_allow_html=True)
with col4:
    top_score = round(max((compute_score(a, st.session_state.places, st.session_state.weights)["final"] for a in st.session_state.apartments), default=0), 1) if st.session_state.apartments else "—"
    st.markdown(f"""<div class="metric-card"><div class="value">{top_score}</div><div class="label">Top score</div></div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ─────────────────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4 = st.tabs(["📍 Places & Apartments", "🗺️ Map", "🏆 Rankings", "📊 Analysis"])

# ════════════════════════════════════════
# TAB 1 — Places & Apartments
# ════════════════════════════════════════
with tab1:
    left, right = st.columns([1, 1], gap="large")

    with left:
        st.markdown('<div class="section-header">📍 Your frequent places</div>', unsafe_allow_html=True)

        for p in st.session_state.places:
            tag_cls = f"tag-{p['type']}"
            st.markdown(f"""
            <div class="apt-card rank-other" style="padding:0.9rem 1.2rem">
              <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
                <span class="place-tag {tag_cls}">{p['type']}</span>
                <span style="font-weight:600;color:#1a1a2e">{p['name']}</span>
                <span style="font-size:0.78rem;color:#888;flex:1">{p['addr']}</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

        with st.expander("➕ Add a place"):
            c1, c2 = st.columns(2)
            pname = c1.text_input("Label", key="pname", placeholder="e.g. Gym")
            ptype = c2.selectbox("Type", ["work", "family", "friends", "leisure"], key="ptype")
            paddr = st.text_input("Address", key="paddr", placeholder="e.g. Soho, New York, NY")
            if st.button("Add place", use_container_width=True):
                if pname and paddr:
                    coords = geocode(paddr)
                    new_place = {
                        "id": st.session_state.next_place_id,
                        "name": pname, "addr": paddr, "type": ptype,
                        "lat": coords[0] if coords else 40.7128,
                        "lon": coords[1] if coords else -74.0060
                    }
                    st.session_state.places.append(new_place)
                    st.session_state.next_place_id += 1
                    st.rerun()
                else:
                    st.warning("Please fill in both fields.")

        if st.session_state.places:
            to_del = st.selectbox("Remove a place", ["—"] + [p["name"] for p in st.session_state.places], key="del_place")
            if to_del != "—" and st.button("Remove selected place"):
                st.session_state.places = [p for p in st.session_state.places if p["name"] != to_del]
                st.rerun()

    with right:
        st.markdown('<div class="section-header">🏠 Apartments</div>', unsafe_allow_html=True)

        for a in st.session_state.apartments:
            safety = get_safety_score(a["addr"])
            slbl, scls = safety_label(safety)
            st.markdown(f"""
            <div class="apt-card rank-other" style="padding:0.9rem 1.2rem">
              <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
                <span style="font-weight:600;color:#1a1a2e">{a['name']}</span>
                <span style="font-size:0.78rem;color:#888;flex:1">{a['addr']}</span>
                <span class="safety-badge {scls}">● {slbl}</span>
                <span style="font-size:0.8rem;font-weight:600;color:#6366f1">★ {a['rating']}/10</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

        with st.expander("➕ Add apartments"):
            st.markdown("**Single apartment**")
            c1, c2 = st.columns([2, 1])
            aname = c1.text_input("Nickname", key="aname", placeholder="e.g. The Brooklyn Dream")
            arating = c2.slider("Your rating", 1, 10, 7, key="arating")
            aaddr = st.text_input("Address", key="aaddr", placeholder="e.g. 350 Bedford Ave, Brooklyn, NY")
            if st.button("Add apartment", use_container_width=True):
                if aaddr:
                    coords = geocode(aaddr)
                    new_apt = {
                        "id": st.session_state.next_apt_id,
                        "name": aname or f"Apt {st.session_state.next_apt_id}",
                        "addr": aaddr, "rating": arating,
                        "lat": coords[0] if coords else 40.7128,
                        "lon": coords[1] if coords else -74.0060
                    }
                    st.session_state.apartments.append(new_apt)
                    st.session_state.next_apt_id += 1
                    st.rerun()
                else:
                    st.warning("Please enter an address.")

            st.markdown("**Bulk add (one per line)**")
            bulk = st.text_area("Addresses", key="bulk", placeholder="123 Main St, Brooklyn, NY\n456 Park Ave, Manhattan, NY", height=100)
            if st.button("Bulk add", use_container_width=True):
                lines = [l.strip() for l in bulk.split("\n") if l.strip()]
                for addr in lines:
                    coords = geocode(addr)
                    st.session_state.apartments.append({
                        "id": st.session_state.next_apt_id,
                        "name": f"Apt {st.session_state.next_apt_id}",
                        "addr": addr, "rating": 7,
                        "lat": coords[0] if coords else 40.7128,
                        "lon": coords[1] if coords else -74.0060
                    })
                    st.session_state.next_apt_id += 1
                    time.sleep(1.1)
                st.rerun()

        if st.session_state.apartments:
            to_del_a = st.selectbox("Remove an apartment", ["—"] + [a["name"] for a in st.session_state.apartments], key="del_apt")
            if to_del_a != "—" and st.button("Remove selected apartment"):
                st.session_state.apartments = [a for a in st.session_state.apartments if a["name"] != to_del_a]
                st.rerun()

        st.markdown("**Edit ratings**")
        for a in st.session_state.apartments:
            a["rating"] = st.slider(f"{a['name']}", 1, 10, a["rating"], key=f"rate_{a['id']}")

# ════════════════════════════════════════
# TAB 2 — Map
# ════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-header">🗺️ NYC overview map</div>', unsafe_allow_html=True)

    fig = go.Figure()

    # Safety color zones — simplified borough polygons
    # (omitted for brevity — real app would use GeoJSON choropleth)

    # Apartments
    for a in st.session_state.apartments:
        s = compute_score(a, st.session_state.places, st.session_state.weights)
        color = "#22c55e" if s["final"] >= 7 else "#f59e0b" if s["final"] >= 5 else "#ef4444"
        fig.add_trace(go.Scattermapbox(
            lat=[a["lat"]], lon=[a["lon"]],
            mode="markers+text",
            marker=dict(size=18, color=color, opacity=0.9),
            text=[a["name"]],
            textposition="top right",
            textfont=dict(size=12, color="#1a1a2e"),
            name=f"🏠 {a['name']} ({s['final']}/10)",
            hovertemplate=f"<b>{a['name']}</b><br>{a['addr']}<br>Score: {s['final']}/10<br>Rating: {a['rating']}/10<extra></extra>",
        ))

    # Places
    place_colors = {"work": "#3b82f6", "family": "#ec4899", "friends": "#8b5cf6", "leisure": "#10b981"}
    place_symbols = {"work": "building", "family": "home", "friends": "heart", "leisure": "cafe"}
    for p in st.session_state.places:
        fig.add_trace(go.Scattermapbox(
            lat=[p["lat"]], lon=[p["lon"]],
            mode="markers+text",
            marker=dict(size=14, color=place_colors.get(p["type"], "#888"), opacity=1),
            text=[p["name"]],
            textposition="top right",
            textfont=dict(size=11, color="#444"),
            name=f"📍 {p['name']} ({p['type']})",
            hovertemplate=f"<b>{p['name']}</b><br>{p['addr']}<br>Type: {p['type']}<extra></extra>",
        ))

    fig.update_layout(
        mapbox=dict(
            style="carto-positron",
            center=dict(lat=40.73, lon=-73.95),
            zoom=11
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=560,
        legend=dict(
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="#eee",
            borderwidth=1,
            font=dict(size=11)
        )
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    <div style="display:flex;gap:16px;font-size:0.8rem;color:#666;flex-wrap:wrap;margin-top:8px">
      <span>🟢 Score ≥ 7</span>
      <span>🟡 Score 5–7</span>
      <span>🔴 Score &lt; 5</span>
      <span>🔵 Work</span>
      <span>🩷 Family</span>
      <span>🟣 Friends</span>
      <span>🟢 Leisure</span>
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════
# TAB 3 — Rankings
# ════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header">🏆 Apartment rankings</div>', unsafe_allow_html=True)

    if not st.session_state.apartments:
        st.info("Add some apartments in the first tab to see rankings.")
    else:
        run_btn = st.button("⚡ Calculate rankings + AI explanations", type="primary", use_container_width=True)

        if run_btn or st.session_state.results:
            if run_btn:
                scored = []
                for a in st.session_state.apartments:
                    s = compute_score(a, st.session_state.places, st.session_state.weights)
                    scored.append({"apt": a, "scores": s})
                scored.sort(key=lambda x: x["scores"]["final"], reverse=True)

                with st.spinner("Getting AI explanations..."):
                    for item in scored:
                        rank = scored.index(item) + 1
                        explanation = get_ai_explanation(
                            item["apt"], item["scores"], rank, len(scored)
                        )
                        item["explanation"] = explanation

                st.session_state.results = scored

            rank_labels = {1: ("rank-1", "rank-1-color", "🥇"),
                           2: ("rank-2", "rank-2-color", "🥈"),
                           3: ("rank-3", "rank-3-color", "🥉")}

            for i, item in enumerate(st.session_state.results):
                rank = i + 1
                a = item["apt"]
                s = item["scores"]
                card_cls, badge_cls, emoji = rank_labels.get(rank, ("rank-other", "rank-other-color", f"#{rank}"))
                slbl, scls = safety_label(s["safety"])
                score_cls = "score-high" if s["final"] >= 7 else "score-mid" if s["final"] >= 5 else "score-low"
                pct = int(s["final"] / 10 * 100)

                st.markdown(f"""
                <div class="apt-card {card_cls}">
                  <div style="display:flex;gap:16px;align-items:flex-start">
                    <div style="text-align:center;min-width:40px">
                      <div class="rank-badge {badge_cls}">{emoji}</div>
                    </div>
                    <div style="flex:1">
                      <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:6px">
                        <span style="font-size:1.05rem;font-weight:700;color:#1a1a2e">{a['name']}</span>
                        <span style="font-size:0.78rem;color:#888">{a['addr']}</span>
                        <span class="score-pill {score_cls}">{s['final']}/10</span>
                        <span class="safety-badge {scls}">● {slbl}</span>
                      </div>
                      <div style="background:#f8f9fa;border-radius:6px;height:8px;margin:8px 0">
                        <div style="background:{'#22c55e' if rank==1 else '#f59e0b' if rank==2 else '#a78bfa' if rank==3 else '#94a3b8'};height:8px;border-radius:6px;width:{pct}%;transition:width 0.5s"></div>
                      </div>
                      <div style="display:flex;gap:16px;font-size:0.78rem;color:#666;flex-wrap:wrap;margin-bottom:8px">
                        <span>★ Your rating: <b>{a['rating']}/10</b></span>
                        <span>📍 Proximity: <b>{s['proximity']}/10</b></span>
                        <span>🛡️ Safety: <b>{s['safety']}/10</b></span>
                        {"<span>⚠️ Distance penalty: <b>-" + str(s['diversity_penalty']) + "</b></span>" if s['diversity_penalty'] > 0 else ""}
                      </div>
                      <div class="ai-box">{item.get('explanation', '—')}</div>
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

# ════════════════════════════════════════
# TAB 4 — Analysis
# ════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-header">📊 Score breakdown analysis</div>', unsafe_allow_html=True)

    if not st.session_state.apartments:
        st.info("Add apartments to see analysis charts.")
    else:
        scored_all = sorted(
            [{"apt": a, "scores": compute_score(a, st.session_state.places, st.session_state.weights)}
             for a in st.session_state.apartments],
            key=lambda x: x["scores"]["final"], reverse=True
        )

        names = [x["apt"]["name"] for x in scored_all]
        finals = [x["scores"]["final"] for x in scored_all]
        ratings = [x["scores"]["personal_rating"] for x in scored_all]
        proxims = [x["scores"]["proximity"] for x in scored_all]
        safeties = [x["scores"]["safety"] for x in scored_all]

        # Stacked bar
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(name="Your rating (35%)",  x=names, y=[r * 0.35 for r in ratings],  marker_color="#6366f1"))
        fig_bar.add_trace(go.Bar(name="Proximity (40%)",   x=names, y=[p * 0.40 for p in proxims],   marker_color="#22c55e"))
        fig_bar.add_trace(go.Bar(name="Safety (15%)",      x=names, y=[s * 0.15 for s in safeties],  marker_color="#f59e0b"))
        fig_bar.update_layout(
            barmode="stack",
            title="Score composition per apartment",
            height=350,
            margin=dict(t=40, b=20),
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(family="Inter"),
            legend=dict(orientation="h", y=-0.2)
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        # Radar chart for top 3
        top3 = scored_all[:min(3, len(scored_all))]
        cats = ["Your rating", "Proximity", "Safety"]
        fig_radar = go.Figure()
        colors = ["#6366f1", "#22c55e", "#f59e0b"]
        for i, item in enumerate(top3):
            s = item["scores"]
            fig_radar.add_trace(go.Scatterpolar(
                r=[s["personal_rating"], s["proximity"], s["safety"]],
                theta=cats,
                fill="toself",
                name=item["apt"]["name"],
                line_color=colors[i],
                fillcolor=colors[i],
                opacity=0.25
            ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
            title="Top 3 apartments — radar comparison",
            height=380,
            font=dict(family="Inter"),
            paper_bgcolor="white",
        )
        st.plotly_chart(fig_radar, use_container_width=True)

        # Distance table
        st.markdown('<div class="section-header" style="margin-top:1rem">📏 Distance matrix (km)</div>', unsafe_allow_html=True)
        rows = []
        for item in scored_all:
            a = item["apt"]
            row = {"Apartment": a["name"]}
            for p in st.session_state.places:
                try:
                    d = geodesic((a["lat"], a["lon"]), (p["lat"], p["lon"])).km
                    row[p["name"]] = f"{d:.1f}"
                except Exception:
                    row[p["name"]] = "—"
            rows.append(row)
        df = pd.DataFrame(rows).set_index("Apartment")
        st.dataframe(df, use_container_width=True)
