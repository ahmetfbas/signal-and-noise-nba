import os
import requests
import math
from datetime import datetime, timedelta

API_URL = "https://api.balldontlie.io/v1/games"
API_KEY = os.getenv("BALLDONTLIE_API_KEY")

if not API_KEY:
    raise ValueError("BALLDONTLIE_API_KEY environment variable not set")

HEADERS = {"Authorization": API_KEY}

# ---------------- API (with pagination) ----------------
def fetch_games(start_date, end_date):
    all_games = []
    page = 1

    while True:
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "per_page": 100,
            "page": page
        }

        response = requests.get(API_URL, headers=HEADERS, params=params)
        if response.status_code != 200:
            print("API error:", response.status_code)
            print(response.text)
            return []

        payload = response.json()
        all_games.extend(payload.get("data", []))

        meta = payload.get("meta", {})
        if page >= meta.get("total_pages", 1):
            break

        page += 1

    return all_games

# ---------------- DATE ----------------
def parse_game_date(game):
    return datetime.fromisoformat(
        game["date"].replace("Z", "+00:00")
    ).date()

# ---------------- METRICS ----------------
def count_games_before(team_id, games, cutoff_date):
    return sum(
        1 for g in games
        if (
            (g["home_team"]["id"] == team_id
             or g["visitor_team"]["id"] == team_id)
            and parse_game_date(g) < cutoff_date
        )
    )

def schedule_density_score(g7, g14):
    return round(100 * (0.6 * g7 / 7 + 0.4 * g14 / 14), 1)

def density_label(D):
    if D < 35: return "Light"
    if D < 50: return "Moderate"
    if D < 65: return "Heavy"
    return "Extreme"

def days_since_last_game(team_id, games, cutoff_date):
    past_dates = [
        parse_game_date(g)
        for g in games
        if (
            (g["home_team"]["id"] == team_id
             or g["visitor_team"]["id"] == team_id)
            and parse_game_date(g) < cutoff_date
        )
    ]
    return None if not past_dates else (cutoff_date - max(past_dates)).days

def rest_context_label(days_since):
    if days_since == 1: return "Back-to-Back"
    if days_since == 2: return "1 day rest"
    if days_since is None: return "No recent games"
    return "3+ days rest"

def b2b_pressure(days_since):
    return 1 if days_since == 1 else 0

# ---------------- TRAVEL (DISTANCE) ----------------

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
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    return round(2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

def last_game_location(team_id, games, cutoff_date):
    past_games = [
        (parse_game_date(g), g)
        for g in games
        if (
            (g["home_team"]["id"] == team_id
             or g["visitor_team"]["id"] == team_id)
            and parse_game_date(g) < cutoff_date
        )
    ]
    if not past_games:
        return None

    _, g = max(past_games, key=lambda x: x[0])
    return g["home_team"]["city"] if g["home_team"]["id"] == team_id else g["visitor_team"]["city"]

def travel_load_distance(last_city, current_city):
    if last_city is None or last_city == current_city:
        return 0, 0, "no / same-city travel"

    if last_city not in CITY_COORDS or current_city not in CITY_COORDS:
        return 1, None, "unknown city coords"

    lat1, lon1 = CITY_COORDS[last_city]
    lat2, lon2 = CITY_COORDS[current_city]
    dist = haversine_miles(lat1, lon1, lat2, lon2)

    if dist < 300: return 1, dist, "short travel"
    if dist < 800: return 2, dist, "medium travel"
    return 3, dist, "long travel"

# ---------------- MAIN ----------------
def main():
    target_date = datetime.utcnow().date().isoformat()
    cutoff_date = datetime.fromisoformat(target_date).date()

    print(f"NBA Schedule Density — {target_date}\n")

    games_today = fetch_games(target_date, target_date)
    if not games_today:
        return

    history_end = (cutoff_date + timedelta(days=1)).isoformat()
    games_7d = fetch_games((cutoff_date - timedelta(days=7)).isoformat(), history_end)
    games_14d = fetch_games((cutoff_date - timedelta(days=14)).isoformat(), history_end)

    for game in games_today:
        away, home = game["visitor_team"], game["home_team"]

        away_rest = days_since_last_game(away["id"], games_14d, cutoff_date)
        home_rest = days_since_last_game(home["id"], games_14d, cutoff_date)

        away_last_city = last_game_location(away["id"], games_14d, cutoff_date)
        home_last_city = last_game_location(home["id"], games_14d, cutoff_date)

        away_travel, away_miles, away_reason = travel_load_distance(
            away_last_city, away["city"]
        )
        home_travel, home_miles, home_reason = travel_load_distance(
            home_last_city, home["city"]
        )

        print(f"{away['full_name']} @ {home['full_name']}")
        print(f"• {away['full_name']}: {rest_context_label(away_rest)}")
        print(f"  → B2B Pressure: {b2b_pressure(away_rest)}")
        print(f"  → Travel Load: {away_travel} ({away_reason}, {away_miles} mi)")
        print(f"• {home['full_name']}: {rest_context_label(home_rest)}")
        print(f"  → B2B Pressure: {b2b_pressure(home_rest)}")
        print(f"  → Travel Load: {home_travel} ({home_reason}, {home_miles} mi)\n")

if __name__ == "__main__":
    main()
