from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

from scripts.ingest.data_provider import fetch_games_range
from analysis.utils import game_date, is_completed

# --------------------------------------------------
# Project root
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]
FACTS_PATH = BASE_DIR / "data" / "core" / "team_game_facts.csv"

# --------------------------------------------------
# Official NBA team name mapping
# --------------------------------------------------
NAME_MAP = {
    "76ers": "Philadelphia 76ers",
    "Bucks": "Milwaukee Bucks",
    "Bulls": "Chicago Bulls",
    "Celtics": "Boston Celtics",
    "Clippers": "LA Clippers",
    "Grizzlies": "Memphis Grizzlies",
    "Hawks": "Atlanta Hawks",
    "Heat": "Miami Heat",
    "Hornets": "Charlotte Hornets",
    "Jazz": "Utah Jazz",
    "Kings": "Sacramento Kings",
    "Knicks": "New York Knicks",
    "Lakers": "Los Angeles Lakers",
    "Magic": "Orlando Magic",
    "Mavericks": "Dallas Mavericks",
    "Nets": "Brooklyn Nets",
    "Nuggets": "Denver Nuggets",
    "Pacers": "Indiana Pacers",
    "Pelicans": "New Orleans Pelicans",
    "Pistons": "Detroit Pistons",
    "Raptors": "Toronto Raptors",
    "Rockets": "Houston Rockets",
    "Spurs": "San Antonio Spurs",
    "Suns": "Phoenix Suns",
    "Thunder": "Oklahoma City Thunder",
    "Timberwolves": "Minnesota Timberwolves",
    "Trail Blazers": "Portland Trail Blazers",
    "Warriors": "Golden State Warriors",
    "Wizards": "Washington Wizards",
    "Cavaliers": "Cleveland Cavaliers",
}


def normalize_team_names(df: pd.DataFrame) -> pd.DataFrame:
    for col in ["team_name", "opponent_name"]:
        if col in df.columns:
            df[col] = df[col].map(NAME_MAP).fillna(df[col])
    return df


def main():
    TODAY_UTC = datetime.utcnow().date()

    # --------------------------------------------------
    # Rolling UTC backfill window (authoritative)
    # --------------------------------------------------
    BACKFILL_DAYS = 4
    start_date = TODAY_UTC - timedelta(days=BACKFILL_DAYS)
    end_date = TODAY_UTC

    # --------------------------------------------------
    # Load existing facts (if any)
    # --------------------------------------------------
    if FACTS_PATH.exists():
        existing = pd.read_csv(FACTS_PATH)
        existing["game_date"] = pd.to_datetime(
            existing["game_date"], errors="coerce"
        ).dt.date
    else:
        existing = None

    # --------------------------------------------------
    # Fetch games (API UTC → UTC calendar date)
    # --------------------------------------------------
    games = fetch_games_range(start_date.isoformat(), end_date.isoformat())
    games = [g for g in games if is_completed(g)]

    if not games:
        print("No completed games found.")
        return

    # --------------------------------------------------
    # Normalize to team-level rows (UTC calendar date)
    # --------------------------------------------------
    rows = []
    for g in games:
        gd = game_date(g)  # UTC calendar date
        home = g["home_team"]
        away = g["visitor_team"]

        rows.extend([
            {
                "game_id": g["id"],
                "game_date": gd,
                "team_id": home["id"],
                "team_name": home["full_name"],
                "opponent_id": away["id"],
                "opponent_name": away["full_name"],
                "home_away": "H",
                "team_points": g["home_team_score"],
                "opponent_points": g["visitor_team_score"],
            },
            {
                "game_id": g["id"],
                "game_date": gd,
                "team_id": away["id"],
                "team_name": away["full_name"],
                "opponent_id": home["id"],
                "opponent_name": home["full_name"],
                "home_away": "A",
                "team_points": g["visitor_team_score"],
                "opponent_points": g["home_team_score"],
            },
        ])

    new_df = pd.DataFrame(rows)
    new_df = normalize_team_names(new_df)
    new_df["game_date"] = pd.to_datetime(
        new_df["game_date"], errors="coerce"
    ).dt.date

    # --------------------------------------------------
    # Merge + dedupe (canonical key = game_id + team_id)
    # --------------------------------------------------
    if existing is not None:
        combined = pd.concat([existing, new_df], ignore_index=True)
    else:
        combined = new_df

    combined = combined.drop_duplicates(
        subset=["game_id", "team_id"], keep="last"
    )

    combined = combined.sort_values(
        ["game_date", "game_id"], ascending=[True, True]
    )

    # --------------------------------------------------
    # Season safety filter (UTC calendar)
    # --------------------------------------------------
    combined = combined[
        combined["game_date"] >= pd.to_datetime("2025-10-01").date()
    ]

    # --------------------------------------------------
    # Save (UTC calendar date, no timezone)
    # --------------------------------------------------
    FACTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(FACTS_PATH, index=False)

    print(
        f"✅ Ingested games from {start_date} → {end_date} "
        f"({len(new_df)} team-rows, UTC canonical)"
    )


if __name__ == "__main__":
    main()
