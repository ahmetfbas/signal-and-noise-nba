import os
import requests
from datetime import datetime, timedelta

API_URL = "https://api.balldontlie.io/v1/games"
API_KEY = os.getenv("BALLDONTLIE_API_KEY")

HEADERS = {
    "Authorization": API_KEY
}

# ---------------- API ----------------
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

# ---------------- METRICS ----------------
def count_games(team_id, games):
    return sum(
        1 for g in games
        if g["home_team"]["id"] == team_id
        or g["visitor_team"]["id"] == team_id
    )

def schedule_density_score(g7, g14):
    d7 = g7 / 7
    d14 = g14 / 14
    d_raw = 0.6 * d7 + 0.4 * d14
    return round(100 * d_raw, 1)

# ---------------- MAIN ----------------
def main():
    # 👇 Explicit NBA slate date (change this freely)
    target_date = datetime.utcnow().date().isoformat()
    # Example override:
    # target_date = "2026-01-21"

    print(f"NBA Schedule Density — {target_date}\n")

    # Fetch slate games (authoritative)
    games_today = fetch_games(target_date, target_date)

    if not games_today:
        print("No NBA games on this date.")
        return

    # Fetch history for density
    start_7d = (datetime.fromisoformat(target_date) - timedelta(days=7)).date().isoformat()
    start_14d = (datetime.fromisoformat(target_date) - timedelta(days=14)).date().isoformat()

    games_7d = fetch_games(start_7d, target_date)
    games_14d = fetch_games(start_14d, target_date)

    for game in games_today:
        away = game["visitor_team"]
        home = game["home_team"]

        away_7d = count_games(away["id"], games_7d)
        away_14d = count_games(away["id"], games_14d)
        home_7d = count_games(home["id"], games_7d)
        home_14d = count_games(home["id"], games_14d)

        away_D = schedule_density_score(away_7d, away_14d)
        home_D = schedule_density_score(home_7d, home_14d)

        print(f"{away['full_name']} @ {home['full_name']}")
        print(f"  {away['full_name']}: D={away_D}")
        print(f"  {home['full_name']}: D={home_D}")
        print()

if __name__ == "__main__":
    main()
