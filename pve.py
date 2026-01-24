from datetime import datetime, timedelta
from utils import (
    fetch_games_range,
    game_date,
    is_completed,
    team_in_game,
    margin_for_team,
    expected_margin_for_team
)


def pick_games_for_date(run_date):
    games = fetch_games_range(
        run_date.isoformat(),
        run_date.isoformat()
    )
    return [
        g for g in games
        if game_date(g) == run_date and is_completed(g)
    ]


def pve_for_game(game, run_date):
    results = []

    for side in ["home_team", "visitor_team"]:
        team = game[side]
        team_id = team["id"]
        team_name = team["full_name"]

        actual_margin = margin_for_team(game, team_id)
        expected_margin = expected_margin_for_team(game, team_id, run_date)
        pve = actual_margin - expected_margin

        results.append({
            "team_id": team_id,
            "team": team_name,
            "actual_margin": round(actual_margin, 2),
            "expected_margin": round(expected_margin, 2),
            "pve": round(pve, 2)
        })

    return results


def main():
    run_date = datetime.utcnow().date()

    recent_games = fetch_games_range(
        (run_date - timedelta(days=15)).isoformat(),
        run_date.isoformat()
    )

    games_today = pick_games_for_date(run_date)

    print("\n🏀 PvE — Performance vs Expectation")
    print(f"📅 Date: {run_date}")
    print("-" * 50)

    for game in games_today:
        matchup = f"{game['visitor_team']['abbreviation']} @ {game['home_team']['abbreviation']}"
        print(f"\n{matchup}")

        rows = []
        for side in ["home_team", "visitor_team"]:
            team_id = game[side]["id"]
            team_name = game[side]["full_name"]

            actual = margin_for_team(game, team_id)
            expected = expected_margin_for_team(game, team_id, recent_games)
            pve = actual - expected

            rows.append((team_name, actual, expected, pve))

        for r in rows:
            print(
                f"{r[0]:25s} | "
                f"Actual: {r[1]:>6.1f} | "
                f"Expected: {r[2]:>6.1f} | "
                f"PvE: {r[3]:>6.1f}"
            )


if __name__ == "__main__":
    main()
