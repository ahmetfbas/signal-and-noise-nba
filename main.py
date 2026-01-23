import os
import time
import math
import requests
from datetime import datetime, timedelta

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

def api_get(params):
    r = requests.get(API_URL, headers=HEADERS, params=params, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"API error {r.status_code}: {r.text}")
    return r.json()

def fetch_games(start_date, end_date):
    out = []
    page = 1
    while True:
        payload = api_get({
            "start_date": start_date,
            "end_date": end_date,
            "per_page": 100,
            "page": page,
            "sort": "-date"
        })
        data = payload.get("data", [])
        out.extend(data)

        meta = payload.get("meta", {})
        total_pages = meta.get("total_pages")
        if not total_pages or page >= total_pages:
            break

        page += 1
        time.sleep(0.15)

    return out

def game_dt(g):
    return datetime.fromisoformat(g["date"].replace("Z", "+00:00"))

def is_completed(g):
    return g["home_team_score"] is not None and g["visitor_team_score"] is not None

def haversine(a, b):
    R = 3958.8
    lat1, lon1 = a
    lat2, lon2 = b
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    x = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return round(2 * R * math.atan2(math.sqrt(x), math.sqrt(1-x)))

def density_7(g):
    return 10 if g <= 2 else 40 if g == 3 else 75 if g == 4 else 95

def density_14(g):
    return 10 if g <= 4 else 35 if g == 5 else 55 if g == 6 else 75 if g == 7 else 95

def recovery(days):
    return 0.00 if days <= 1 else 0.10 if days == 2 else 0.25 if days == 3 else 0.40 if days == 4 else 0.55

def fatigue_index(density, days_since, travel):
    b2b = 1 if days_since == 1 else 0
    raw = density + (12 if b2b else 0) + travel * 6 + (10 if b2b and travel >= 2 else 0)
    return round(raw * (1 - recovery(days_since)), 1)

def travel_load(prev_city, cur_city):
    if not prev_city or prev_city == cur_city:
        return 0
    if prev_city not in CITY_COORDS or cur_city not in CITY_COORDS:
        return 1
    m = haversine(CITY_COORDS[prev_city], CITY_COORDS[cur_city])
    return 1 if m < 300 else 2 if m < 800 else 3

def pick_games_today(run_date):
    games = fetch_games(
        (run_date - timedelta(days=1)).isoformat(),
        (run_date + timedelta(days=1)).isoformat()
    )
    return [g for g in games if game_dt(g).date() == run_date]

def print_team_analysis(team, slate_date, games):
    tid = team["id"]
    name = team["full_name"]

    g7 = sum(
        1 for g in games if is_completed(g)
        and tid in (g["home_team"]["id"], g["visitor_team"]["id"])
        and slate_date - timedelta(days=7) <= game_dt(g).date() < slate_date
    )

    g14 = sum(
        1 for g in games if is_completed(g)
        and tid in (g["home_team"]["id"], g["visitor_team"]["id"])
        and slate_date - timedelta(days=14) <= game_dt(g).date() < slate_date
    )

    density = round(0.65 * density_7(g7) + 0.35 * density_14(g14), 1)

    past = sorted(
        [g for g in games if is_completed(g)
         and tid in (g["home_team"]["id"], g["visitor_team"]["id"])
         and game_dt(g).date() < slate_date],
        key=game_dt
    )

    last_date = game_dt(past[-1]).date() if past else None
    days_since = (slate_date - last_date).days if last_date else 5
    prev_city = past[-1]["home_team"]["city"] if past else None
    travel = travel_load(prev_city, team["city"])
    fatigue = fatigue_index(density, days_since, travel)

    print(f"\n🧪 {name}")
    print(f"  games_7d={g7}")
    print(f"  games_14d={g14}")
    print(f"  density={density}")
    print(f"  days_since_last={days_since}")
    print(f"  travel_load={travel}")
    print(f"  fatigue_index={fatigue}")
    print("  margins_last_15d:")

    for g in past:
        gd = game_dt(g).date()
        if slate_date - timedelta(days=15) <= gd < slate_date:
            is_home = g["home_team"]["id"] == tid
            opp = g["visitor_team"]["full_name"] if is_home else g["home_team"]["full_name"]
            ts = g["home_team_score"] if is_home else g["visitor_team_score"]
            os = g["visitor_team_score"] if is_home else g["home_team_score"]
            print(f"    {gd} vs {opp}: {ts - os:+}")

def main():
    RUN_DATE = datetime.utcnow().date()

    games_today = pick_games_today(RUN_DATE)
    if not games_today:
        print("No games today")
        return

    all_games = fetch_games(
        (RUN_DATE - timedelta(days=20)).isoformat(),
        RUN_DATE.isoformat()
    )

    for g in games_today:
        away = g["visitor_team"]
        home = g["home_team"]
        print(f"\n🎯 {away['full_name']} @ {home['full_name']}")
        print_team_analysis(away, RUN_DATE, all_games)
        print_team_analysis(home, RUN_DATE, all_games)

if __name__ == "__main__":
    main()
