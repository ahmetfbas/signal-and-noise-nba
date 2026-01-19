import os
import requests
from datetime import datetime, timedelta

API_URL = "https://api.balldontlie.io/v1/games"
API_KEY = os.getenv("BALLDONTLIE_API_KEY")

HEADERS = {
    "Authorization": API_KEY
}

def fetch_games(start_date, end_date):
    params = {
        "start_date": start_date,
        "end_date": end_date,
        "per_page": 100
    }

    response = requests.get(API_URL, headers=HEADERS, params=params)

    if response.status_code != 200:
        print("API error:", response.status_code)
        print(response.text)
        return []

    return response.json()["data"]

def count_games(team_id, games):
    return sum(
        1 for g in games
        if g["home_team"]["id"] == team_id or g["visitor_team"]["id"] == team_id
    )

def list_games_for_team(team_id, games):
    return sorted(
        [
            g["date"][:10]
            for g in games
            if g["home_team"]["id"] == team_id or g["visitor_team"]["id"] == team_id
        ]
    )

def main():
    today = datetime.utcnow().date()
    today_str = today.isoformat()

    games_today = fetch_games(today_str, today_str)

    if not games_today:
        print("No NBA games today.")
        return

    games_7d = fetch_games((today - timedelta(days=7)).isoformat(), today_str)
    games_14d = fetch_games((today - timedelta(days=14)).isoformat(), today_str)

    print("Schedule Density (raw counts)\n")

    for game in games_today:
        home = game["home_team"]
        away = game["visitor_team"]

        print(f"{away['full_name']} @ {home['full_name']}")

        away_7d = count_games(away["id"], games_7d)
        away_14d = count_games(away["id"], games_14d)

        home_7d = count_games(home["id"], games_7d)
        home_14d = count_games(home["id"], games_14d)

        print(f"  {away['full_name']}: 7d={away_7d}, 14d={away_14d}")
        print(f"  {home['full_name']}: 7d={home_7d}, 14d={home_14d}")

        # DEBUG: validate Milwaukee Bucks counts
        if away["full_name"] == "Milwaukee Bucks" or home["full_name"] == "Milwaukee Bucks":
            bucks_id = away["id"] if away["full_name"] == "Milwaukee Bucks" else home["id"]

            print("  [DEBUG] Bucks games last 7 days:")
            for d in list_games_for_team(bucks_id, games_7d):
                print(f"    - {d}")

            print("  [DEBUG] Bucks games last 14 days:")
            for d in list_games_for_team(bucks_id, games_14d):
                print(f"    - {d}")

        print()

if __name__ == "__main__":
    main()
