import os
import requests
from datetime import datetime, timedelta
from collections import defaultdict

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

def game_day_str(game):
    """
    Day label as the API effectively exposes it.
    """
    return game_datetime(game).date().isoformat()

# ---------------- MAIN DEBUG ----------------
def main():
    target_date = datetime.utcnow().date().isoformat()
    start_date = (datetime.fromisoformat(target_date) - timedelta(days=14)).date().isoformat()

    print(f"\nNBA API DEBUG — Games grouped by day")
    print(f"Range: {start_date} → {target_date}\n")

    games = fetch_games(start_date, target_date)

    # Group games by API-derived day
    games_by_day = defaultdict(list)
    for g in games:
        games_by_day[game_day_str(g)].append(g)

    # Print days in order
    for day in sorted(games_by_day.keys()):
        print(f"📅 {day} — {len(games_by_day[day])} games")

        for g in games_by_day[day]:
            away = g["visitor_team"]["full_name"]
            home = g["home_team"]["full_name"]
            tip = game_datetime(g).strftime("%Y-%m-%d %H:%M UTC")

            print(f"  {away} @ {home}  | tipoff: {tip}")

        print("-" * 60)

if __name__ == "__main__":
    main()
