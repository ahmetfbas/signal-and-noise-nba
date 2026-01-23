import os
import time
import math
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

API_URL = "https://api.balldontlie.io/v1/games"
API_KEY = os.getenv("BALLDONTLIE_API_KEY")
if not API_KEY:
    raise ValueError("BALLDONTLIE_API_KEY environment variable not set")

HEADERS = {"Authorization": API_KEY}

CITY_COORDS = {
    "Atlanta": (33.7573, -84.3963),
    "Boston": (42.3662, -71.0621),
    "Brooklyn": (40.6826, -73.9754),
    "Charlotte": (35.2251, -80.8392),
    "Chicago": (41.8807, -87.6742),
    "Cleveland": (41.4965, -81.6882),
    "Dallas": (32.7905, -96.8103),
    "Denver": (39.7487, -105.0077),
    "Detroit": (42.3411, -83.0553),
    "Houston": (29.7508, -95.3621),
    "Indianapolis": (39.7639, -86.1555),
    "Los Angeles": (34.0430, -118.2673),
    "Memphis": (35.1382, -90.0506),
    "Miami": (25.7814, -80.1870),
    "Milwaukee": (43.0451, -87.9172),
    "Minneapolis": (44.9795, -93.2760),
    "New Orleans": (29.9490, -90.0821),
    "New York": (40.7505, -73.9934),
    "Oklahoma City": (35.4634, -97.5151),
    "Orlando": (28.5392, -81.3839),
    "Philadelphia": (39.9012, -75.1720),
    "Phoenix": (33.4457, -112.0712),
    "Portland": (45.5316, -122.6668),
    "Sacramento": (38.5802, -121.4997),
    "San Antonio": (29.4269, -98.4375),
    "San Francisco": (37.7680, -122.3877),
    "Toronto": (43.6435, -79.3791),
    "Salt Lake City": (40.7683, -111.9011),
    "Washington": (38.8981, -77.0209),
}

# ---------------- helpers ----------------
def game_dt(g):
    return datetime.fromisoformat(g["date"].replace("Z", "+00:00"))

def game_date(g):
    return game_dt(g).date()

def is_completed(g):
    return g.get("home_team_score") is not None and g.get("visitor_team_score") is not None

def haversine_miles(a, b):
    R = 3958.8
    lat1, lon1 = a
    lat2, lon2 = b
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    x = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dl/2)**2
    return round(2 * R * math.atan2(math.sqrt(x), math.sqrt(1 - x)))

def density_7d_score(g7):
    if g7 <= 2: return 10
    if g7 == 3: return 40
    if g7 == 4: return 75
    return 95

def density_14d_score(g14):
    if g14 <= 4: return 10
    if g14 == 5: return 35
    if g14 == 6: return 55
    if g14 == 7: return 75
    return 95

def recovery_offset(days):
    if days <= 1: return 0.00
    if days == 2: return 0.10
    if days == 3: return 0.25
    if days == 4: return 0.40
    return 0.55

def fatigue_load_index_v1(density, days_since, travel):
    if days_since is None:
        days_since = 5
    b2b = 1 if days_since == 1 else 0
    raw = density + (12 if b2b else 0) + travel * 6 + (10 if b2b and travel >= 2 else 0)
    return round(raw * (1 - recovery_offset(days_since)), 1)

def travel_load_v1(last_city, target_city):
    if last_city is None or target_city is None:
        return 1, None
    if last_city == target_city:
        return 0, 0
    if last_city not in CITY_COORDS or target_city not in CITY_COORDS:
        return 1, None
    miles = haversine_miles(CITY_COORDS[last_city], CITY_COORDS[target_city])
    if miles < 300: return 1, miles
    if miles < 800: return 2, miles
    return 3, miles

# ---------------- API with cache + backoff ----------------
def _request(params, timeout=30, max_retries=8):
    delay = 0.35
    for attempt in range(max_retries):
        r = requests.get(API_URL, headers=HEADERS, params=params, timeout=timeout)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429:
            ra = r.headers.get("Retry-After")
            if ra:
                try:
                    time.sleep(float(ra))
                except:
                    time.sleep(delay)
            else:
                time.sleep(delay)
                delay = min(delay * 1.8, 6.0)
            continue
        raise RuntimeError(f"API error {r.status_code}: {r.text}")
    raise RuntimeError("API error 429: retries exhausted")

def fetch_games_range(start_date, end_date):
    out = []
    page = 1
    while True:
        payload = _request({
            "start_date": start_date,
            "end_date": end_date,
            "per_page": 100,
            "page": page,
            "sort": "-date",
        })
        data = payload.get("data", [])
        out.extend(data)

        meta = payload.get("meta", {})
        total_pages = meta.get("total_pages")
        if not total_pages or page >= total_pages:
            break

        page += 1
        time.sleep(0.12)
    return out

def cached_games(start_date, end_date, cache_dir=".cache"):
    Path(cache_dir).mkdir(parents=True, exist_ok=True)
    key = f"games_{start_date}_{end_date}.json"
    p = Path(cache_dir) / key
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    data = fetch_games_range(start_date, end_date)
    p.write_text(json.dumps(data), encoding="utf-8")
    return data

# ---------------- slate + outputs ----------------
def pick_games_today(run_date):
    games = cached_games(
        (run_date - timedelta(days=1)).isoformat(),
        (run_date + timedelta(days=1)).isoformat()
    )
    return [g for g in games if game_date(g) == run_date]

def count_team_games(team_id, games, start_d, end_d_exclusive):
    return sum(
        1 for g in games
        if is_completed(g)
        and start_d <= game_date(g) < end_d_exclusive
        and (g["home_team"]["id"] == team_id or g["visitor_team"]["id"] == team_id)
    )

def last_game_before(team_id, games, today):
    past = [
        g for g in games
        if is_completed(g)
        and (g["home_team"]["id"] == team_id or g["visitor_team"]["id"] == team_id)
        and game_date(g) < today
    ]
    if not past:
        return None
    return max(past, key=game_dt)

def team_margin(game, team_id):
    if game["home_team"]["id"] == team_id:
        return game["home_team_score"] - game["visitor_team_score"]
    return game["visitor_team_score"] - game["home_team_score"]

def avg_margin_last_15d(team_id, games, end_date, window_days=15):
    start = end_date - timedelta(days=window_days)
    gs = [
        g for g in games
        if is_completed(g)
        and start <= game_date(g) < end_date
        and (g["home_team"]["id"] == team_id or g["visitor_team"]["id"] == team_id)
    ]
    if not gs:
        return None, 0
    ms = [team_margin(g, team_id) for g in gs]
    return round(sum(ms) / len(ms), 2), len(ms)

def print_team_calc(team, slate_date, games_pool):
    tid = team["id"]
    name = team["full_name"]

    g7 = count_team_games(tid, games_pool, slate_date - timedelta(days=7), slate_date)
    g14 = count_team_games(tid, games_pool, slate_date - timedelta(days=14), slate_date)

    density = round(0.65 * density_7d_score(g7) + 0.35 * density_14d_score(g14), 1)

    last_g = last_game_before(tid, games_pool, slate_date)
    last_date = game_date(last_g) if last_g else None
    days_since = (slate_date - last_date).days if last_date else None

    last_city = last_g["home_team"]["city"] if last_g else None
    target_city = team.get("city")
    travel, miles = travel_load_v1(last_city, target_city)

    fatigue = fatigue_load_index_v1(density, days_since, travel)

    avg15, n15 = avg_margin_last_15d(tid, games_pool, slate_date, window_days=15)

    print(f"\n{name}")
    print(f"g7={g7} g14={g14} density={density}")
    print(f"last_date={last_date} days_since={days_since}")
    print(f"last_city={last_city} target_city={target_city} miles={miles} travel_load={travel}")
    print(f"fatigue={fatigue}")
    print(f"avg_margin_15d={avg15} games_in_15d={n15}")

def main():
    RUN_DATE = datetime.utcnow().date()

    games_today = pick_games_today(RUN_DATE)
    if not games_today:
        print(f"No games scheduled on {RUN_DATE}.")
        return

    pool_start = (RUN_DATE - timedelta(days=40)).isoformat()
    pool_end = RUN_DATE.isoformat()
    games_pool = cached_games(pool_start, pool_end)

    for g in sorted(games_today, key=game_dt):
        away = g["visitor_team"]
        home = g["home_team"]
        print(f"\n🎯 {away['full_name']} @ {home['full_name']}")
        print_team_calc(away, RUN_DATE, games_pool)
        print_team_calc(home, RUN_DATE, games_pool)

if __name__ == "__main__":
    main()
