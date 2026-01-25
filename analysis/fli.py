from datetime import datetime, timedelta
from datetime import date

from scripts.ingest.data_provider import fetch_games_range
from scripts.utils.utils import (
    game_date,
    is_completed,
    team_in_game,
    travel_miles
)

# --------------------------------------------------
# Density scoring
# --------------------------------------------------

def density_7d_score(g7):
    if g7 <= 2: return 10
    if g7 == 3: return 40
    if g7 == 4: return 75
    return 95


def density_14d_score(g14):
    if g14 <= 4: return 10
    if g14 == 5: return 35
    if g14 == 6: return 55
    if g14 == 7: return 75
    return 95


# --------------------------------------------------
# Recovery & travel
# --------------------------------------------------

def recovery_offset(days):
    if days == 1: return 0.00
    if days == 2: return 0.10
    if days == 3: return 0.25
    if days == 4: return 0.40
    return 0.55


def travel_load(miles):
    if miles is None: return 1
    if miles < 300: return 1
    if miles < 800: return 2
    return 3


# --------------------------------------------------
# Core fatigue calculation
# --------------------------------------------------

def fatigue_index(density, days_since, travel):
    b2b = 1 if days_since == 1 else 0

    raw = (
        density +
        (12 if b2b else 0) +
        travel * 6 +
        (10 if b2b and travel >= 2 else 0)
    )

    return round(raw * (1 - recovery_offset(days_since)), 1)


def fatigue_tier(score):
    if score < 30: return "Low"
    if score < 50: return "Elevated"
    if score < 70: return "High"
    return "Critical"


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def last_game_info(team_id, games, today):
    past = [
        g for g in games
        if is_completed(g)
        and team_in_game(g, team_id)
        and game_date(g) < today
    ]

    if not past:
        return None, None

    last = max(past, key=game_date)
    city = (
        last["home_team"]["city"]
        if last["home_team"]["id"] == team_id
        else last["visitor_team"]["city"]
    )

    return game_date(last), city


def count_games(team_id, games, start, end):
    return sum(
        1 for g in games
        if is_completed(g)
        and team_in_game(g, team_id)
        and start <= game_date(g) < end
    )


def pick_games_today(run_date):
    games = fetch_games_range(
        (run_date - timedelta(days=1)).isoformat(),
        (run_date + timedelta(days=1)).isoformat()
    )
    return [g for g in games if game_date(g) == run_date]


# --------------------------------------------------
# Public API
# --------------------------------------------------

def fatigue_index_for_team(team_id, run_date, games_14, games_today):
    g7_start = run_date - timedelta(days=7)
    g14_start = run_date - timedelta(days=14)

    g7 = count_games(team_id, games_14, g7_start, run_date)
    g14 = count_games(team_id, games_14, g14_start, run_date)

    density = round(
        0.65 * density_7d_score(g7) +
        0.35 * density_14d_score(g14),
        1
    )

    last_date, last_city = last_game_info(team_id, games_14, run_date)
    days_since = (run_date - last_date).days if last_date else 5

    game_today = next(
        (g for g in games_today if team_in_game(g, team_id)),
        None
    )

    travel = 1
    if game_today and last_city:
        miles = travel_miles(
            last_city,
            game_today["home_team"]["city"]
        )
        travel = travel_load(miles)

    return fatigue_index(density, days_since, travel)


# --------------------------------------------------
# CLI runner (debug / demo)
# --------------------------------------------------

def main():
    today = date(2026, 1, 23)

    g14_start = today - timedelta(days=14)

    games_14 = fetch_games_range(
        g14_start.isoformat(),
        today.isoformat()
    )
    games_today = pick_games_today(today)

    if not games_today:
        print("No games today.")
        return

    for g in games_today:
        away = g["visitor_team"]
        home = g["home_team"]

        print(f"\n{away['full_name']} @ {home['full_name']}\n")

        for team in [away, home]:
            tid = team["id"]
            fatigue = fatigue_index_for_team(
                tid, today, games_14, games_today
            )

            print(f"{team['full_name']}")
            print(f"  fatigue_index = {fatigue}")
            print(f"  tier = {fatigue_tier(fatigue)}\n")


if __name__ == "__main__":
    main()
