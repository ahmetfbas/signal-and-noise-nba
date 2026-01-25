import pandas as pd

df = pd.read_csv("team_games.csv")

# normalize column name
df = df.rename(columns={"gameDateTimeEst": "game_date"})

# parse datetime safely (handles timezone)
df["game_date"] = pd.to_datetime(df["game_date"], utc=True)

# filter
filtered = df[df["game_date"] >= "2020-01-01"]

# save
filtered.to_csv("team_games_2020_plus.csv", index=False)
