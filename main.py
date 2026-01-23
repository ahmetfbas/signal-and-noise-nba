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
        resp = _get(params)
        payload = resp.json()
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


def format_line(game, team_id):
    gd = game_date(game)
    is_home = game["home_team"]["id"] == team_id
    opponent = game["visitor_team"]["full_name"] if is_home else game["home_team"]["full_name"]
    team_score = game["home_team_score"] if is_home else game["visitor_team_score"]
    opp_score = game["visitor_team_score"] if is_home else game["home_team_score"]
    loc = "HOME" if is_home else "AWAY"
    margin = team_score - opp_score
    return f"  {gd} | {loc} vs {opponent} | {team_score}-{opp_score} | margin: {margin:+}"


def pick_slate_game(run_date):
    games = fetch_games_range(
        (run_date - timedelta(days=1)).isoformat(),
        (run_date + timedelta(days=1)).isoformat()
    )

    games_by_date = {}
    for g in games:
        games_by_date.setdefault(game_date(g), []).append(g)

    if not games_by_date:
        return None, None

    slate_date = max(games_by_date.keys())
    game = sorted(games_by_date[slate_date], key=game_datetime)[0]
    return slate_date, game


def team_games_last_days(team, end_date, window_days):
    start_date = (end_date - timedelta(days=window_days - 1)).isoformat()
    end_date = end_date.isoformat()

    games = fetch_games_range(start_date, end_date)

    out = [
        g for g in games
        if is_completed(g) and team_played(g, team["id"])
    ]

    out.sort(key=game_datetime)
    return out


def print_team_window(team, slate_date, window_days):
    games = team_games_last_days(team, slate_date, window_days)

    print(f"\n📌 {team['full_name']} — completed games in last {window_days} days (ending {slate_date})")

    if not games:
        print("  (no games found)")
        return

    for g in games:
        print(format_line(g, team["id"]))

    print(f"  -> printed {len(games)} games | last game date: {game_date(games[-1])}")


def main():
    RUN_DATE = datetime.utcnow().date()
    WINDOW_DAYS = 18

    slate_date, game = pick_slate_game(RUN_DATE)
    if not game:
        print("No slate found.")
        return

    away = game["visitor_team"]
    home = game["home_team"]

    print(f"\n🎯 Selected matchup on {slate_date}: {away['full_name']} @ {home['full_name']}\n")

    print_team_window(away, slate_date, WINDOW_DAYS)
    print_team_window(home, slate_date, WINDOW_DAYS)


if __name__ == "__main__":
    main()
