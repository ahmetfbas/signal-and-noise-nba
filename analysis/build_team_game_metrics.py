# analysis/build_team_game_metrics.py

import pandas as pd
from datetime import date, timedelta
from typing import Optional

from analysis.fli import fatigue_components_from_row
from analysis.utils import travel_miles


# --------------------------------------------------
# Load team-level game facts
# --------------------------------------------------

def load_team_games(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    df["game_date"] = pd.to_datetime(
        df["game_date"],
        utc=True,
        errors="coerce",
        format="mixed"
    ).dt.date

    return df


# --------------------------------------------------
# Core builder
# --------------------------------------------------

def build_team_game_metrics(
    games: pd.DataFrame,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> pd.DataFrame:

    if start_date is None:
        start_date = games["game_date"].min()
    if end_date is None:
        end_date = games["game_date"].max()

    rows = []
    current = start_date

    while current <= end_date:
        games_today = games[games["game_date"] == current]

        if games_today.empty:
            current += timedelta(days=1)
            continue

        recent_14 = games[
            (games["game_date"] < current) &
            (games["game_date"] >= current - timedelta(days=14))
        ]

        recent_7 = games[
            (games["game_date"] < current) &
            (games["game_date"] >= current - timedelta(days=7))
        ]

        for _, g in games_today.iterrows():

            team_id = g["team_id"]
            team_name = g["team_name"]
            opp_id = g["opponent_id"]
            opp_name = g["opponent_name"]

            actual_margin = g["team_points"] - g["opponent_points"]

            # -----------------------------
            # Recent game counts
            # -----------------------------
            games_last_7 = (recent_7["team_id"] == team_id).sum()
            games_last_14 = (recent_14["team_id"] == team_id).sum()

            # -----------------------------
            # Previous game (for travel)
            # -----------------------------
            last_game = games[
                (games["team_id"] == team_id) &
                (games["game_date"] < current)
            ].sort_values("game_date", ascending=False).head(1)

            if not last_game.empty:
                prev = last_game.iloc[0]
                days_since_last_game = (current - prev["game_date"]).days
                previous_city = prev.get("current_city", None)
            else:
                days_since_last_game = 5
                previous_city = None

            # -----------------------------
            # Current city (home team city heuristic)
            # -----------------------------
            if g["home_away"] == "H":
                current_city = team_name.split()[-1]
            else:
                current_city = g["opponent_name"].split()[-1]

            travel = (
                travel_miles(previous_city, current_city)
                if previous_city and current_city
                else None
            )

            fatigue = fatigue_components_from_row(
                games_last_7=games_last_7,
                games_last_14=games_last_14,
                days_since_last_game=days_since_last_game,
                travel_miles=travel,
            )

            rows.append({
                "game_id": g["game_id"],
                "game_date": current,
                "team_id": team_id,
                "team_name": team_name,
                "opponent_id": opp_id,
                "opponent_name": opp_name,
                "home_away": g["home_away"],
                "actual_margin": actual_margin,
                "current_city": current_city,
                "previous_city": previous_city,
                **fatigue,
            })

        current += timedelta(days=1)

    return pd.DataFrame(rows)


# --------------------------------------------------
# Entrypoint
# --------------------------------------------------

def main():
    games = load_team_games("data/core/team_game_facts.csv")
    df = build_team_game_metrics(games)
    df.to_csv("data/derived/team_game_metrics.csv", index=False)
    print(f"Wrote {len(df)} rows to team_game_metrics.csv")


if __name__ == "__main__":
    main()
