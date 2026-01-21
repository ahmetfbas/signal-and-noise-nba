import os
import requests
import math
from datetime import datetime, timedelta

API_URL = "https://api.balldontlie.io/v1/games"
API_KEY = os.getenv("BALLDONTLIE_API_KEY")

if not API_KEY:
    raise ValueError("BALLDONTLIE_API_KEY environment variable not set")

HEADERS = {"Authorization": API_KEY}

# ---------------- API ----------------
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
            raise RuntimeError(f"API error {response.status_code}: {response.text}")

        payload = response.json()
        all_games.extend(payload.get("data", []))

        if page >= payload.get("meta", {}).get("total_pages", 1):
            break

        page += 1

    return all_games

# ---------------- HELPERS ----------------
def game_datetime(game):
    return datetime.fromisoformat(game["date"].replace("Z", "+00:00"))

def rest_context_label(days_since):
    if days_since is None:
        return "No recent games"
    if days_since == 1:
        return "Back-to-Back"
    if days_since == 2:
        return "1 off-day"
    if days_since == 3:
        return "2 off-days"
    return "3+ off-days"

def last_game_before(team_id, all_games, current_game):
    """
    Finds the last game this team played before current_game.
    Returns (date, city)
    """
    current_dt = game_datetime(current_game)
    current_game_id = current_game["id"]

    team_games = [
        g for g in all_games
        if g["id"] != current_game_id
        and (g["home_team"]["id"] == team_id or g["visitor_team"]["id"] == team_id)
        and game_datetime(g) < current_dt
    ]

    if not team_games:
        return None, None

    last_game = max(team_games, key=game_datetime)
    last_date = game_datetime(last_game).date()
    last_city = last_game["home_team"]["city"]  # game location

    return last_date, last_city

# ---------------- TRAVEL LOAD v1 ----------------
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
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def travel_load_v1(last_city, target_city):
    if last_city is None or target_city is None:
        return 1, None, "unknown (missing city)"

    if last_city == target_city:
        return 0, 0, "no travel / same city"

    if last_city not in CITY_COORDS or target_city not in CITY_COORDS:
        return 1, None, "unknown (no coords)"

    miles = round(
        haversine_miles(*CITY_COORDS[last_city], *CITY_COORDS[target_city])
    )

    if miles < 300:
        return 1, miles, "short travel"
    if miles < 800:
        return 2, miles, "medium travel"
    return 3, miles, "long travel"

# ---------------- MAIN ----------------
def main():
    target_date = datetime.utcnow().date().isoformat()
    print(f"NBA Schedule Debug — {target_date}\n")

    games_today = fetch_games(target_date, target_date)
    if not games_today:
        return

    history_start = (datetime.fromisoformat(target_date) - timedelta(days=15)).date().isoformat()
    history_end = (datetime.fromisoformat(target_date) + timedelta(days=1)).date().isoformat()

    all_recent_games = fetch_games(history_start, history_end)

    for game in games_today:
        away = game["visitor_team"]
        home = game["home_team"]

        target_city = home["city"]
        target_game_date = game_datetime(game).date()

        away_last_date, away_last_city = last_game_before(away["id"], all_recent_games, game)
        home_last_date, home_last_city = last_game_before(home["id"], all_recent_games, game)

        away_days_rest = None if away_last_date is None else (target_game_date - away_last_date).days
        home_days_rest = None if home_last_date is None else (target_game_date - home_last_date).days

        away_travel, away_miles, away_reason = travel_load_v1(away_last_city, target_city)
        home_travel, home_miles, home_reason = travel_load_v1(home_last_city, target_city)

        print(f"{away['full_name']} @ {home['full_name']}")
        print(
            f"• {away['full_name']}\n"
            f"  Rest context : {rest_context_label(away_days_rest)}\n"
            f"  Travel load  : {away_travel} ({away_reason}, {away_miles} mi)"
        )
        print(
            f"• {home['full_name']}\n"
            f"  Rest context : {rest_context_label(home_days_rest)}\n"
            f"  Travel load  : {home_travel} ({home_reason}, {home_miles} mi)"
        )
        print()

if __name__ == "__main__":
    main()
