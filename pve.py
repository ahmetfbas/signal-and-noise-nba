from datetime import datetime
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
    games = pick_games_for_date(run_date)

    print("\n🏀 PvE — Performance vs Expectation")
    print(f"📅 Date: {run_date}")
    print("-" * 50)

    for game in games:
        matchup = f"{game['visitor_team']['abbreviation']} @ {game['home_team']['abbreviation']}"
        print(f"\n{matchup}")

        rows = pve_for_game(game, run_date)
        for r in rows:
            print(
                f"{r['team']:25s} | "
                f"Actual: {r['actual_margin']:>6} | "
                f"Expected: {r['expected_margin']:>6} | "
                f"PvE: {r['pve']:>6}"
            )


if __name__ == "__main__":
    main()
