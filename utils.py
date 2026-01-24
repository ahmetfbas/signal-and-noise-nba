import os
import time
import math
import requests
from datetime import datetime

API_URL = "https://api.balldontlie.io/v1/games"
API_KEY = os.getenv("BALLDONTLIE_API_KEY")

if not API_KEY:
    raise ValueError("BALLDONTLIE_API_KEY not set")

HEADERS = {"Authorization": API_KEY}


def api_get(params, timeout=30, retries=3, base_sleep=0.2):
    for i in range(retries):
        resp = requests.get(API_URL, headers=HEADERS, params=params, timeout=timeout)
        if resp.status_code == 200:
            time.sleep(base_sleep)
            return resp.json()
        if resp.status_code == 429 and i < retries - 1:
            time.sleep(base_sleep * (i + 1))
            continue
        raise RuntimeError(f"{resp.status_code}: {resp.text}")
    raise RuntimeError("API failed after retries")


def fetch_games_range(start_date, end_date, sort="-date"):
    out = []
    page = 1
    while True:
        payload = api_get({
            "start_date": start_date,
            "end_date": end_date,
            "per_page": 100,
            "page": page,
            "sort": sort
        })
        data = payload.get("data", [])
        if not data:
            break
        out.extend(data)
        meta = payload.get("meta", {})
        if page >= meta.get("total_pages", 1):
            break
        page += 1
    return out


def game_datetime(g):
    return datetime.fromisoformat(g["date"].replace("Z", "+00:00"))


def game_date(g):
    return game_datetime(g).date()


def is_completed(g):
    return g.get("home_team_score") is not None and g.get("visitor_team_score") is not None


def team_in_game(g, team_id):
    return g["home_team"]["id"] == team_id or g["visitor_team"]["id"] == team_id


def margin_for_team(g, team_id):
    is_home = g["home_team"]["id"] == team_id
    ts = g["home_team_score"] if is_home else g["visitor_team_score"]
    os = g["visitor_team_score"] if is_home else g["home_team_score"]
    return ts - os

def recent_average_margin(team_id, end_date, window_days=15):
    from datetime import timedelta

    start_date = end_date - timedelta(days=window_days)
    games = fetch_games_range(start_date.isoformat(), end_date.isoformat())

    margins = [
        margin_for_team(g, team_id)
        for g in games
        if is_completed(g) and team_in_game(g, team_id)
    ]

    if not margins:
        return 0.0

    return sum(margins) / len(margins)

def expected_margin_base(game, team_id, run_date, window_days=15):
    home_id = game["home_team"]["id"]
    away_id = game["visitor_team"]["id"]

    opponent_id = away_id if team_id == home_id else home_id

    team_form = recent_average_margin(team_id, run_date, window_days)
    opp_form = recent_average_margin(opponent_id, run_date, window_days)

    return team_form - opp_form
    
def home_away_adjustment(game, team_id):
    HOME_ADVANTAGE = 2.0  # fixed for now

    if game["home_team"]["id"] == team_id:
        return HOME_ADVANTAGE
    else:
        return -HOME_ADVANTAGE
        
def expected_margin_for_team(game, team_id, run_date):
    base = expected_margin_base(game, team_id, run_date)
    ha = home_away_adjustment(game, team_id)

    return base + ha


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


def haversine_miles(lat1, lon1, lat2, lon2):
    R = 3958.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return round(2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 1)


def travel_miles(city_a, city_b):
    if city_a not in CITY_COORDS or city_b not in CITY_COORDS:
        return None
    return haversine_miles(*CITY_COORDS[city_a], *CITY_COORDS[city_b])
