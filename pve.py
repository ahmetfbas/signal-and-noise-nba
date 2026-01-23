from datetime import datetime, timedelta
from utils import (
    fetch_games_range,
    game_date,
    is_completed,
    team_in_game,
    margin_for_team
)

WINDOW_DAYS = 15


def team_pve_from_games(team_id, games, end_date, window_days):
    start_date = end_date - timedelta(days=window_days)

    margins = [
        margin_for_team(g, team_id)
        for g in games
        if is_completed(g)
        and team_in_game(g, team_id)
        and start_date <= game_date(g) < end_date
    ]

    if not margins:
        return 0, None

    avg_margin = round(sum(margins) / len(margins), 2)
    return len(margins), avg_margin


def pick_games_today(run_date):
    games = fetch_games_range(
        (run_date - timedelta(days=1)).isoformat(),
        (run_date + timedelta(days=1)).isoformat()
    )
    return [g for g in games if game_date(g) == run_date]


def main():
    run_date = datetime.utcnow().date()

    print("\n🏀 PvE — Performance vs Expectation")
    print(f"📅 Slate date: {run_date}")
    print(f"🗓 Window: last {WINDOW_DAYS} days\n")

    games_today = pick_games_today(run_date)
    if not games_today:
        print("No games found.")
        return

    lookback_games = fetch_games_range(
        (run_date - timedelta(days=WINDOW_DAYS)).isoformat(),
        run_date.isoformat()
    )

    for g in games_today:
        away = g["visitor_team"]
        home = g["home_team"]

        print(f"\n🎯 {away['full_name']} @ {home['full_name']}")

        for team in [away, home]:
            count, avg = team_pve_from_games(
                team["id"],
                lookback_games,
                run_date,
                WINDOW_DAYS
            )

            print(f"\n🧪 {team['full_name']}")
            print(f"  window_days = {WINDOW_DAYS}")
            print(f"  games_in_window = {count}")
            print(f"  avg_margin = {_
