import os
import requests
from datetime import datetime, timedelta
import math

API_URL = "https://api.balldontlie.io/v1/games"
API_KEY = os.getenv("BALLDONTLIE_API_KEY")

if not API_KEY:
    raise ValueError("BALLDONTLIE_API_KEY environment variable not set")

HEADERS = {"Authorization": API_KEY}

# ---------------- API ----------------
def fetch_games(start_date: str, end_date: str):
    all_games = []
    page = 1

    while True:
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "per_page": 100,
            "page": page
        }

        resp = requests.get(API_URL, headers=HEADERS, params=params, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"API error {resp.status_code}: {resp.text}")

        payload = resp.json()
        data = payload.get("data", [])
        all_games.extend(data)

        if page >= payload.get("meta", {}).get("total_pages", 1):
            break

        page += 1

    return all_games

# ---------------- DATE HELPERS ----------------
def game_datetime(game):
    return datetime.fromisoformat(game["date"].replace("Z", "+00:00"))

def game_date(game):
    return game_datetime(game).date()

# ---------------- DENSITY HELPERS ----------------
def count_games_in_window(team_id, games, start_date, end_date):
    return sum(
        1 for g in games
        if start_date <= game_date(g) < end_date
        and (g["home_team"]["id"] == team_id or g["visitor_team"]["id"] == team_id)
    )

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

def back_to_back_pressure(days_since):
    return 1 if days_since == 1 else 0

def last_game_before(team_id, games, today):
    past = [
        game_date(g) for g in games
        if (g["home_team"]["id"] == team_id or g["visitor_team"]["id"] == team_id)
        and game_date(g) < today
    ]
    return max(past) if past else None

# ---------------- TRAVEL ----------------
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
    return round(2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

def last_game_city(team_id, games, today):
    past = [
        g for g in games
        if (g["home_team"]["id"] == team_id or g["visitor_team"]["id"] == team_id)
        and game_date(g) < today
    ]
    if not past:
        return None
    return max(past, key=game_datetime)["home_team"]["city"]

def travel_load_v1(last_city, target_city):
    if not last_city or not target_city:
        return 1
    if last_city == target_city:
        return 0
    if last_city not in CITY_COORDS or target_city not in CITY_COORDS:
        return 1
    miles = haversine_miles(*CITY_COORDS[last_city], *CITY_COORDS[target_city])
    if miles < 300: return 1
    if miles < 800: return 2
    return 3

def recovery_offset(days):
    if days <= 1: return 0.00
    if days == 2: return 0.10
    if days == 3: return 0.25
    if days == 4: return 0.40
    return 0.55

def fatigue_load_index_v1(density, days_since, travel):
    if days_since is None:
        days_since = 5

    b2b = back_to_back_pressure(days_since)
    raw = density + (12 if b2b else 0) + travel * 6 + (10 if b2b and travel >= 2 else 0)
    return round(raw * (1 - recovery_offset(days_since)), 1)

def fatigue_risk_tier(score):
    if score < 30: return "Low"
    if score < 50: return "Elevated"
    if score < 70: return "High"
    return "Critical"

def print_scores_last_30_days(run_date):
    start_date = (run_date - timedelta(days=29)).isoformat()
    end_date = run_date.isoformat()

    games = fetch_games(start_date, end_date)

    # Only completed games
    completed = [
        g for g in games
        if g.get("home_team_score") is not None
        and g.get("visitor_team_score") is not None
    ]

    # Sort by date, oldest → newest
    completed.sort(key=game_datetime)

    print(f"\n🏀 NBA Game Scores — Last 30 Days (ending {run_date})\n")

    current_day = None
    for g in completed:
        gd = game_date(g)
        if gd != current_day:
            current_day = gd
            print(f"\n📅 {gd}")

        away = g["visitor_team"]["full_name"]
        home = g["home_team"]["full_name"]
        away_score = g["visitor_team_score"]
        home_score = g["home_team_score"]

        print(f"{away} {away_score} @ {home} {home_score}")


# ---------------- MAIN ----------------
def main():
    RUN_DATE = datetime(2026, 1, 22).date()

    print_scores_last_30_days(RUN_DATE)
    
    start_7 = (RUN_DATE - timedelta(days=6)).isoformat()
    start_14 = (RUN_DATE - timedelta(days=13)).isoformat()

    games_last_7 = fetch_games(start_7, RUN_DATE.isoformat())
    games_last_14 = fetch_games(start_14, RUN_DATE.isoformat())

    games_today = [g for g in games_last_7 if game_date(g) == RUN_DATE]

    team_results = {}

    for g in games_today:
        for team in [g["home_team"], g["visitor_team"]]:
            tid = team["id"]
            if tid in team_results:
                continue

            g7 = count_games_in_window(tid, games_last_7, RUN_DATE - timedelta(days=7), RUN_DATE)
            g14 = count_games_in_window(tid, games_last_14, RUN_DATE - timedelta(days=14), RUN_DATE)

            density = round(
                0.65 * density_7d_score(g7) + 0.35 * density_14d_score(g14),
                1
            )

            last_date = last_game_before(tid, games_last_14, RUN_DATE)
            days_since = (RUN_DATE - last_date).days if last_date else None

            last_city = last_game_city(tid, games_last_14, RUN_DATE)
            target_city = g["home_team"]["city"]
            travel = travel_load_v1(last_city, target_city)

            fatigue = fatigue_load_index_v1(density, days_since, travel)

            team_results[tid] = {
                "name": team["full_name"],
                "fatigue": fatigue,
                "tier": fatigue_risk_tier(fatigue)
            }

    print(f"\n🏀 NBA Fatigue Index — {RUN_DATE}\n")

    emoji = {"Low": "🟢", "Elevated": "🟡", "High": "🟠", "Critical": "🔴"}

    for g in games_today:
        away = g["visitor_team"]
        home = g["home_team"]

        a = team_results[away["id"]]
        h = team_results[home["id"]]

        print(
            f"{away['full_name']} @ {home['full_name']}\n"
            f"{emoji[a['tier']]} {away['full_name']} — {a['tier']} ({a['fatigue']})\n"
            f"{emoji[h['tier']]} {home['full_name']} — {h['tier']} ({h['fatigue']})\n"
        )

if __name__ == "__main__":
    main()
