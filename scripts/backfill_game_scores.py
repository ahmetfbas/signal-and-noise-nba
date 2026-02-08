import os
import pandas as pd
import time
import requests

API_KEY = os.getenv("BALLDONTLIE_API_KEY")
if not API_KEY:
    raise RuntimeError("BALLDONTLIE_API_KEY not set")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}

API_URL = "https://api.balldontlie.io/v1/games"
CSV_PATH = "data/core/team_game_facts.csv"

df = pd.read_csv(CSV_PATH, parse_dates=["game_date"])

bad = df[(df["team_points"] == 0) & (df["opponent_points"] == 0)].copy()

print(f"Found {bad['game_id'].nunique()} games to backfill")

for gid, g in bad.groupby("game_id"):
    sample = g.iloc[0]

    game_date = sample["game_date"].strftime("%Y-%m-%d")
    team = sample["team_name"]
    opp = sample["opponent_name"]

    print(f"\nRefetching {team} vs {opp} on {game_date}")

    params = {
        "dates[]": game_date,
        "per_page": 100
    }

    r = requests.get(API_URL, params=params, headers=HEADERS)
    if r.status_code == 429:
        print("  ⏸ rate limited — stopping run, resume later")
        break

    if r.status_code != 200:
        print(f"  ❌ API error {r.status_code}: {r.text[:200]}")
        continue



    games = r.json()["data"]

    match = None
    for game in games:
        names = {
            game["home_team"]["full_name"],
            game["visitor_team"]["full_name"]
        }
        if team in names and opp in names:
            match = game
            break

    if not match or match["status"] != "Final":
        print("  ⏳ no final match found")
        continue

    home = match["home_team"]["full_name"]
    home_pts = match["home_team_score"]
    away_pts = match["visitor_team_score"]

    def resolve_points(row):
        if row["team_name"] == home:
            return home_pts, away_pts
        else:
            return away_pts, home_pts

    df.loc[df["game_id"] == gid, ["team_points", "opponent_points"]] = (
        df[df["game_id"] == gid]
        .apply(lambda r: pd.Series(resolve_points(r)), axis=1)
        .values
    )

    print(f"  ✅ filled: {home_pts}-{away_pts}")
    time.sleep(1.5)

df.to_csv(CSV_PATH, index=False)
print("\n✅ Backfill complete")
