import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time
from typing import Optional

st.set_page_config(
    page_title="AptRank NYC",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.main-header {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    padding: 2.5rem 2rem; border-radius: 16px; margin-bottom: 2rem; text-align: center;
}
.main-header h1 { color: white; font-size: 2.8rem; font-weight: 700; margin: 0; letter-spacing: -0.5px; }
.main-header p  { color: rgba(255,255,255,0.65); font-size: 1rem; margin-top: 0.5rem; }

.metric-card {
    background: white; border: 1px solid #eee; border-radius: 12px;
    padding: 1.25rem 1.5rem; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.metric-card .value { font-size: 2rem; font-weight: 700; color: #1a1a2e; }
.metric-card .label { font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 2px; }

.apt-card {
    background: white; border: 1px solid #eee; border-radius: 14px;
    padding: 1.5rem; margin-bottom: 1rem; box-shadow: 0 2px 12px rgba(0,0,0,0.05);
}
.apt-card.rank-1     { border-left: 4px solid #22c55e; }
.apt-card.rank-2     { border-left: 4px solid #f59e0b; }
.apt-card.rank-3     { border-left: 4px solid #a78bfa; }
.apt-card.rank-other { border-left: 4px solid #e2e8f0; }

.rank-badge       { font-size: 1.8rem; font-weight: 800; line-height: 1; }
.rank-1-color     { color: #22c55e; }
.rank-2-color     { color: #f59e0b; }
.rank-3-color     { color: #a78bfa; }
.rank-other-color { color: #cbd5e1; }

.score-pill { display:inline-block; padding:4px 12px; border-radius:20px; font-size:0.8rem; font-weight:600; }
.score-high { background:#dcfce7; color:#15803d; }
.score-mid  { background:#fef9c3; color:#a16207; }
.score-low  { background:#fee2e2; color:#b91c1c; }

.safety-badge { display:inline-flex; align-items:center; gap:5px; padding:3px 10px; border-radius:20px; font-size:0.75rem; font-weight:500; }
.safety-safe  { background:#dcfce7; color:#166534; }
.safety-mixed { background:#fef9c3; color:#92400e; }
.safety-risky { background:#fee2e2; color:#991b1b; }

.place-tag  { display:inline-block; padding:3px 10px; border-radius:20px; font-size:0.72rem; font-weight:600; text-transform:uppercase; letter-spacing:0.03em; }
.tag-work    { background:#dbeafe; color:#1d4ed8; }
.tag-family  { background:#fce7f3; color:#be185d; }
.tag-friends { background:#ede9fe; color:#6d28d9; }
.tag-leisure { background:#d1fae5; color:#065f46; }

.insight-box {
    background: linear-gradient(135deg, #f8f7ff, #f0f4ff);
    border: 1px solid #e0e7ff; border-radius: 10px;
    padding: 0.75rem 1rem; margin-top: 0.75rem;
    font-size: 0.875rem; color: #374151; line-height: 1.7;
}
.insight-label {
    font-size: 0.7rem; font-weight: 600; color: #6366f1;
    text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.3rem;
}

.section-header {
    font-size: 1.1rem; font-weight: 600; color: #1a1a2e;
    margin-bottom: 1rem; display:flex; align-items:center; gap:8px;
}
.stButton > button { border-radius: 10px !important; font-weight: 500 !important; }

div[data-testid="stSidebar"] { background: #0f0c29 !important; }
div[data-testid="stSidebar"] * { color: white !important; }

/* autocomplete dropdown */
.autocomplete-item {
    padding: 8px 12px; cursor: pointer; font-size: 0.85rem;
    border-bottom: 1px solid #f0f0f0; color: #1a1a2e;
}
.autocomplete-item:hover { background: #f5f3ff; }
</style>
""", unsafe_allow_html=True)

# ── Session state ───────────────────────────────────────────────────────────────

def init_state():
    if "places" not in st.session_state:
        st.session_state.places = [
            {"id":1,"name":"Office",   "addr":"Rockefeller Center, New York, NY","type":"work",    "lat":40.7587,"lon":-73.9787},
            {"id":2,"name":"Mum",      "addr":"Jackson Heights, Queens, NY",     "type":"family",  "lat":40.7557,"lon":-73.8831},
            {"id":3,"name":"BSF",      "addr":"Williamsburg, Brooklyn, NY",      "type":"friends", "lat":40.7081,"lon":-73.9571},
            {"id":4,"name":"Fav café", "addr":"West Village, New York, NY",      "type":"leisure", "lat":40.7338,"lon":-74.0059},
        ]
    if "apartments" not in st.session_state:
        st.session_state.apartments = [
            {"id":1,"name":"Apt A","addr":"Upper West Side, New York, NY",   "rating":8,"lat":40.7870,"lon":-73.9754},
            {"id":2,"name":"Apt B","addr":"Bushwick, Brooklyn, NY",           "rating":9,"lat":40.6944,"lon":-73.9213},
            {"id":3,"name":"Apt C","addr":"Long Island City, Queens, NY",     "rating":7,"lat":40.7447,"lon":-73.9485},
        ]
    if "weights"          not in st.session_state: st.session_state.weights = {"work":5,"family":2,"friends":2,"leisure":4}
    if "results"          not in st.session_state: st.session_state.results = []
    if "next_place_id"    not in st.session_state: st.session_state.next_place_id = 5
    if "next_apt_id"      not in st.session_state: st.session_state.next_apt_id = 4
    if "map_click_addr"   not in st.session_state: st.session_state.map_click_addr = ""
    if "map_click_coords" not in st.session_state: st.session_state.map_click_coords = None

init_state()

# ── NYC safety data ─────────────────────────────────────────────────────────────

NYC_SAFETY = {
    "upper west side":8.2,"upper east side":8.5,"astoria":7.1,
    "long island city":7.3,"williamsburg":7.0,"park slope":8.3,
    "brooklyn heights":8.6,"cobble hill":8.4,"greenpoint":7.2,
    "bushwick":4.8,"crown heights":5.1,"bed stuy":5.3,
    "east new york":3.2,"harlem":5.5,"east harlem":4.2,
    "washington heights":6.1,"inwood":6.3,"midtown":7.2,
    "hell's kitchen":6.5,"chelsea":8.1,"west village":9.0,
    "soho":8.3,"tribeca":9.1,"financial district":7.5,
    "lower east side":6.2,"chinatown":6.0,"flushing":6.4,
    "jamaica":4.1,"bronx":4.3,"south bronx":3.0,
    "fordham":4.2,"staten island":7.1,"bay ridge":7.4,
    "sunset park":5.2,"flatbush":5.0,"jackson heights":6.5,
    "forest hills":7.8,"riverdale":7.9,"murray hill":7.6,
    "gramercy":8.0,"kips bay":7.4,"nolita":8.2,"dumbo":8.5,
    "red hook":6.3,"gowanus":6.1,"prospect heights":7.2,
    "fort greene":7.0,"clinton hill":6.8,"boerum hill":7.5,
    "carroll gardens":8.0,
}

NYC_NEIGHBORHOODS = sorted(NYC_SAFETY.keys())

def get_safety_score(addr: str) -> float:
    a = addr.lower()
    for n, s in NYC_SAFETY.items():
        if n in a:
            return s
    return 6.0

def safety_label(score: float) -> tuple:
    if score >= 7.5: return "Safe",        "safety-safe"
    if score >= 5.5: return "Mixed",       "safety-mixed"
    return              "Higher risk",     "safety-risky"

# ── Geocoding ───────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def geocode(address: str) -> Optional[tuple]:
    try:
        geolocator = Nominatim(user_agent="aptrank_nyc_v2")
        loc = geolocator.geocode(address + ", New York", timeout=10)
        if loc:
            return loc.latitude, loc.longitude
        loc = geolocator.geocode(address, timeout=10)
        if loc:
            return loc.latitude, loc.longitude
    except Exception:
        pass
    return None

@st.cache_data(show_spinner=False)
def reverse_geocode(lat: float, lon: float) -> str:
    try:
        geolocator = Nominatim(user_agent="aptrank_nyc_v2")
        loc = geolocator.reverse((lat, lon), timeout=10)
        if loc:
            return loc.address
    except Exception:
        pass
    return f"{lat:.4f}, {lon:.4f}"

def suggest_neighborhoods(query: str) -> list:
    q = query.lower().strip()
    if len(q) < 2:
        return []
    return [n.title() + ", New York, NY" for n in NYC_NEIGHBORHOODS if q in n][:6]

# ── Scoring ─────────────────────────────────────────────────────────────────────

def compute_score(apt: dict, places: list, weights: dict) -> dict:
    apt_coords = (apt.get("lat", 40.7128), apt.get("lon", -74.0060))
    safety = get_safety_score(apt["addr"])

    prox_scores, place_details, total_weight = [], [], 0
    for p in places:
        w = weights.get(p["type"], 1)
        p_coords = (p.get("lat", 40.7128), p.get("lon", -74.0060))
        try:    dist_km = geodesic(apt_coords, p_coords).km
        except: dist_km = 5.0
        prox = 10 * np.exp(-dist_km / 4.0)
        prox_scores.append(prox * w)
        total_weight += w * 10
        place_details.append({"name":p["name"],"type":p["type"],"dist_km":round(dist_km,2),"weight":w,"score":round(prox,2)})

    raw_prox = sum(prox_scores) / total_weight * 10 if total_weight > 0 else 5.0

    high_w = [p for p in place_details if p["weight"] >= 4]
    diversity_penalty = 0.0
    if high_w:
        max_dist = max(p["dist_km"] for p in high_w)
        if max_dist > 10:
            diversity_penalty = min(1.5, (max_dist - 10) * 0.15)

    safety_multiplier = 1.0 if safety >= 6 else 0.85 if safety >= 4 else 0.70
    personal_rating   = apt["rating"]
    prox_adjusted     = max(0, raw_prox - diversity_penalty)

    final = (
        personal_rating * 0.35 +
        prox_adjusted   * 0.40 +
        safety          * 0.15 +
        (0.5 if (personal_rating >= 7 and prox_adjusted >= 6 and safety >= 6) else 0) * 0.10
    ) * safety_multiplier

    return {
        "final":            round(min(10, max(0, final)), 2),
        "personal_rating":  personal_rating,
        "proximity":        round(prox_adjusted, 2),
        "safety":           safety,
        "diversity_penalty":round(diversity_penalty, 2),
        "place_details":    place_details,
    }

# ── Rule-based explanation ───────────────────────────────────────────────────────

def get_explanation(apt: dict, scores: dict, rank: int, total: int) -> str:
    reasons = []
    if   scores["personal_rating"] >= 8: reasons.append(f"you rated it highly at {scores['personal_rating']}/10")
    elif scores["personal_rating"] <= 5: reasons.append(f"your personal rating is low ({scores['personal_rating']}/10)")

    if   scores["proximity"] >= 7: reasons.append("it sits close to most of your frequent spots")
    elif scores["proximity"] <= 4: reasons.append("it is quite far from several of your key places")

    slbl, _ = safety_label(scores["safety"])
    if   scores["safety"] >= 7.5: reasons.append(f"the neighborhood is {slbl.lower()}")
    elif scores["safety"] <  5.5: reasons.append(f"the area carries higher risk ({slbl})")

    if scores["diversity_penalty"] > 0:
        reasons.append(f"a -{scores['diversity_penalty']} distance penalty was applied for being far from a high-priority place")

    if   rank == 1:     opener = "Top pick overall"
    elif rank == total: opener = "Lowest ranked"
    else:               opener = f"Ranked #{rank} of {total}"

    body = "; ".join(reasons) if reasons else f"composite score of {scores['final']}/10 across rating, proximity, and safety"
    return f"{opener} — {body}."

# ── Sidebar ─────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 🏙️ AptRank NYC")
    st.markdown("---")
    st.markdown("### ⚖️ Category weights")
    for cat, icon in [("work","💼"),("family","🏠"),("friends","👥"),("leisure","☕")]:
        st.session_state.weights[cat] = st.slider(
            f"{icon} {cat.capitalize()}", 1, 10,
            st.session_state.weights[cat], key=f"w_{cat}"
        )
    st.markdown("---")
    st.markdown("### ℹ️ Scoring formula")
    st.markdown("""
- **35%** your personal rating
- **40%** weighted proximity
- **15%** neighborhood safety
- **10%** balance bonus
- Safety multiplier for risky areas
- Diversity penalty if far from high-weight places
    """)

# ── Header ───────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="main-header">
    <h1>🏙️ AptRank NYC</h1>
    <p>Score apartments by proximity, safety, and personal preference</p>
</div>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div class="metric-card"><div class="value">{len(st.session_state.apartments)}</div><div class="label">Apartments</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><div class="value">{len(st.session_state.places)}</div><div class="label">Frequent places</div></div>', unsafe_allow_html=True)
with col3:
    avg_w = round(sum(st.session_state.weights.values()) / len(st.session_state.weights), 1)
    st.markdown(f'<div class="metric-card"><div class="value">{avg_w}</div><div class="label">Avg weight</div></div>', unsafe_allow_html=True)
with col4:
    top_score = round(max((compute_score(a, st.session_state.places, st.session_state.weights)["final"] for a in st.session_state.apartments), default=0), 1) if st.session_state.apartments else "—"
    st.markdown(f'<div class="metric-card"><div class="value">{top_score}</div><div class="label">Top score</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["📍 Places & Apartments", "🗺️ Map", "🏆 Rankings", "📊 Analysis"])

# ════════════════════════════════════════════════════════
# TAB 1 — Places & Apartments
# ════════════════════════════════════════════════════════
with tab1:
    left, right = st.columns([1, 1], gap="large")

    # ── LEFT: Places ──
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
            </div>""", unsafe_allow_html=True)

        with st.expander("➕ Add a place"):
            c1, c2 = st.columns(2)
            pname = c1.text_input("Label", key="pname", placeholder="e.g. Gym")
            ptype = c2.selectbox("Type", ["work","family","friends","leisure"], key="ptype")

            paddr_raw = st.text_input("Address", key="paddr", placeholder="Start typing a NYC neighborhood…")
            suggestions = suggest_neighborhoods(paddr_raw) if paddr_raw else []
            if suggestions:
                st.caption("Suggestions — click to use:")
                for sug in suggestions:
                    if st.button(sug, key=f"psug_{sug}"):
                        st.session_state["paddr"] = sug
                        st.rerun()

            if st.button("Add place", use_container_width=True, key="add_place_btn"):
                if pname and paddr_raw:
                    with st.spinner("Looking up location…"):
                        coords = geocode(paddr_raw)
                        time.sleep(1.1)
                    st.session_state.places.append({
                        "id": st.session_state.next_place_id,
                        "name": pname, "addr": paddr_raw, "type": ptype,
                        "lat": coords[0] if coords else 40.7128,
                        "lon": coords[1] if coords else -74.0060,
                    })
                    st.session_state.next_place_id += 1
                    st.rerun()
                else:
                    st.warning("Fill in both label and address.")

        if st.session_state.places:
            to_del = st.selectbox("Remove a place", ["—"] + [p["name"] for p in st.session_state.places], key="del_place")
            if to_del != "—" and st.button("Remove", key="rm_place"):
                st.session_state.places = [p for p in st.session_state.places if p["name"] != to_del]
                st.rerun()

    # ── RIGHT: Apartments ──
    with right:
        st.markdown('<div class="section-header">🏠 Apartments</div>', unsafe_allow_html=True)

        for a in st.session_state.apartments:
            slbl, scls = safety_label(get_safety_score(a["addr"]))
            st.markdown(f"""
            <div class="apt-card rank-other" style="padding:0.9rem 1.2rem">
              <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
                <span style="font-weight:600;color:#1a1a2e">{a['name']}</span>
                <span style="font-size:0.78rem;color:#888;flex:1">{a['addr']}</span>
                <span class="safety-badge {scls}">● {slbl}</span>
                <span style="font-size:0.8rem;font-weight:600;color:#6366f1">★ {a['rating']}/10</span>
              </div>
            </div>""", unsafe_allow_html=True)

        with st.expander("➕ Add apartments"):
            st.markdown("**Single apartment**")
            c1, c2 = st.columns([2, 1])
            aname   = c1.text_input("Nickname", key="aname", placeholder="e.g. The Brooklyn Dream")
            arating = c2.slider("Your rating", 1, 10, 7, key="arating")

            aaddr_raw = st.text_input("Address", key="aaddr", placeholder="Start typing a NYC neighborhood…")
            asug = suggest_neighborhoods(aaddr_raw) if aaddr_raw else []
            if asug:
                st.caption("Suggestions — click to use:")
                for s in asug:
                    if st.button(s, key=f"asug_{s}"):
                        st.session_state["aaddr"] = s
                        st.rerun()

            if st.button("Add apartment", use_container_width=True, key="add_apt_btn"):
                if aaddr_raw:
                    with st.spinner("Looking up location…"):
                        coords = geocode(aaddr_raw)
                        time.sleep(1.1)
                    st.session_state.apartments.append({
                        "id": st.session_state.next_apt_id,
                        "name": aname or f"Apt {st.session_state.next_apt_id}",
                        "addr": aaddr_raw, "rating": arating,
                        "lat": coords[0] if coords else 40.7128,
                        "lon": coords[1] if coords else -74.0060,
                    })
                    st.session_state.next_apt_id += 1
                    st.rerun()
                else:
                    st.warning("Please enter an address.")

            st.markdown("**Bulk add (one address per line)**")
            bulk = st.text_area("Addresses", key="bulk",
                placeholder="Upper West Side, New York, NY\n350 Bedford Ave, Brooklyn, NY", height=90)
            if st.button("Bulk add", use_container_width=True, key="bulk_btn"):
                lines = [l.strip() for l in bulk.split("\n") if l.strip()]
                prog = st.progress(0, text="Geocoding addresses…")
                for i, addr in enumerate(lines):
                    coords = geocode(addr)
                    st.session_state.apartments.append({
                        "id": st.session_state.next_apt_id,
                        "name": f"Apt {st.session_state.next_apt_id}",
                        "addr": addr, "rating": 7,
                        "lat": coords[0] if coords else 40.7128,
                        "lon": coords[1] if coords else -74.0060,
                    })
                    st.session_state.next_apt_id += 1
                    prog.progress((i + 1) / len(lines), text=f"Geocoded {i+1}/{len(lines)}")
                    time.sleep(1.1)
                st.rerun()

        if st.session_state.apartments:
            to_del_a = st.selectbox("Remove an apartment", ["—"] + [a["name"] for a in st.session_state.apartments], key="del_apt")
            if to_del_a != "—" and st.button("Remove", key="rm_apt"):
                st.session_state.apartments = [a for a in st.session_state.apartments if a["name"] != to_del_a]
                st.rerun()

        st.markdown("**Edit ratings**")
        for a in st.session_state.apartments:
            a["rating"] = st.slider(f"{a['name']}", 1, 10, a["rating"], key=f"rate_{a['id']}")

# ════════════════════════════════════════════════════════
# TAB 2 — Map  (click-to-add + proper legend placement)
# ════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-header">🗺️ NYC overview map</div>', unsafe_allow_html=True)

    st.info("💡 **Click any map marker** to see details in the hover tooltip. Use the form below to add a location by clicking on the map coordinates.", icon="ℹ️")

    # Build map
    fig_map = go.Figure()
    place_colors = {"work":"#3b82f6","family":"#ec4899","friends":"#8b5cf6","leisure":"#10b981"}

    for p in st.session_state.places:
        fig_map.add_trace(go.Scattermapbox(
            lat=[p["lat"]], lon=[p["lon"]],
            mode="markers+text",
            marker=dict(size=16, color=place_colors.get(p["type"], "#888"), opacity=1),
            text=[p["name"]], textposition="top right",
            textfont=dict(size=11, color="#1a1a2e"),
            name=f"📍 {p['name']} ({p['type']})",
            hovertemplate=f"<b>{p['name']}</b><br>{p['addr']}<br>Type: {p['type']}<extra></extra>",
        ))

    for a in st.session_state.apartments:
        s = compute_score(a, st.session_state.places, st.session_state.weights)
        color = "#22c55e" if s["final"] >= 7 else "#f59e0b" if s["final"] >= 5 else "#ef4444"
        fig_map.add_trace(go.Scattermapbox(
            lat=[a["lat"]], lon=[a["lon"]],
            mode="markers+text",
            marker=dict(size=20, color=color, opacity=0.9),
            text=[a["name"]], textposition="top right",
            textfont=dict(size=12, color="#1a1a2e"),
            name=f"🏠 {a['name']} ({s['final']}/10)",
            hovertemplate=(
                f"<b>{a['name']}</b><br>{a['addr']}<br>"
                f"Score: {s['final']}/10<br>Your rating: {a['rating']}/10<br>"
                f"Proximity: {s['proximity']}/10<br>Safety: {s['safety']}/10"
                "<extra></extra>"
            ),
        ))

    fig_map.update_layout(
        mapbox=dict(style="carto-positron", center=dict(lat=40.73, lon=-73.95), zoom=11),
        height=520,
        legend=dict(
            # Place legend BELOW the map inside the figure
            orientation="h",
            yanchor="top", y=-0.02,
            xanchor="left", x=0,
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="#eee", borderwidth=1,
            font=dict(size=11),
        ),
        # Extra bottom margin so the horizontal legend doesn't clip
        margin=dict(l=0, r=0, t=0, b=120),
    )
    st.plotly_chart(fig_map, use_container_width=True)

    # ── Click-to-add panel ──────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 📌 Add a location from coordinates")
    st.caption("Copy lat/lon from any map tool (Google Maps, right-click → copy coordinates) and paste below.")

    m1, m2 = st.columns(2)
    click_lat = m1.number_input("Latitude",  value=40.7128, format="%.6f", key="click_lat")
    click_lon = m2.number_input("Longitude", value=-74.0060, format="%.6f", key="click_lon")

    if st.button("🔍 Look up address from coordinates", key="rev_geo_btn"):
        with st.spinner("Reverse geocoding…"):
            addr = reverse_geocode(click_lat, click_lon)
        st.session_state.map_click_addr   = addr
        st.session_state.map_click_coords = (click_lat, click_lon)
        st.rerun()

    if st.session_state.map_click_addr:
        st.success(f"Found: **{st.session_state.map_click_addr}**")
        c1, c2, c3 = st.columns(3)
        mc_label = c1.text_input("Label",    key="mc_label",  placeholder="e.g. Dream Apt")
        mc_what  = c2.selectbox("Add as",   ["apartment","place"], key="mc_what")
        mc_type  = c3.selectbox("Category", ["work","family","friends","leisure"], key="mc_type")

        if st.button("Add this location", key="mc_add_btn", type="primary"):
            coords = st.session_state.map_click_coords
            label  = mc_label or st.session_state.map_click_addr[:40]
            if mc_what == "apartment":
                st.session_state.apartments.append({
                    "id":     st.session_state.next_apt_id,
                    "name":   label,
                    "addr":   st.session_state.map_click_addr,
                    "rating": 7,
                    "lat":    coords[0], "lon": coords[1],
                })
                st.session_state.next_apt_id += 1
            else:
                st.session_state.places.append({
                    "id":   st.session_state.next_place_id,
                    "name": label,
                    "addr": st.session_state.map_click_addr,
                    "type": mc_type,
                    "lat":  coords[0], "lon": coords[1],
                })
                st.session_state.next_place_id += 1
            st.session_state.map_click_addr   = ""
            st.session_state.map_click_coords = None
            st.rerun()

# ════════════════════════════════════════════════════════
# TAB 3 — Rankings
# ════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header">🏆 Apartment rankings</div>', unsafe_allow_html=True)

    if not st.session_state.apartments:
        st.info("Add some apartments in the first tab to see rankings.")
    else:
        if st.button("⚡ Calculate rankings", type="primary", use_container_width=True):
            scored = sorted(
                [{"apt": a, "scores": compute_score(a, st.session_state.places, st.session_state.weights)}
                 for a in st.session_state.apartments],
                key=lambda x: x["scores"]["final"], reverse=True
            )
            for i, item in enumerate(scored):
                item["explanation"] = get_explanation(item["apt"], item["scores"], i + 1, len(scored))
            st.session_state.results = scored

        if st.session_state.results:
            rank_meta = {
                1: ("rank-1",     "rank-1-color",     "🥇", "#22c55e"),
                2: ("rank-2",     "rank-2-color",     "🥈", "#f59e0b"),
                3: ("rank-3",     "rank-3-color",     "🥉", "#a78bfa"),
            }

            for i, item in enumerate(st.session_state.results):
                rank   = i + 1
                a      = item["apt"]
                s      = item["scores"]
                card_cls, badge_cls, emoji, bar_color = rank_meta.get(rank, ("rank-other","rank-other-color",f"#{rank}","#94a3b8"))
                slbl, scls  = safety_label(s["safety"])
                score_cls   = "score-high" if s["final"] >= 7 else "score-mid" if s["final"] >= 5 else "score-low"
                pct         = int(s["final"] / 10 * 100)
                penalty_html = f'<span>⚠️ Distance penalty: <b>-{s["diversity_penalty"]}</b></span>' if s["diversity_penalty"] > 0 else ""

                # Render card shell in HTML
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
                        <div style="background:{bar_color};height:8px;border-radius:6px;width:{pct}%"></div>
                      </div>
                      <div style="display:flex;gap:16px;font-size:0.78rem;color:#666;flex-wrap:wrap;margin-bottom:8px">
                        <span>★ Your rating: <b>{s['personal_rating']}/10</b></span>
                        <span>📍 Proximity: <b>{s['proximity']}/10</b></span>
                        <span>🛡️ Safety: <b>{s['safety']}/10</b></span>
                        {penalty_html}
                      </div>
                    </div>
                  </div>
                </div>""", unsafe_allow_html=True)

                # Explanation rendered OUTSIDE the f-string to avoid HTML injection
                explanation = item.get("explanation", "")
                st.markdown(f"""
                <div class="insight-box">
                  <div class="insight-label">✦ Insight</div>
                  {explanation}
                </div>
                <br>
                """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════
# TAB 4 — Analysis
# ════════════════════════════════════════════════════════
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
        names    = [x["apt"]["name"]              for x in scored_all]
        ratings  = [x["scores"]["personal_rating"] for x in scored_all]
        proxims  = [x["scores"]["proximity"]        for x in scored_all]
        safeties = [x["scores"]["safety"]           for x in scored_all]

        # Stacked bar
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(name="Your rating (35%)", x=names, y=[r*0.35 for r in ratings],  marker_color="#6366f1"))
        fig_bar.add_trace(go.Bar(name="Proximity (40%)",   x=names, y=[p*0.40 for p in proxims],  marker_color="#22c55e"))
        fig_bar.add_trace(go.Bar(name="Safety (15%)",      x=names, y=[s*0.15 for s in safeties], marker_color="#f59e0b"))
        fig_bar.update_layout(
            barmode="stack", title="Score composition per apartment",
            height=350, margin=dict(t=40,b=20),
            plot_bgcolor="white", paper_bgcolor="white",
            font=dict(family="Inter"),
            legend=dict(orientation="h", y=-0.25)
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        # Radar
        top3   = scored_all[:min(3, len(scored_all))]
        colors = ["#6366f1","#22c55e","#f59e0b"]
        fig_radar = go.Figure()
        for i, item in enumerate(top3):
            s = item["scores"]
            fig_radar.add_trace(go.Scatterpolar(
                r=[s["personal_rating"], s["proximity"], s["safety"]],
                theta=["Your rating","Proximity","Safety"],
                fill="toself", name=item["apt"]["name"],
                line_color=colors[i], fillcolor=colors[i], opacity=0.25,
            ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0,10])),
            title="Top 3 apartments — radar comparison",
            height=380, font=dict(family="Inter"), paper_bgcolor="white",
        )
        st.plotly_chart(fig_radar, use_container_width=True)

        # Distance matrix
        st.markdown('<div class="section-header" style="margin-top:1rem">📏 Distance matrix (km)</div>', unsafe_allow_html=True)
        rows = []
        for item in scored_all:
            a   = item["apt"]
            row = {"Apartment": a["name"]}
            for p in st.session_state.places:
                try:    row[p["name"]] = f"{geodesic((a['lat'],a['lon']),(p['lat'],p['lon'])).km:.1f}"
                except: row[p["name"]] = "—"
            rows.append(row)
        st.dataframe(pd.DataFrame(rows).set_index("Apartment"), use_container_width=True)
