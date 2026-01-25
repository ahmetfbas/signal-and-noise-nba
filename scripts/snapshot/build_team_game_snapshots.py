import pandas as pd
from pathlib import Path

# --------------------------------------------------
# Resolve project root (signal-and-noise-nba/)
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]

# --------------------------------------------------
# Paths
# --------------------------------------------------
IN_PATH = BASE_DIR / "data" / "derived" / "team_game_metrics.csv"
OUT_PATH = BASE_DIR / "data" / "snapshots" / "team_game_snapshots.csv"

# --------------------------------------------------
# Load derived metrics table
# --------------------------------------------------
df = pd.read_csv(IN_PATH)

# --------------------------------------------------
# Ensure datetime
# --------------------------------------------------
df["game_date"] = pd.to_datetime(df["game_date"], utc=True)

# --------------------------------------------------
# Sort correctly (critical for shifting)
# --------------------------------------------------
df = df.sort_values(["team_id", "game_date"])

# --------------------------------------------------
# Pre-game snapshot metrics (no leakage)
# --------------------------------------------------
metrics_to_shift = [
    "avg_point_diff_5",
    "avg_point_diff_10",
    "avg_point_diff_15",
    "std_point_diff_10"
]

for col in metrics_to_shift:
    df[f"{col}_pre"] = (
        df.groupby("team_id")[col]
          .shift(1)
    )

# --------------------------------------------------
# Remove rows without sufficient history
# --------------------------------------------------
df_snapshots = df.dropna(
    subset=[f"{c}_pre" for c in metrics_to_shift]
)

# --------------------------------------------------
# Select final snapshot schema
# --------------------------------------------------
snapshot_columns = [
    "game_id",
    "game_date",
    "team_id",
    "team_name",
    "opponent_id",
    "opponent_name",
    "home_away",
    "team_points",
    "opponent_points",
    "point_diff",
    "win",
    "avg_point_diff_5_pre",
    "avg_point_diff_10_pre",
    "avg_point_diff_15_pre",
    "std_point_diff_10_pre"
]

df_snapshots = df_snapshots[snapshot_columns]

# --------------------------------------------------
# Save snapshot table
# --------------------------------------------------
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
df_snapshots.to_csv(OUT_PATH, index=False)
