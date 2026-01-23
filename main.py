import os
import time
import requests
from datetime import datetime, timedelta
import math

API_URL = "https://api.balldontlie.io/v1/games"
API_KEY = os.getenv("BALLDONTLIE_API_KEY")

if not API_KEY:
    raise ValueError("BALLDONTLIE_API_KEY environment variable not set")

HEADERS = {"Authorization": API_KEY}

WINDOW_DAYS = 15
MAX_FATIGUE_PENALTY = 6.0


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


def build_completed_games_cache(slate_date):
    start = (slate_date - timedelta(days=WINDOW_DAYS - 1)).isoformat()
    end = slate_date.isoformat()
    games = fetch_games_range(start, end)
    completed = [g for g in games if is_completed(g)]
    completed.sort(key=game_datetime)
    return completed


def build_team_game_cache(completed_games):
    cache = {}
    for g in completed_games:
        for t in (g["home_team"], g["visitor_team"]):
            cache.setdefault(t["id"], []).append(g)
    return cache


def avg_margin(team_id, games):
    if not games:
        return 0.0
    margins = [calc_margin(g, team_id) for g in games]
    return sum(margins) / len(margins)


def avg_opponent_strength(team_id, games, team_cache):
    vals = []
    for g in games:
        opp = g["visitor_team"]["id"] if g["home_team"]["id"] == team_id else g["home_team"]["id"]
        opp_games = team_cache.get(opp, [])
        vals.append(avg_margin(opp, opp_games))
    return sum(vals) / len(vals) if vals else 0.0


def home_away_adjustment(team_id, games):
    adj = 0
    for g in games:
        adj += 2 if g["home_team"]["id"] == team_id else -2
    return adj / len(games) if games else 0.0


def back_to_back_pressure(days_since):
    return 1 if days_since == 1 else 0


def recovery_offset(days):
    if days <= 1: return 0.00
    if days == 2: return 0.10
    if days == 3: return 0.25
    if days == 4: return 0.40
    return 0.55


def fatigue_load_index(density, days_since, travel):
    if days_since is None:
        days_since = 5
    b2b = back_to_back_pressure(days_since)
    raw = density + (12 if b2b else 0) + travel * 6 + (10 if b2b and travel >= 2 else 0)
    return raw * (1 - recovery_offset(days_since))


def fatigue_penalty(fli):
    return (fli / 100) * MAX_FATIGUE_PENALTY


def calculate_pve(team, team_games, team_cache, fatigue_score):
    raw_perf = avg_margin(team["id"], team_games)
    opp_strength = avg_opponent_strength(team["id"], team_games, team_cache)
    ha_adj = home_away_adjustment(team["id"], team_games)
    fat_pen = fatigue_penalty(fatigue_score)

    expected = opp_strength + ha_adj + fat_pen
    pve = raw_perf - expected

    return {
        "raw_margin": raw_perf,
        "avg_opp_strength": opp_strength,
        "home_away_adj": ha_adj,
        "fatigue_score": fatigue_score,
        "fatigue_penalty": fat_pen,
        "expected_context": expected,
        "pve": pve
    }


def main():
    RUN_DATE = datetime.utcnow().date()
    slate_date, games_today = pick_slate_games(RUN_DATE)
    if not games_today:
        print("No games.")
        return

    completed = build_completed_games_cache(slate_date)
    team_cache = build_team_game_cache(completed)

    print(f"\n🏀 PvE Debug — {slate_date}\n")

    for g in games_today:
        for team in (g["visitor_team"], g["home_team"]):
            team_games = team_cache.get(team["id"], [])

            density = len(team_games) * 10
            days_since = 2
            travel = 1
            fli = fatigue_load_index(density, days_since, travel)

            result = calculate_pve(team, team_games, team_cache, fli)

            print(f"\n📌 {team['full_name']}")
            print(f"Margins: {[calc_margin(x, team['id']) for x in team_games]}")
            print(f"Games played: {len(team_games)}")
            print(f"Avg margin: {result['raw_margin']:.2f}")
            print(f"Avg opponent strength: {result['avg_opp_strength']:.2f}")
            print(f"Home/Away adj: {result['home_away_adj']:.2f}")
            print(f"Fatigue load index: {result['fatigue_score']:.1f}")
            print(f"Fatigue penalty: {result['fatigue_penalty']:.2f}")
            print(f"Expected context: {result['expected_context']:.2f}")
            print(f"PvE: {result['pve']:.2f}")


if __name__ == "__main__":
    main()
