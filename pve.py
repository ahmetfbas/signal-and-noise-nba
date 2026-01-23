from datetime import datetime, timedelta
from utils import (
    fetch_games_range,
    game_date,
    is_completed,
    team_in_game,
    margin_for_team
)

WINDOW_DAYS = 15

def team_margins_last_days(team_id, end_date, window_days):
    start_date = end_date - timedelta(days=window_days - 1)
    games = fetch_games_range(start_date.isoformat(), end_date.isoformat())

    margins = [
        margin_for_team(g, team_id)
        for g in games
        if is_completed(g)
        and team_in_game(g, team_id)
        and start_date <= game_date(g) <= end_date
    ]

    return margins

def average_margin(margins):
    if not margins:
        return 0.0
    return round(sum(margins) / len(margins), 2)

def pick_games_today(run_date):
    games = fetch_games_range(
        (run_date - timedelta(days=1)).isoformat(),
        (run_date + timedelta(days=1)).isoformat()
    )
    return [g for g in games if game_date(g) == run_date]

def main():
    run_date = datetime.utcnow().date()
    games_today = pick_games_today(run_date)

    if not games_today:
        print(f"No games on {run_date}")
        return

    print("\n🏀 PvE — Performance vs Expectation")
    print(f"📅 Slate date: {run_date}")
    print(f"🗓 Window: last {WINDOW_DAYS} days\n")

    processed = set()

    for g in games_today:
        away = g["visitor_team"]
        home = g["home_team"]

        print(f"\n🎯 {away['full_name']} @ {home['full_name']}")

        for team in [away, home]:
            tid = team["id"]
            if tid in processed:
                continue
            processed.add(tid)

            margins = team_margins_last_days(tid, run_date, WINDOW_DAYS)
            avg = average_margin(margins)

            print(f"\n🧪 {team['full_name']}")
            print(f"  window_days = {WINDOW_DAYS}")
            print(f"  games_in_window = {len(margins)}")
            print(f"  avg_margin = {avg}")

if __name__ == "__main__":
    main()
