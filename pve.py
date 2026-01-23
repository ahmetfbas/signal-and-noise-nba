# pve.py

from datetime import datetime, timedelta
from utils import (
    fetch_games_range,
    game_date,
    is_completed,
    team_in_game,
    margin_for_team
)

WINDOW_DAYS = 15


def pick_games_today(all_games, run_date):
    return [g for g in all_games if game_date(g) == run_date]


def team_margins_last_days(team_id, all_games, end_date, window_days):
    start_date = end_date - timedelta(days=window_days)

    margins = [
        margin_for_team(g, team_id)
        for g in all_games
        if is_completed(g)
        and team_in_game(g, team_id)
        and start_date <= game_date(g) < end_date
    ]

    return margins


def main():
    run_date = datetime.utcnow().date()

    all_games = fetch_games_range(
        (run_date - timedelta(days=WINDOW_DAYS)).isoformat(),
        run_date.isoformat()
    )

    games_today = pick_games_today(all_games, run_date)

    print("\n🏀 PvE — Performance vs Expectation")
    print(f"📅 Slate date: {run_date}")
    print(f"🗓 Window: last {WINDOW_DAYS} days\n")

    if not games_today:
        print("No games today.")
        return

    for g in games_today:
        away = g["visitor_team"]
        home = g["home_team"]

        print(f"\n🎯 {away['full_name']} @ {home['full_name']}\n")

        for team in [away, home]:
            tid = team["id"]

            margins = team_margins_last_days(
                tid,
                all_games,
                run_date,
                WINDOW_DAYS
            )

            games_count = len(margins)
            avg_margin = round(sum(margins) / games_count, 2) if games_count else 0.0

            print(f"🧪 {team['full_name']}")
            print(f"  window_days = {WINDOW_DAYS}")
            print(f"  games_in_window = {games_count}")
            print(f"  avg_margin = {avg_margin}\n")


if __name__ == "__main__":
    main()
