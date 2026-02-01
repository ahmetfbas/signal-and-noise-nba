import pandas as pd
from datetime import date, timedelta
from typing import Optional

from analysis.fli import fatigue_components_from_row
from analysis.utils import travel_miles


# --------------------------------------------------
# Team → City mapping (NBA-complete)
# --------------------------------------------------

def extract_city(team_name: str) -> str:
    CITY_MAP = {
        "Atlanta Hawks": "Atlanta",
        "Boston Celtics": "Boston",
        "Brooklyn Nets": "Brooklyn",
        "Charlotte Hornets": "Charlotte",
        "Chicago Bulls": "Chicago",
        "Cleveland Cavaliers": "Cleveland",
        "Dallas Mavericks": "Dallas",
        "Denver Nuggets": "Denver",
        "Detroit Pistons": "Detroit",
        "Golden State Warriors": "San Francisco",
        "Houston Rockets": "Houston",
        "Indiana Pacers": "Indianapolis",
        "LA Clippers": "Los Angeles",
        "Los Angeles Lakers": "Los Angeles",
        "Memphis Grizzlies": "Memphis",
        "Miami Heat": "Miami",
        "Milwaukee Bucks": "Milwaukee",
        "Minnesota Timberwolves": "Minneapolis",
        "New Orleans Pelicans": "New Orleans",
        "New York Knicks": "New York",
        "Oklahoma City Thunder": "Oklahoma City",
        "Orlando Magic": "Orlando",
        "Philadelphia 76ers": "Philadelphia",
        "Phoenix Suns": "Phoenix",
        "Portland Trail Blazers": "Portland",
        "Sacramento Kings": "Sacramento",
        "San Antonio Spurs": "San Antonio",
        "Toronto Raptors": "Toronto",
        "Utah Jazz": "Salt Lake City",
        "Washington Wizards": "Washington",
    }

    return CITY_MAP[team_name]


# --------------------------------------------------
# Load team-level game facts
# --------------------------------------------------

def load_team_games(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["game_date"] = pd.to_datetime(
        df["game_date"], utc=True, errors="coerce", format="mixed"
    ).dt.date
    return df


# --------------------------------------------------
# Core builder (FIXED)
# --------------------------------------------------

def build_team_game_metrics(
    games: pd.DataFrame,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> pd.DataFrame:

    if games.empty:
        raise RuntimeError("No team game facts provided.")

    if start_date is None:
        start_date = games["game_date"].min()
    if end_date is None:
        end_date = games["game_date"].max()

    rows = []
    current = start_date

    # ✅ Per-team rolling state
    last_city_by_team = {}
    last_game_date_by_team = {}

    while current <= end_date:
        games_today = games[games["game_date"] == current]

        if games_today.empty:
            current += timedelta(days=1)
            continue

        recent_14 = games[
            (games["game_date"] < current)
            & (games["game_date"] >= current - timedelta(days=14))
        ]

        recent_7 = games[
            (games["game_date"] < current)
            & (games["game_date"] >= current - timedelta(days=7))
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
            # Days since last game
            # -----------------------------
            if team_id in last_game_date_by_team:
                days_since_last_game = (current - last_game_date_by_team[team_id]).days
            else:
                days_since_last_game = 5  # season opener fallback

            # -----------------------------
            # City continuity (FIX)
            # -----------------------------
            previous_city = last_city_by_team.get(team_id)

            if g["home_away"] == "H":
                current_city = extract_city(team_name)
            else:
                current_city = extract_city(opp_name)

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

            # ✅ update rolling state
            last_city_by_team[team_id] = current_city
            last_game_date_by_team[team_id] = current

        current += timedelta(days=1)

    df = pd.DataFrame(rows)

    if df.empty:
        raise RuntimeError("team_game_metrics produced no rows.")

    return df


# --------------------------------------------------
# Entrypoint
# --------------------------------------------------

def main():
    games = load_team_games("data/core/team_game_facts.csv")
    df = build_team_game_metrics(games)
    df.to_csv("data/derived/team_game_metrics.csv", index=False)
    print(f"✅ Wrote {len(df)} rows → team_game_metrics.csv")


if __name__ == "__main__":
    main()
