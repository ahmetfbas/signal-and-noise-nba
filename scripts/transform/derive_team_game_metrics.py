import pandas as pd
from pathlib import Path

# --------------------------------------------------
# Resolve project root (signal-and-noise-nba/)
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]

# --------------------------------------------------
# Paths
# --------------------------------------------------
IN_PATH = BASE_DIR / "data" / "core" / "team_game_facts.csv"
OUT_PATH = BASE_DIR / "data" / "derived" / "team_game_metrics.csv"

# --------------------------------------------------
# Load core fact table
# --------------------------------------------------
df = pd.read_csv(IN_PATH)

# --------------------------------------------------
# Ensure datetime
# --------------------------------------------------
df["game_date"] = pd.to_datetime(df["game_date"], utc=True)

# --------------------------------------------------
# Sort correctly (critical for rolling windows)
# --------------------------------------------------
df = df.sort_values(["team_id", "game_date"])

# -----------------------------
# Basic derived metrics
# -----------------------------

# Point differential
df["point_diff"] = df["team_points"] - df["opponent_points"]

# Win flag
df["win"] = (df["point_diff"] > 0).astype(int)

# -----------------------------
# Rolling metrics (index-safe)
# -----------------------------

# Rolling 5 games average point diff
df["avg_point_diff_5"] = (
    df.groupby("team_id")["point_diff"]
      .transform(lambda s: s.rolling(window=5, min_periods=1).mean())
)

# Rolling 10 games average point diff
df["avg_point_diff_10"] = (
    df.groupby("team_id")["point_diff"]
      .transform(lambda s: s.rolling(window=10, min_periods=1).mean())
)

# Rolling 15 games average point diff
df["avg_point_diff_15"] = (
    df.groupby("team_id")["point_diff"]
      .transform(lambda s: s.rolling(window=15, min_periods=1).mean())
)

# Rolling 10 games volatility (std)
print("computing rolling std...")
df["std_point_diff_10"] = (
    df.groupby("team_id")["point_diff"]
      .transform(lambda s: s.rolling(window=10, min_periods=2).std())
)
print("rolling std done")

# -----------------------------
# Save derived table
# -----------------------------

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
print("saving file...")
df.to_csv(OUT_PATH, index=False)
print("done")
