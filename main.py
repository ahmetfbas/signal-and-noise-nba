import os
import requests
from datetime import datetime, timedelta
import math
import time

API_URL = "https://api.balldontlie.io/v1/games"
API_KEY = os.getenv("BALLDONTLIE_API_KEY")

if not API_KEY:
    raise ValueError("BALLDONTLIE_API_KEY environment variable not set")

HEADERS = {"Authorization": API_KEY}

def fetch_games(end_date: str):
    all_games = []
    page = 1

    while True:
        params = {
            "end_date": end_date,
            "per_page": 100,
            "page": page,
            "sort": "-date"
        }

        resp = requests.get(API_URL, headers=HEADERS, params=params, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"API error {resp.status_code}: {resp.text}")

        payload = resp.json()
        data = payload.get("data", [])
        if not data:
            break

        all_games.extend(data)

        if page >= payload.get("meta", {}).get("total_pages", 1):
            break

        page += 1
        time.sleep(0.2)

    return all_games

def game_datetime(game):
    return datetime.fromisoformat(game["date"].replace("Z", "+00:00"))

def game_date(game):
    return game_datetime(game).date()

def print_team_scores_last_30_days(team, run_date, window_days=30):
    team_id = team["id"]
    team_name = team["full_name"]
    cutoff_date = run_date - timedelta(days=window_days)

    games = fetch_games(run_date.isoformat())

    collected = []
    for g in games:
        gd = game_date(g)
        if gd < cutoff_date:
            break

        if (
            g.get("home_team_score") is not None
            and g.get("visitor_team_score") is not None
            and (g["home_team"]["id"] == team_id or g["visitor_team"]["id"] == team_id)
        ):
            collected.append(g)

    collected.sort(key=game_datetime)

    print(f"\n📌 {team_name} — completed games in last {window_days} days (ending {run_date})")

    if not collected:
        print("  (no games found)")
        return

    for g in collected:
        gd = game_date(g)
        is_home = g["home_team"]["id"] == team_id
        opponent = g["visitor_team"]["full_name"] if is_home else g["home_team"]["full_name"]
        team_score = g["home_team_score"] if is_home else g["visitor_team_score"]
        opp_score = g["visitor_team_score"] if is_home else g["home_team_score"]
        margin = team_score - opp_score
        loc = "HOME" if is_home else "AWAY"
        print(f"  {gd} | {loc} vs {opponent} | {team_score}-{opp_score} | margin: {margin:+}")

    print(f"  -> printed {len(collected)} games | last game date: {game_date(collected[-1])}")

def pick_one_game_today_and_print_histories(run_date):
    today_games = fetch_games(run_date.isoformat())
    today_games = [g for g in today_games if game_date(g) == run_date]

    if not today_games:
        print(f"\nNo games scheduled on {run_date}.")
        return

    g = today_games[0]
    away = g["visitor_team"]
    home = g["home_team"]

    print(f"\n🎯 Selected matchup on {run_date}: {away['full_name']} @ {home['full_name']}\n")

    print_team_scores_last_30_days(away, run_date, window_days=30)
    print_team_scores_last_30_days(home, run_date, window_days=30)

def main():
    RUN_DATE = datetime.utcnow().date()
    pick_one_game_today_and_print_histories(RUN_DATE)

if __name__ == "__main__":
    main()
