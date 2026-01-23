import os
import time
import requests
from datetime import datetime, timedelta

API_URL = "https://api.balldontlie.io/v1/games"
API_KEY = os.getenv("BALLDONTLIE_API_KEY")

if not API_KEY:
    raise ValueError("BALLDONTLIE_API_KEY environment variable not set")

HEADERS = {"Authorization": API_KEY}


# ---------------- API ----------------
def fetch_games(start_date, end_date):
    all_games = []
    page = 1
    PER_PAGE = 100
    MAX_RETRIES = 5

    while True:
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "per_page": PER_PAGE,
            "page": page
        }

        retries = 0
        while True:
            r = requests.get(API_URL, headers=HEADERS, params=params, timeout=30)

            if r.status_code == 200:
                break

            if r.status_code == 429:
                wait = 2 ** retries
                print(f"Rate limited. Sleeping {wait}s...")
                time.sleep(wait)
                retries += 1
                if retries >= MAX_RETRIES:
                    raise RuntimeError("Exceeded max retries due to rate limiting.")
                continue

            raise RuntimeError(r.text)

        payload = r.json()
        data = payload.get("data", [])
        all_games.extend(data)

        # Stop when this page is not full
        if len(data) < PER_PAGE:
            break

        page += 1
        time.sleep(0.4)  # polite pause

    return all_games


# ---------------- HELPERS ----------------
def game_datetime(game):
    return datetime.fromisoformat(game["date"].replace("Z", "+00:00"))


def is_completed(game):
    return (
        game.get("home_team_score") is not None
        and game.get("visitor_team_score") is not None
    )


# ---------------- MAIN LOGIC ----------------
def print_last_10_charlotte_games():
    TEAM = "Charlotte Hornets"

    # 🔒 Anchor to a KNOWN real completed game date
    END_DATE_STR = "2026-01-22"
    END_DATE = datetime.fromisoformat(END_DATE_STR).date()

    LOOKBACK_DAYS = 300
    start_date = (END_DATE - timedelta(days=LOOKBACK_DAYS)).isoformat()
    end_date = END_DATE_STR

    print(f"\nFetching games from {start_date} to {end_date}...\n")

    games = fetch_games(start_date, end_date)

    # Filter Charlotte + completed games
    char_games = [
        g for g in games
        if is_completed(g)
        and (
            g["home_team"]["full_name"] == TEAM
            or g["visitor_team"]["full_name"] == TEAM
        )
    ]

    # Sort newest → oldest
    char_games.sort(key=game_datetime, reverse=True)

    last_10 = char_games[:10]

    print(f"🔎 Last {len(last_10)} completed games for {TEAM} before {END_DATE_STR}\n")

    if not last_10:
        print("No games found. Increase LOOKBACK_DAYS.")
        return

    # Print oldest → newest for readability
    for g in reversed(last_10):
        is_home = g["home_team"]["full_name"] == TEAM
        opponent = (
            g["visitor_team"]["full_name"]
            if is_home
            else g["home_team"]["full_name"]
        )

        team_score = g["home_team_score"] if is_home else g["visitor_team_score"]
        opp_score = g["visitor_team_score"] if is_home else g["home_team_score"]
        margin = team_score - opp_score

        loc = "HOME" if is_home else "AWAY"
        date = game_datetime(g).date()

        print(f"{date} | {loc} vs {opponent} | {team_score}-{opp_score} | margin: {margin:+}")


# ---------------- RUN ----------------
if __name__ == "__main__":
    print_last_10_charlotte_games()
