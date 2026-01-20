import os
import requests
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
        data = payload.get("data", [])
        all_games.extend(data)

        meta = payload.get("meta", {})
        total_pages = meta.get("total_pages", 1)
        if page >= total_pages:
            break

        page += 1

    return all_games

# ---------------- METRICS ----------------
def parse_game_date(game):
    """Parse balldontlie ISO datetime safely (ROLLED BACK to original)"""
    return datetime.fromisoformat(
        game["date"].replace("Z", "+00:00")
    ).date()

def count_games_before(team_id, games, cutoff_date):
    return sum(
        1
        for g in games
        if (
            (g["home_team"]["id"] == team_id
             or g["visitor_team"]["id"] == team_id)
            and parse_game_date(g) < cutoff_date
        )
    )

def schedule_density_score(g7, g14):
    d7 = g7 / 7
    d14 = g14 / 14
    d_raw = 0.6 * d7 + 0.4 * d14
    return round(100 * d_raw, 1)

def density_label(D):
    if D < 35:
        return "Light"
    elif D < 50:
        return "Moderate"
    elif D < 65:
        return "Heavy"
    else:
        return "Extreme"

def days_since_last_game(team_id, games, cutoff_date, debug=False, team_name=None):
    past_dates = [
        parse_game_date(g)
        for g in games
        if (
            (g["home_team"]["id"] == team_id
             or g["visitor_team"]["id"] == team_id)
            and parse_game_date(g) < cutoff_date
        )
    ]

    if debug:
        print("\n[DEBUG days_since_last_game]")
        print(f"Team: {team_name} (id={team_id})")
        print(f"Cutoff date: {cutoff_date}")
        print(f"Past dates found: {sorted(past_dates)}")

    if not past_dates:
        return None

    last_game = max(past_dates)
    days = (cutoff_date - last_game).days

    if debug:
        print(f"Last game date: {last_game}")
        print(f"Days since last game: {days}\n")

    return days

def rest_context_label(days_since):
    if days_since is None:
        return "No recent games"
    elif days_since == 1:
        return "Back-to-Back"
    elif days_since == 2:
        return "1 day rest"
    else:
        return "3+ days rest"

def b2b_pressure(days_since):
    """
    Back-to-Back Pressure:
    1 = second night of back-to-back
    0 = otherwise
    """
    return 1 if days_since == 1 else 0

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
    "Golden State": (37.7680, -122.3877),
    "Houston": (29.7508, -95.3621),
    "Indiana": (39.7639, -86.1555),
    "LA Clippers": (34.0430, -118.2673),
    "LA Lakers": (34.0430, -118.2673),
    "Memphis": (35.1382, -90.0506),
    "Miami": (25.7814, -80.1870),
    "Milwaukee": (43.0451, -87.9172),
    "Minnesota": (44.9795, -93.2760),
    "New Orleans": (29.9490, -90.0821),
    "New York": (40.7505, -73.9934),
    "Oklahoma City": (35.4634, -97.5151),
    "Orlando": (28.5392, -81.3839),
    "Philadelphia": (39.9012, -75.1720),
    "Phoenix": (33.4457, -112.0712),
    "Portland": (45.5316, -122.6668),
    "Sacramento": (38.5802, -121.4997),
    "San Antonio": (29.4269, -98.4375),
    "Toronto": (43.6435, -79.3791),
    "Utah": (40.7683, -111.9011),
    "Washington": (38.8981, -77.0209),
}

import math

def haversine_miles(lat1, lon1, lat2, lon2):
    """
    Great-circle distance between two points (miles)
    """
    R = 3958.8  # Earth radius in miles

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2

    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def travel_load_distance(last_city, current_city):
    """
    Returns (travel_load, distance_miles, reason)
    """
    if last_city is None:
        return 0, 0, "no prior game"

    if last_city == current_city:
        return 0, 0, "same city"

    if last_city not in CITY_COORDS or current_city not in CITY_COORDS:
        return 1, None, "unknown city coords"

    lat1, lon1 = CITY_COORDS[last_city]
    lat2, lon2 = CITY_COORDS[current_city]

    dist = round(haversine_miles(lat1, lon1, lat2, lon2))

    # Buckets (NBA-realistic)
    if dist < 300:
        return 1, dist, "short travel"
    elif dist < 800:
        return 2, dist, "medium travel"
    else:
        return 3, dist, "long travel"


# ---------------- MAIN ----------------
def main():
    # Slate date (can override)
    target_date = datetime.utcnow().date().isoformat()
    # target_date = "2026-01-20"

    cutoff_date = datetime.fromisoformat(target_date).date()

    print(f"NBA Schedule Density — {target_date}\n")

    # Fetch slate games
    games_today = fetch_games(target_date, target_date)
    if not games_today:
        print("No NBA games on this date.")
        return

    # Fetch historical windows
    start_7d = (cutoff_date - timedelta(days=7)).isoformat()
    start_14d = (cutoff_date - timedelta(days=14)).isoformat()

    # IMPORTANT: history_end includes the full previous day in UTC time
    history_end = (cutoff_date + timedelta(days=1)).isoformat()

    games_7d = fetch_games(start_7d, history_end)
    games_14d = fetch_games(start_14d, history_end)

    debug_team = "Phoenix Suns"  # set None to disable debug

    for game in games_today:
        away = game["visitor_team"]
        home = game["home_team"]

        # Density (strictly before cutoff_date)
        away_7d = count_games_before(away["id"], games_7d, cutoff_date)
        away_14d = count_games_before(away["id"], games_14d, cutoff_date)
        home_7d = count_games_before(home["id"], games_7d, cutoff_date)
        home_14d = count_games_before(home["id"], games_14d, cutoff_date)

        away_D = schedule_density_score(away_7d, away_14d)
        home_D = schedule_density_score(home_7d, home_14d)

        # Days since last game (B2B detection)
        away_rest = days_since_last_game(
            away["id"], games_14d, cutoff_date,
            debug=(debug_team is not None and away["full_name"] == debug_team),
            team_name=away["full_name"]
        )
        home_rest = days_since_last_game(
            home["id"], games_14d, cutoff_date,
            debug=(debug_team is not None and home["full_name"] == debug_team),
            team_name=home["full_name"]
        )

        away_b2b = b2b_pressure(away_rest)
        home_b2b = b2b_pressure(home_rest)

        # Current game cities
        away_city = game["visitor_team"]["city"]
        home_city = game["home_team"]["city"]
        
        # Last game cities
        away_last_city = last_game_location(away["id"], games_14d, cutoff_date)
        home_last_city = last_game_location(home["id"], games_14d, cutoff_date)
        
        # Travel Load (distance-based)
        away_travel, away_miles, away_reason = travel_load_distance(
            away_last_city, away_city
        )
        home_travel, home_miles, home_reason = travel_load_distance(
            home_last_city, home_city
        )

        print(f"{away['full_name']} @ {home['full_name']}")
        print(
            f"• {away['full_name']}: "
            f"{density_label(away_D)} (D={away_D}), "
            f"{rest_context_label(away_rest)}"
        )
        print(f"  → B2B Pressure: {away_b2b}")
        
        print(
            f"• {home['full_name']}: "
            f"{density_label(home_D)} (D={home_D}), "
            f"{rest_context_label(home_rest)}"
        )
        print(f"  → B2B Pressure: {home_b2b}")
        print(f"  → Travel Load: {away_travel} ({away_reason}, {away_miles} mi)")
        print(f"  → Travel Load: {home_travel} ({home_reason}, {home_miles} mi)")
        print()


if __name__ == "__main__":
    main()
