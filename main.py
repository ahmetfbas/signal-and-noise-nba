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

# ---------------- SCHEDULE HELPERS ----------------
def last_game_info(team_id, games, cutoff_date):
    """
    Returns (last_game_date, last_game_city)
    strictly before cutoff_date.
    """
    past_games = []

    for g in games:
        if g["home_team"]["id"] == team_id or g["visitor_team"]["id"] == team_id:
            gd = parse_game_date(g)
            if gd < cutoff_date:
                past_games.append((gd, g))

    if not past_games:
        return None, None

    last_date, g = max(past_games, key=lambda x: x[0])

    if g["home_team"]["id"] == team_id:
        city = g["home_team"]["city"]
    else:
        city = g["visitor_team"]["city"]

    return last_date, city

def days_since_last_game(last_game_date, cutoff_date):
    if last_game_date is None:
        return None
    return (cutoff_date - last_game_date).days

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
    target_date = datetime.utcnow().date().isoformat()
    cutoff_date = datetime.fromisoformat(target_date).date()

    print(f"NBA Schedule Debug — {target_date}\n")

    games_today = fetch_games(target_date, target_date)
    if not games_today:
        return

    games_14d = fetch_games(
        (cutoff_date - timedelta(days=14)).isoformat(),
        target_date
    )

    for game in games_today:
        away = game["visitor_team"]
        home = game["home_team"]

        # Last game info
        away_last_date, away_last_city = last_game_info(
            away["id"], games_14d, cutoff_date
        )
        home_last_date, home_last_city = last_game_info(
            home["id"], games_14d, cutoff_date
        )

        away_days_rest = days_since_last_game(away_last_date, cutoff_date)
        home_days_rest = days_since_last_game(home_last_date, cutoff_date)

        print(f"{away['full_name']} @ {home['full_name']}")

        print(
            f"• {away['full_name']}\n"
            f"  Target game date : {cutoff_date}\n"
            f"  Last game date   : {away_last_date}\n"
            f"  Target city      : {away['city']}\n"
            f"  Last game city   : {away_last_city}\n"
            f"  Rest context     : {rest_context_label(away_days_rest)}"
        )

        print(
            f"• {home['full_name']}\n"
            f"  Target game date : {cutoff_date}\n"
            f"  Last game date   : {home_last_date}\n"
            f"  Target city      : {home['city']}\n"
            f"  Last game city   : {home_last_city}\n"
            f"  Rest context     : {rest_context_label(home_days_rest)}"
        )

        print()

if __name__ == "__main__":
    main()
