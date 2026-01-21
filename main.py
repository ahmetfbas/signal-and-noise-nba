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

        resp = requests.get(API_URL, headers=HEADERS, params=params)
        if resp.status_code != 200:
            raise RuntimeError(f"API error {resp.status_code}: {resp.text}")

        payload = resp.json()
        all_games.extend(payload.get("data", []))

        if page >= payload.get("meta", {}).get("total_pages", 1):
            break

        page += 1

    return all_games


# ---------------- DATE HELPERS ----------------
def game_datetime(game):
    return datetime.fromisoformat(game["date"].replace("Z", "+00:00"))


# ---------------- DENSITY HELPERS ----------------
def count_games_in_window(team_id, games, start_date, end_date):
    """
    Counts games where:
    start_date <= game_date < end_date
    """
    count = 0
    for g in games:
        gd = game_datetime(g).date()
        if start_date <= gd < end_date:
            if g["home_team"]["id"] == team_id or g["visitor_team"]["id"] == team_id:
                count += 1
    return count


def density_7d_score(g7):
    if g7 <= 2:
        return 10
    if g7 == 3:
        return 40
    if g7 == 4:
        return 75
    return 95


def density_14d_score(g14):
    if g14 <= 4:
        return 10
    if g14 == 5:
        return 35
    if g14 == 6:
        return 55
    if g14 == 7:
        return 75
    return 95

def back_to_back_pressure(last_game_date, today):
    """
    Returns 1 if team played yesterday, else 0
    """
    if last_game_date is None:
        return 0
    return 1 if (today - last_game_date).days == 1 else 0

def last_game_before(team_id, games, today):
    """
    Returns the most recent game date strictly before today
    """
    past_games = [
        game_datetime(g).date()
        for g in games
        if (
            (g["home_team"]["id"] == team_id or g["visitor_team"]["id"] == team_id)
            and game_datetime(g).date() < today
        )
    ]
    return max(past_games) if past_games else None

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

def last_game_city(team_id, games, today):
    """
    Returns the city where the team played its most recent game before today
    """
    past_games = [
        g for g in games
        if (
            (g["home_team"]["id"] == team_id or g["visitor_team"]["id"] == team_id)
            and game_datetime(g).date() < today
        )
    ]

    if not past_games:
        return None

    last_game = max(past_games, key=game_datetime)
    return last_game["home_team"]["city"]  # game location

def travel_load_v1(last_city, target_city):
    if last_city is None or target_city is None:
        return 1, None, "unknown (missing city)"

    if last_city == target_city:
        return 0, 0, "no travel / same city"

    if last_city not in CITY_COORDS or target_city not in CITY_COORDS:
        return 1, None, "unknown (no coords)"

    miles = haversine_miles(
        *CITY_COORDS[last_city],
        *CITY_COORDS[target_city]
    )

    if miles < 300:
        return 1, miles, "short travel"
    if miles < 800:
        return 2, miles, "medium travel"
    return 3, miles, "long travel"

def recovery_offset(days_since_last_game):
    if days_since_last_game is None:
        return 0.30  # neutral fallback

    if days_since_last_game == 0:
        return 0.00
    if days_since_last_game == 1:
        return 0.10
    if days_since_last_game == 2:
        return 0.25
    if days_since_last_game == 3:
        return 0.40
    return 0.55


# ---------------- MAIN ----------------
def main():
    today = datetime.utcnow().date()

    print(f"Today : {today.isoformat()}")

    # --- Fetch windows (date logic unchanged) ---
    start_7 = (today - timedelta(days=6)).isoformat()
    start_14 = (today - timedelta(days=13)).isoformat()
    end_date = today.isoformat()

    games_last_7 = fetch_games(start_7, end_date)
    games_last_14 = fetch_games(start_14, end_date)

    # --- Teams playing today ---
    teams_today = {}
    for g in games_last_7:
        if game_datetime(g).date() == today:
            home = g["home_team"]
            away = g["visitor_team"]
            teams_today[home["id"]] = home["full_name"]
            teams_today[away["id"]] = away["full_name"]

    print("\nDENSITY + B2B — Teams playing today\n")

    # --- Metrics per team ---
    for team_id, team_name in teams_today.items():
        # Density counts (strictly before today)
        g7 = count_games_in_window(
            team_id,
            games_last_7,
            today - timedelta(days=7),
            today
        )

        g14 = count_games_in_window(
            team_id,
            games_last_14,
            today - timedelta(days=14),
            today
        )

        # Density scores
        d7 = density_7d_score(g7)
        d14 = density_14d_score(g14)
        density = round(0.65 * d7 + 0.35 * d14, 1)

        # Back-to-back
        last_game_date = last_game_before(team_id, games_last_14, today)
        days_since = (today - last_game_date).days if last_game_date else None
        b2b = back_to_back_pressure(last_game_date, today)
        rec_offset = recovery_offset(days_since)

        # --- Travel Load ---
        last_city = last_game_city(team_id, games_last_14, today)
        target_city = next(
            g["home_team"]["city"]
            for g in games_last_7
            if game_datetime(g).date() == today
            and (g["home_team"]["id"] == team_id or g["visitor_team"]["id"] == team_id)
        )

        travel_score, miles, travel_reason = travel_load_v1(last_city, target_city)

        
        print(
            f"{team_name}\n"
            f"  Density:\n"
            f"    G7  = {g7}  → D7  = {d7}\n"
            f"    G14 = {g14} → D14 = {d14}\n"
            f"    Blended D = {density}\n"
            f"  Back-to-Back:\n"
            f"    Last game date = {last_game_date}\n"
            f"    Days since     = {days_since if days_since is not None else 'N/A'}\n"
            f"  Recovery Offset: {rec_offset}\n"
            f"    B2B Pressure   = {b2b}\n"
            f"  Travel:\n"
            f"    Last game city = {last_city}\n"
            f"    Target city    = {target_city}\n"
            f"    Distance       = {miles if miles is not None else 'N/A'} miles\n"
            f"    Travel Load    = {travel_score} ({travel_reason})\n"
        )


if __name__ == "__main__":
    main()
