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


def game_datetime(game):
    return datetime.fromisoformat(game["date"].replace("Z", "+00:00"))


def game_day(game):
    return game_datetime(game).date().isoformat()


# ---------------- PRINT ----------------
def print_games_grouped_by_day(games, title):
    print(f"\n{title}")
    print("=" * len(title))

    if not games:
        print("No games.")
        return

    by_day = defaultdict(list)
    for g in games:
        by_day[game_day(g)].append(g)

    for day in sorted(by_day.keys()):
        print(f"📅 {day} — {len(by_day[day])} games")
        for g in by_day[day]:
            away = g["visitor_team"]["full_name"]
            home = g["home_team"]["full_name"]
            tip = game_datetime(g).strftime("%Y-%m-%d %H:%M UTC")
            print(f"  {away} @ {home} | tipoff: {tip}")
        print("-" * 60)


# ---------------- MAIN ----------------
def main():
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)

    start_date = (today - timedelta(days=6)).isoformat()  # last 7 days total
    end_date = today.isoformat()

    print(f"Yesterday : {yesterday.isoformat()}")
    print(f"Today     : {today.isoformat()}")

    games_last_7 = fetch_games(start_date, end_date)

    print_games_grouped_by_day(
        games_last_7,
        f"NBA API — Games from LAST 7 days ({start_date} → {end_date})"
    )


if __name__ == "__main__":
    main()
