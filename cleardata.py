import pandas as pd

# 1️⃣ Load your normalized team_games file
df = pd.read_csv("team_games.csv")

# 2️⃣ Convert date column to actual dates
df["game_date"] = pd.to_datetime(df["game_date"])

# 3️⃣ Filter rows (keep 2020+)
filtered = df[df["game_date"] >= "2020-01-01"]

# 4️⃣ Save to a new file (safe)
filtered.to_csv("team_games_2020_plus.csv", index=False)
