import pandas as pd
from pathlib import Path

# --------------------------------------------------
# Resolve project root (signal-and-noise-nba/)
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]

# --------------------------------------------------
# Paths
# --------------------------------------------------
RAW_PATH = BASE_DIR / "data" / "raw" / "team_games.csv"
OUT_PATH = BASE_DIR / "data" / "archive" / "team_games_2020_plus.csv"

# --------------------------------------------------
# Load raw data
# --------------------------------------------------
df = pd.read_csv(RAW_PATH)

# --------------------------------------------------
# Normalize column names
# --------------------------------------------------
df = df.rename(columns={"gameDateTimeEst": "game_date"})

# --------------------------------------------------
# Robust datetime parsing (mixed formats + timezones)
# --------------------------------------------------
df["game_date"] = pd.to_datetime(
    df["game_date"],
    utc=True,
    format="mixed",
    errors="coerce"
)

# --------------------------------------------------
# Apply historical cutoff
# --------------------------------------------------
filtered = df[df["game_date"] >= "2020-01-01"]

# --------------------------------------------------
# Save filtered archive
# --------------------------------------------------
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
filtered.to_csv(OUT_PATH, index=False)
