import os
import requests
import pandas as pd
from datetime import datetime, date

API_URL = "https://api.balldontlie.io/v1/games"
API_KEY = os.getenv("BALLDONTLIE_API_KEY")


def fetch_today_games(run_date: date) -> pd.DataFrame:
    if not API_KEY:
        raise RuntimeError("BALLDONTLIE_API_KEY is not set")

    params = {
        "dates[]": run_date.isoformat(),
        "per_page": 100,
    }

    # BallDontLie v1 auth (NO Bearer)
    headers = {
        "Authorization": API_KEY
    }

    r = requests.get(API_URL, params=params, headers=headers, timeout=30)
    r.raise_for_status()

    games = r.json().get("data", [])

    rows = []
    for g in games:
        rows.append({
            "game_id": g["id"],
            "game_date": run_date.isoformat(),
            "home_team_id": g["home_team"]["id"],
            "home_team_name": g["home_team"]["full_name"],
            "away_team_id": g["visitor_team"]["id"],
            "away_team_name": g["visitor_team"]["full_name"],
            "matchup": f'{g["visitor_team"]["abbreviation"]} @ {g["home_team"]["abbreviation"]}',
        })

    return pd.DataFrame(rows)


def main():
    # Use UTC to stay consistent with pipeline
    run_date = datetime.utcnow().date()
    df = fetch_today_games(run_date)

    output_path = "data/derived/game_schedule_today.csv"
    df.to_csv(output_path, index=False)

    print(f"Saved {len(df)} games to {output_path}")


if __name__ == "__main__":
    main()
