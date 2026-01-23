# pve.py
import os
import time
import requests
from datetime import datetime, timedelta

API_URL = "https://api.balldontlie.io/v1/games"
API_KEY = os.getenv("BALLDONTLIE_API_KEY")

if not API_KEY:
    raise ValueError("BALLDONTLIE_API_KEY environment variable not set")

HEADERS = {"Authorization": API_KEY}


def _get(params, timeout=30):
    resp = requests.get(API_URL, headers=HEADERS, params=params, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"API error {resp.status_code}: {resp.text}")
    return resp.json()


def fetch_games_range(start_date, end_date):
    all_games = []
    page = 1
    while True:
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "per_page": 100,
            "page": page,
            "sort": "-date"
        }
        payload = _get(params)
        data = payload.get("data", [])
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


def is_completed(game):
    return game["home_team_score"] is not None and game["visitor_team_score"] is not None


def team_played(game, team_id):
    return game["home_team"]["id"] == team_id or game["visitor_team"]["id"] == team_id


def team_games_last_days(team_id, end_date, window_days):
    start_date = (end_date - timedelta(days=window_days - 1)).isoformat()
    end_date = end_date.isoformat()

    games = fetch_games_range(start_date, end_date)

    out = [
        g for g in games
        if is_completed(g) and team_played(g, team_id)
    ]

    out.sort(key=game_datetime)
    return out


def average_margin(team_id, games):
    if not games:
        return 0.0

    margins = []
    for g in games:
        is_home = g["home_team"]["id"] == team_id
        team_score = g["home_team_score"] if is_home else g["visitor_team_score"]
        opp_score = g["visitor_team_score"] if is_home else g["home_team_score"]
        margins.append(team_score - opp_score)

    return round(sum(margins) / len(margins), 2)


def pick_slate_games(run_date):
    games = fetch_games_range(
        (run_date - timedelta(days=1)).isoformat(),
        (run_date + timedelta(days=1)).isoformat()
    )

    by_date = {}
    for g in games:
        by_date.setdefault(game_date(g), []).append(g)

    if not by_date:
        return None, []

    slate_date = max(by_date.keys())
    return slate_date, by_date[slate_date]


def print_team_pve(team, slate_date, window_days):
    games = team_games_last_days(team["id"], slate_date, window_days)
    avg = average_margin(team["id"], games)

    print(f"\n🧪 {team['full_name']}")
    print(f"  window_days = {window_days}")
    print(f"  games_in_window = {len(games)}")
    print(f"  avg_margin = {avg}")


def main():
    RUN_DATE = datetime.utcnow().date()
    WINDOW_DAYS = 15

    slate_date, games = pick_slate_games(RUN_DATE)
    if not games:
        print("No games found.")
        return

    print("\n🏀 PvE — Performance vs Expectation")
    print(f"📅 Slate date: {slate_date}")
    print(f"🗓 Window: last {WINDOW_DAYS} days\n")

    for g in games:
        away = g["visitor_team"]
        home = g["home_team"]

        print(f"\n🎯 {away['full_name']} @ {home['full_name']}")
        print_team_pve(away, slate_date, WINDOW_DAYS)
        print_team_pve(home, slate_date, WINDOW_DAYS)


if __name__ == "__main__":
    main()
