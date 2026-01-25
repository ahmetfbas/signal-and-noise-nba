import pandas as pd
from pathlib import Path

# --------------------------------------------------
# Resolve project root (signal-and-noise-nba/)
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]

# --------------------------------------------------
# Paths
# --------------------------------------------------
IN_PATH = BASE_DIR / "data" / "archive" / "team_games_2020_plus.csv"
OUT_PATH = BASE_DIR / "data" / "core" / "team_game_facts.csv"

# --------------------------------------------------
# Load filtered historical games
# --------------------------------------------------
df = pd.read_csv(IN_PATH)
print("loaded")

# --------------------------------------------------
# Ensure datetime
# --------------------------------------------------
df["game_date"] = pd.to_datetime(df["game_date"], utc=True)

# --------------------------------------------------
# Normalize into team-level facts
# --------------------------------------------------

home = pd.DataFrame({
    "game_id": df["gameId"],
    "game_date": df["game_date"],
    "team_id": df["hometeamId"],
    "team_name": df["hometeamName"],
    "opponent_id": df["awayteamId"],
    "opponent_name": df["awayteamName"],
    "home_away": "H",
    "team_points": df["homeScore"],
    "opponent_points": df["awayScore"]
})

away = pd.DataFrame({
    "game_id": df["gameId"],
    "game_date": df["game_date"],
    "team_id": df["awayteamId"],
    "team_name": df["awayteamName"],
    "opponent_id": df["hometeamId"],
    "opponent_name": df["hometeamName"],
    "home_away": "A",
    "team_points": df["awayScore"],
    "opponent_points": df["homeScore"]
})

team_game_facts = pd.concat([home, away], ignore_index=True)

# --------------------------------------------------
# Save core fact table
# --------------------------------------------------
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
print("saving")
team_game_facts.to_csv(OUT_PATH, index=False)
print("done")
