import os
import time
import requests
from datetime import datetime, timedelta

API_URL = "https://api.balldontlie.io/v1/games"
API_KEY = os.getenv("BALLDONTLIE_API_KEY")

if not API_KEY:
    raise ValueError("BALLDONTLIE_API_KEY environment variable not set")

HEADERS = {"Authorization": API_KEY}


def _get_with_retry(params, timeout=30, max_retries=6):
    backoff = 1.0
    for attempt in range(max_retries):
        resp = requests.get(API_URL, headers=HEADERS, params=params, timeout=timeout)
        if resp.status_code == 200:
            return resp
        if resp.status_code in (429, 500, 502, 503, 504):
            time.sleep(backoff)
            backoff = min(backoff * 2, 16)
            continue
        raise RuntimeError(f"API error {resp.status_code}: {resp.text}")
    raise RuntimeError(f"API error {resp.status_code}: {resp.text}")


def fetch_games_range(start_date: str, end_date: str):
    all_games = []
    page = 1
    while True:
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "per_page": 100,
            "page": page,
            "sort": "-date",
        }
        resp = _get_with_retry(params)
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
    return game.get("home_team_score") is not None and game.get("visitor_team_score") is not None


def team_played(game, team_id: int) -> bool:
    return game["home_team"]["id"] == team_id or game["visitor_team"]["id"] == team_id


def format_line(game, team_id: int) -> str:
    gd = game_date(game)
    is_home = game["home_team"]["id"] == team_id
    opponent = game["visitor_team"]["full_name"] if is_home else game["home_team"]["full_name"]
    team_score = game["home_team_score"] if is_home else game["visitor_team_score"]
    opp_score = game["visitor_team_score"] if is_home else game["home_team_score"]
    loc = "HOME" if is_home else "AWAY"
    margin = team_score - opp_score
    return f"  {gd} | {loc} vs {opponent} | {team_score}-{opp_score} | margin: {margin:+}"


def pick_slate_game(run_date):
    start = (run_date - timedelta(days=1)).isoformat()
    end = (run_date + timedelta(days=1)).isoformat()
    games = fetch_games_range(start, end)

    by_day = {}
    for g in games:
        d = game_date(g)
        by_day.setdefault(d, []).append(g)

    slate_days = sorted([d for d, gs in by_day.items() if gs], reverse=True)
    if not slate_days:
        return None, None

    slate_date = slate_days[0]
    slate_games = sorted(by_day[slate_date], key=game_datetime)

    return slate_date, slate_games[0]


def team_last_30_days_games(team, slate_date, window_days=30):
    start = (slate_date - timedelta(days=window_days - 1)).isoformat()
    end = slate_date.isoformat()
    games = fetch_games_range(start, end)

    out = []
    for g in games:
        if is_completed(g) and team_played(g, team["id"]):
            out.append(g)

    out.sort(key=game_datetime)
    return out


def print_team_window(team, slate_date, window_days=30):
    games = team_last_30_days_games(team, slate_date, window_days=window_days)

    print(f"\n📌 {team['full_name']} — completed games in last {window_days} days (ending {slate_date})")
    if not games:
        print("  (no games found)")
        return

    for g in games:
        print(format_line(g, team["id"]))

    print(f"  -> printed {len(games)} games | last game date: {game_date(games[-1])}")


def main():
    RUN_DATE = datetime.utcnow().date()

    slate_date, game = pick_slate_game(RUN_DATE)
    if game is None:
        print(f"\nNo slate found near {RUN_DATE}.")
        return

    away = game["visitor_team"]
    home = game["home_team"]

    print(f"\n🎯 Selected matchup on {slate_date}: {away['full_name']} @ {home['full_name']}\n")

    print_team_window(away, slate_date, window_days=30)
    print_team_window(home, slate_date, window_days=30)


if __name__ == "__main__":
    main()
