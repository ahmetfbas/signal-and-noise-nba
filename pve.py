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
    return resp


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
        payload = _get(params).json()
        data = payload.get("data", [])
        all_games.extend(data)

        if page >= payload.get("meta", {}).get("total_pages", 1):
            break

        page += 1
        time.sleep(0.15)

    return all_games


def game_datetime(game):
    return datetime.fromisoformat(game["date"].replace("Z", "+00:00"))


def game_date(game):
    return game_datetime(game).date()


def is_completed(game):
    return game["home_team_score"] is not None and game["visitor_team_score"] is not None


def team_played(game, team_id):
    return game["home_team"]["id"] == team_id or game["visitor_team"]["id"] == team_id


def team_margin(game, team_id):
    if game["home_team"]["id"] == team_id:
        return game["home_team_score"] - game["visitor_team_score"]
    return game["visitor_team_score"] - game["home_team_score"]


def pick_slate_games(run_date):
    games = fetch_games_range(
        (run_date - timedelta(days=1)).isoformat(),
        (run_date + timedelta(days=1)).isoformat()
    )

    games_by_date = {}
    for g in games:
        games_by_date.setdefault(game_date(g), []).append(g)

    if not games_by_date:
        return None, []

    slate_date = max(games_by_date.keys())
    slate_games = sorted(games_by_date[slate_date], key=game_datetime)
    return slate_date, slate_games


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


def print_team_pve(team, slate_date, window_days):
    games = team_games_last_days(team["id"], slate_date, window_days)

    print(f"\n🧪 {team['full_name']}")
    print(f"  window_days = {window_days}")
    print(f"  games_in_window = {len(games)}")

    if not games:
        print("  (no completed games)")
        return

    margins = []
    for g in games:
        margin = team_margin(g, team["id"])
        margins.append(margin)

        opp = (
            g["visitor_team"]["full_name"]
            if g["home_team"]["id"] == team["id"]
            else g["home_team"]["full_name"]
        )

        print(
            f"  {game_date(g)} vs {opp} | "
            f"{g['home_team_score']}-{g['visitor_team_score']} | "
            f"margin: {margin:+}"
        )

    avg_margin = round(sum(margins) / len(margins), 2)
    print(f"  avg_margin = {avg_margin}")
    print(f"  last_game_date = {game_date(games[-1])}")


def main():
    RUN_DATE = datetime.utcnow().date()
    WINDOW_DAYS = 15

    slate_date, slate_games = pick_slate_games(RUN_DATE)
    if not slate_games:
        print("No slate found.")
        return

    print(f"\n🏀 PvE — Performance vs Expectation")
    print(f"📅 Slate date: {slate_date}")
    print(f"🗓 Window: last {WINDOW_DAYS} days\n")

    for g in slate_games:
        away = g["visitor_team"]
        home = g["home_team"]

        print(f"\n🎯 {away['full_name']} @ {home['full_name']}")

        print_team_pve(away, slate_date, WINDOW_DAYS)
        print_team_pve(home, slate_date, WINDOW_DAYS)


if __name__ == "__main__":
    main()
