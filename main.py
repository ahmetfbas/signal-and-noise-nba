import os
import requests
from datetime import datetime

API_URL = "https://api.balldontlie.io/v1/games"
API_KEY = os.getenv("BALLDONTLIE_API_KEY")

if not API_KEY:
    raise ValueError("BALLDONTLIE_API_KEY environment variable not set")

HEADERS = {"Authorization": API_KEY}


def fetch_games_for_date(date_str):
    all_games = []
    page = 1

    while True:
        params = {
            "start_date": date_str,
            "end_date": date_str,
            "per_page": 100,
            "page": page
        }

        resp = requests.get(API_URL, headers=HEADERS, params=params, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(resp.text)

        payload = resp.json()
        all_games.extend(payload.get("data", []))

        if page >= payload.get("meta", {}).get("total_pages", 1):
            break

        page += 1

    return all_games


def main():
    target_date = "2026-01-22"   # 👈 change if needed
    games = fetch_games_for_date(target_date)

    print(f"\n🏀 NBA Games on {target_date}\n")

    if not games:
        print("No games found.")
        return

    for g in games:
        home = g["home_team"]["full_name"]
        away = g["visitor_team"]["full_name"]

        home_score = g["home_team_score"]
        away_score = g["visitor_team_score"]

        if home_score is None or away_score is None:
            print(f"{away} @ {home} — not completed yet")
        else:
            print(f"{away} {away_score} @ {home} {home_score}")


if __name__ == "__main__":
    main()
