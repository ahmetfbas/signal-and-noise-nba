import os
import time
import requests
from datetime import datetime, timedelta

API_URL = "https://api.balldontlie.io/v1/games"
API_KEY = os.getenv("BALLDONTLIE_API_KEY")

if not API_KEY:
    raise ValueError("BALLDONTLIE_API_KEY environment variable not set")

HEADERS = {"Authorization": API_KEY}


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

        resp = requests.get(API_URL, headers=HEADERS, params=params, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"API error {resp.status_code}: {resp.text}")

        payload = resp.json()
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


def calc_margin(game, team_id):
    if game["home_team"]["id"] == team_id:
        return game["home_team_score"] - game["visitor_team_score"]
    return game["visitor_team_score"] - game["home_team_score"]


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


def build_team_margin_cache(slate_date, window_days):
    start = (slate_date - timedelta(days=window_days - 1)).isoformat()
    end = slate_date.isoformat()

    games = fetch_games_range(start, end)
    completed = [g for g in games if is_completed(g)]
    completed.sort(key=game_datetime)

    cache = {}
    for g in completed:
        for team in (g["home_team"], g["visitor_team"]):
            cache.setdefault(team["id"], []).append(g)

    return cache


def print_team_margins(team, slate_date, window_days, cache):
    games = cache.get(team["id"], [])

    print(f"\n📌 {team['full_name']} — margins (last {window_days} days)")

    if not games:
        print("  (no data)")
        return

    for g in games:
        margin = calc_margin(g, team["id"])
        print(f"  {game_date(g)} | margin: {margin:+}")

    print(f"  -> {len(games)} games | last: {game_date(games[-1])}")


def main():
    RUN_DATE = datetime.utcnow().date()
    WINDOW_DAYS = 15

    slate_date, games_today = pick_slate_games(RUN_DATE)
    if not games_today:
        print("No games scheduled.")
        return

    cache = build_team_margin_cache(slate_date, WINDOW_DAYS)

    print(f"\n🏀 Games on {slate_date}\n")

    for g in games_today:
        away = g["visitor_team"]
        home = g["home_team"]

        print(f"\n🎯 {away['full_name']} @ {home['full_name']}")

        print_team_margins(away, slate_date, WINDOW_DAYS, cache)
        print_team_margins(home, slate_date, WINDOW_DAYS, cache)


if __name__ == "__main__":
    main()
