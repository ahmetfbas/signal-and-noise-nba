import os
import requests
from datetime import datetime, timedelta

API_URL = "https://api.balldontlie.io/v1/games"
API_KEY = os.getenv("BALLDONTLIE_API_KEY")

if not API_KEY:
    raise ValueError("BALLDONTLIE_API_KEY environment variable not set")

HEADERS = {"Authorization": API_KEY}

# ---------------- API (pagination) ----------------
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

        if page >= payload.get("meta", {}).get("total_pages", 1):
            break

        page += 1

    return all_games

# ---------------- HELPERS ----------------
def team_played_in_games(team_id, games):
    for g in games:
        if g["home_team"]["id"] == team_id or g["visitor_team"]["id"] == team_id:
            return True, g
    return False, None

def last_game_info_by_day(team_id, target_date_obj, lookback_days=14):
    """
    Finds last game by walking back day-by-day using the API date filter
    (most stable across timezone quirks).
    Returns: (last_game_date_obj, last_game_city)
    """
    for delta in range(1, lookback_days + 1):
        day = target_date_obj - timedelta(days=delta)
        day_str = day.isoformat()

        games_that_day = fetch_games(day_str, day_str)
        played, game_obj = team_played_in_games(team_id, games_that_day)

        if played:
            # City where the game was played is always the HOME team's city
            last_city = game_obj["home_team"]["city"]
            return day, last_city

    return None, None

def rest_context_label(days_since):
    if days_since == 1:
        return "Back-to-Back"
    if days_since == 2:
        return "1 day rest"
    if days_since is None:
        return "No recent games"
    return "3+ days rest"

# ---------------- MAIN ----------------
def main():
    # Slate day (API-driven daily run)
    target_date_str = datetime.utcnow().date().isoformat()
    target_date_obj = datetime.fromisoformat(target_date_str).date()

    print(f"NBA Schedule Debug — {target_date_str}\n")

    games_today = fetch_games(target_date_str, target_date_str)
    if not games_today:
        return

    for game in games_today:
        away = game["visitor_team"]
        home = game["home_team"]

        # Target city is ALWAYS home team city (game location)
        target_city = home["city"]

        # Find last game (date + city) using day-by-day API lookback
        away_last_date, away_last_city = last_game_info_by_day(away["id"], target_date_obj, lookback_days=14)
        home_last_date, home_last_city = last_game_info_by_day(home["id"], target_date_obj, lookback_days=14)

        away_days_rest = None if away_last_date is None else (target_date_obj - away_last_date).days
        home_days_rest = None if home_last_date is None else (target_date_obj - home_last_date).days

        print(f"{away['full_name']} @ {home['full_name']}")

        print(
            f"• {away['full_name']}\n"
            f"  Target game date : {target_date_obj}\n"
            f"  Last game date   : {away_last_date}\n"
            f"  Target city      : {target_city}\n"
            f"  Last game city   : {away_last_city}\n"
            f"  Rest context     : {rest_context_label(away_days_rest)}"
        )

        print(
            f"• {home['full_name']}\n"
            f"  Target game date : {target_date_obj}\n"
            f"  Last game date   : {home_last_date}\n"
            f"  Target city      : {target_city}\n"
            f"  Last game city   : {home_last_city}\n"
            f"  Rest context     : {rest_context_label(home_days_rest)}"
        )

        print()

if __name__ == "__main__":
    main()
