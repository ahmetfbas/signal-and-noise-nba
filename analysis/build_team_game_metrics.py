import pandas as pd
from datetime import date, timedelta
from typing import Optional

from analysis.fli import fatigue_components_from_row
from analysis.pve import expected_margin_breakdown_from_rows


# --------------------------------------------------
# Load helpers
# --------------------------------------------------

def load_team_games(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["game_date"] = pd.to_datetime(df["game_date"]).dt.date
    return df


# --------------------------------------------------
# Core builder
# --------------------------------------------------

def build_team_game_metrics(
    games: pd.DataFrame,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> pd.DataFrame:
    """
    Build per-team, per-game metrics including fatigue and PvE.

    Assumes input games are at game-level (home/away in same row).
    Returns one row per team per game.
    """

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

        recent_15 = games[
            (games["game_date"] < current)
            & (games["game_date"] >= current - timedelta(days=15))
        ]

        recent_14 = games[
            (games["game_date"] < current)
            & (games["game_date"] >= current - timedelta(days=14))
        ]

        recent_7 = games[
            (games["game_date"] < current)
            & (games["game_date"] >= current - timedelta(days=7))
        ]

        for _, g in games_today.iterrows():
            for is_home in (True, False):
                team_id = g["hometeamId"] if is_home else g["awayteamId"]
                team_name = g["hometeamName"] if is_home else g["awayteamName"]

                opp_id = g["awayteamId"] if is_home else g["hometeamId"]
                opp_name = g["awayteamName"] if is_home else g["hometeamName"]

                team_score = g["homeScore"] if is_home else g["awayScore"]
                opp_score = g["awayScore"] if is_home else g["homeScore"]

                actual_margin = team_score - opp_score

                # ----------------------------
                # Rolling counts
                # ----------------------------
                games_last_7 = (
                    (recent_7["hometeamId"] == team_id)
                    | (recent_7["awayteamId"] == team_id)
                ).sum()

                games_last_14 = (
                    (recent_14["hometeamId"] == team_id)
                    | (recent_14["awayteamId"] == team_id)
                ).sum()

                last_game = games[
                    ((games["hometeamId"] == team_id)
                     | (games["awayteamId"] == team_id))
                    & (games["game_date"] < current)
                ].sort_values("game_date", ascending=False).head(1)

                days_since_last_game = (
                    (current - last_game.iloc[0]["game_date"]).days
                    if not last_game.empty
                    else 5
                )

                # Travel intentionally neutral for now
                travel_miles = None

                fatigue = fatigue_components_from_row(
                    games_last_7=games_last_7,
                    games_last_14=games_last_14,
                    days_since_last_game=days_since_last_game,
                    travel_miles=travel_miles,
                )

                breakdown = expected_margin_breakdown_from_rows(
                    team_id=team_id,
                    opponent_id=opp_id,
                    is_home=is_home,
                    recent_games=recent_15,
                    fatigue_index=fatigue["fatigue_index"],
                )

                expected = breakdown["expected_total"]

                rows.append({
                    "game_id": g["gameId"],
                    "game_date": current,
                    "team_id": team_id,
                    "team_name": team_name,
                    "opponent_id": opp_id,
                    "opponent_name": opp_name,
                    "home_away": "H" if is_home else "A",
                    "actual_margin": round(actual_margin, 2),
                    "result": "W" if actual_margin > 0 else "L",
                    "expected_margin": round(expected, 2),
                    "pve": round(actual_margin - expected, 2),
                    **breakdown,
                    **fatigue,
                })

        current += timedelta(days=1)

    return pd.DataFrame(rows)
