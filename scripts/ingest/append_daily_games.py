# scripts/ingest/append_daily_games.py

from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

from scripts.ingest.data_provider import fetch_games_range
from scripts.utils.utils import game_date, is_completed

# --------------------------------------------------
# Time configuration
# --------------------------------------------------
# Job is expected to run daily at 09:00 UTC
NOW_UTC = datetime.utcnow()
RUN_DATE = NOW_UTC.date()

# We append games from "yesterday"
TARGET_DATE = RUN_DATE - timedelta(days=1)

# --------------------------------------------------
# Resolve project root
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]

FACTS_PATH = BASE_DIR / "data" / "core" / "team_game_facts.csv"

# --------------------------------------------------
# Fetch yesterday's games
# --------------------------------------------------
games = fetch_games_range(
    TARGET_DATE.isoformat(),
    TARGET_DATE.isoformat()
)

games = [
    g for g in games
    if game_date(g) == TARGET_DATE and is_completed(g)
]

if not games:
    print("No completed games to append.")
    exit(0)

# --------------------------------------------------
# Normalize to team-level rows
# --------------------------------------------------
rows = []

for g in games:
    gid = g["id"]
    gd = game_date(g)

    home = g["home_team"]
    away = g["visitor_team"]

    rows.append({
        "game_id": gid,
        "game_date": gd,
        "team_id": home["id"],
        "team_name": home["full_name"],
        "opponent_id": away["id"],
        "opponent_name": away["full_name"],
        "home_away": "H",
        "team_points": g["home_team_score"],
        "opponent_points": g["visitor_team_score"],
    })

    rows.append({
        "game_id": gid,
        "game_date": gd,
        "team_id": away["id"],
        "team_name": away["full_name"],
        "opponent_id": home["id"],
        "opponent_name": home["full_name"],
        "home_away": "A",
        "team_points": g["visitor_team_score"],
        "opponent_points": g["home_team_score"],
    })

new_df = pd.DataFrame(rows)

# --------------------------------------------------
# Load existing facts (if any)
# --------------------------------------------------
if FACTS_PATH.exists():
    existing = pd.read_csv(FACTS_PATH)
    combined = pd.concat([existing, new_df], ignore_index=True)

    # Deduplicate by (game_id, team_id)
    combined = combined.drop_duplicates(
        subset=["game_id", "team_id"],
        keep="last"
    )
else:
    FACTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    combined = new_df

# --------------------------------------------------
# Save updated fact table
# --------------------------------------------------
combined.to_csv(FACTS_PATH, index=False)

print(
    f"Appended {len(new_df)} rows "
    f"for games on {TARGET_DATE}"
)
