import pandas as pd
from datetime import date, timedelta

from scripts.utils.utils import (
    game_date,
    is_completed,
    team_in_game,
    margin_for_team,
    expected_margin_breakdown
)
from analysis.fli import fatigue_components_for_team


def load_games_from_csv(path):
    df = pd.read_csv(path)
    df["game_date"] = pd.to_datetime(df["game_date"]).dt.strftime("%Y-%m-%dT00:00:00Z")

    games = []
    for r in df.to_dict("records"):
        games.append({
            "id": r["gameId"],
            "date": r["game_date"],
            "home_team": {
                "id": r["hometeamId"],
                "full_name": r["hometeamName"],
                "city": r["hometeamCity"]
            },
            "visitor_team": {
                "id": r["awayteamId"],
                "full_name": r["awayteamName"],
                "city": r["awayteamCity"]
            },
            "home_team_score": r["homeScore"],
            "visitor_team_score": r["awayScore"]
        })
    return games


def build_team_game_metrics(start_date, end_date, output_csv):
    all_games = load_games_from_csv(
        "data/archive/team_games_2020_plus.csv"
    )

    rows = []
    current = start_date

    while current <= end_date:
        games_today = [
            g for g in all_games
            if game_date(g) == current
        ]


        if not games_today:
            current += timedelta(days=1)
            continue

        recent_games = [
            g for g in all_games
            if current - timedelta(days=15) <= game_date(g) < current
        ]


        games_14 = [
            g for g in all_games
            if current - timedelta(days=14) <= game_date(g) < current
        ]


        for game in games_today:
            for side, ha in [("home_team", "H"), ("visitor_team", "A")]:
                team = game[side]
                opp = (
                    game["visitor_team"]
                    if side == "home_team"
                    else game["home_team"]
                )

                team_id = team["id"]

                actual = margin_for_team(game, team_id)

                fatigue = fatigue_components_for_team(
                    team_id,
                    current,
                    games_14,
                    games_today
                )

                breakdown = expected_margin_breakdown(
                    game,
                    team_id,
                    recent_games,
                    fatigue_index=fatigue["fatigue_index"]
                )

                expected = breakdown["expected_total"]
                pve = actual - expected

                rows.append({
                    "game_id": game["id"],
                    "game_date": current.isoformat(),
                    "team_id": team_id,
                    "team_name": team["full_name"],
                    "opponent_id": opp["id"],
                    "opponent_name": opp["full_name"],
                    "home_away": ha,
                    "actual_margin": round(actual, 2),
                    "result": "W" if actual > 0 else "L",
                    "expected_margin": round(expected, 2),
                    "pve": round(pve, 2),
                    "base_form_diff": breakdown["base_form_diff"],
                    "home_away_adj": breakdown["home_away"],
                    "fatigue_adj": breakdown["fatigue_adj"],
                    **fatigue
                })

        current += timedelta(days=1)

    df = pd.DataFrame(rows)
    df.to_csv(output_csv, index=False)
    return df


if __name__ == "__main__":
    df = build_team_game_metrics(
        start_date=date(2025, 10, 1),
        end_date=date(2026, 1, 23),
        output_csv="data/derived/team_game_metrics.csv"
    )

    print(f"Saved {len(df)} rows to data/derived/team_game_metrics.csv")
