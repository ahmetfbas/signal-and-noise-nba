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


def main():
    # --------------------------------------------------
    # Determine date range to fetch
    # --------------------------------------------------
    TODAY = datetime.utcnow().date()

    if FACTS_PATH.exists():
        existing = pd.read_csv(FACTS_PATH)
        existing["game_date"] = pd.to_datetime(
            existing["game_date"],
            utc=True,
            errors="coerce",
            format="mixed"
        )
        last_date = (existing["game_date"].dt.tz_convert(None).dt.date.max())

        start_date = last_date + timedelta(days=1)
    else:
        existing = None
        start_date = TODAY - timedelta(days=2)  # first run safety

    end_date = TODAY - timedelta(days=1)

    if start_date > end_date:
        print("No new dates to fetch.")
        return

    # --------------------------------------------------
    # Fetch games
    # --------------------------------------------------
    games = fetch_games_range(
        start_date.isoformat(),
        end_date.isoformat()
    )

    games = [
        g for g in games
        if is_completed(g)
    ]

    if not games:
        print("No completed games found.")
        return

    # --------------------------------------------------
    # Normalize to team-level rows
    # --------------------------------------------------
    rows = []

    for g in games:
        gd = game_date(g)
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
            }
        ])

    new_df = pd.DataFrame(rows)

    # --------------------------------------------------
    # Merge + dedupe
    # --------------------------------------------------
    if existing is not None:
        combined = pd.concat([new_df, existing], ignore_index=True)
    else:
        combined = new_df

    combined["game_date"] = pd.to_datetime(
        combined["game_date"],
        utc=True,
        errors="coerce",
        format="mixed"
    )

    combined = combined.drop_duplicates(
        subset=["game_id", "team_id"],
        keep="first"
    )

    combined = combined.sort_values(
        ["game_date", "game_id"],
        ascending=[False, False]
    )

    # --------------------------------------------------
    # Save
    # --------------------------------------------------
    FACTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(FACTS_PATH, index=False)

    print(
        f"Appended games from {start_date} to {end_date} "
        f"({len(new_df)} rows)"
    )


if __name__ == "__main__":
    main()
