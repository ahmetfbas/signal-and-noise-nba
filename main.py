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

def game_datetime(game):
    return datetime.fromisoformat(game["date"].replace("Z", "+00:00"))

# ---------------- PRINT ----------------
def print_games_by_day(games, title):
    print(f"\n{title}")
    print("=" * len(title))

    if not games:
        print("No games.\n")
        return

    games_by_day = defaultdict(list)
    for g in games:
        day = game_datetime(g).date().isoformat()
        games_by_day[day].append(g)

    for day in sorted(games_by_day.keys()):
        print(f"📅 {day} — {len(games_by_day[day])} games")

        for g in games_by_day[day]:
            away = g["visitor_team"]["full_name"]
            home = g["home_team"]["full_name"]
            tip = game_datetime(g).strftime("%Y-%m-%d %H:%M UTC")
            print(f"  {away} @ {home} | tipoff: {tip}")

        print("-" * 60)

# ---------------- MAIN ----------------
def main():
    today = datetime.utcnow().date()

    start_date = (today - timedelta(days=3)).isoformat()
    end_date = (today + timedelta(days=3)).isoformat()

    games = fetch_games(start_date, end_date)
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    
    print(f"Yesterday : {yesterday}")
    print(f"Today     : {today}")
    print_games_by_day(
        games,
        f"NBA API — Games from LAST 3 days, TODAY, NEXT 3 days ({start_date} → {end_date})"
    )

if __name__ == "__main__":
    main()
