import os
import requests
from datetime import datetime, timedelta

API_URL = "https://api.balldontlie.io/v1/games"
API_KEY = os.getenv("BALLDONTLIE_API_KEY")

if not API_KEY:
    raise ValueError("BALLDONTLIE_API_KEY environment variable not set")

HEADERS = {"Authorization": API_KEY}


def fetch_games(start_date, end_date):
    all_games = []
    page = 1
    PER_PAGE = 100

    while True:
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "per_page": PER_PAGE,
            "page": page
        }

        r = requests.get(API_URL, headers=HEADERS, params=params, timeout=30)
        if r.status_code != 200:
            raise RuntimeError(r.text)

        payload = r.json()
        data = payload.get("data", [])

        all_games.extend(data)

        # ✅ SAFE STOP CONDITION
        if len(data) < PER_PAGE:
            break

        page += 1

    return all_games



def game_datetime(game):
    return datetime.fromisoformat(game["date"].replace("Z", "+00:00"))


def is_completed(game):
    return (
        game["home_team_score"] is not None
        and game["visitor_team_score"] is not None
    )


def print_last_10_charlotte_games():
    TEAM = "Charlotte Hornets"

    today = datetime.utcnow().date()
    start = (today - timedelta(days=300)).isoformat()
    end = today.isoformat()

    games = fetch_games(start, end)

    char_games = [
        g for g in games
        if is_completed(g)
        and (g["home_team"]["full_name"] == TEAM or g["visitor_team"]["full_name"] == TEAM)
    ]

    # newest → oldest
    char_games.sort(key=game_datetime, reverse=True)

    last_10 = char_games[:10]

    print(f"\n🔎 Last {len(last_10)} completed games for {TEAM}\n")

    for g in reversed(last_10):
        is_home = g["home_team"]["full_name"] == TEAM
        opponent = g["visitor_team"]["full_name"] if is_home else g["home_team"]["full_name"]

        team_score = g["home_team_score"] if is_home else g["visitor_team_score"]
        opp_score = g["visitor_team_score"] if is_home else g["home_team_score"]
        margin = team_score - opp_score

        loc = "HOME" if is_home else "AWAY"
        date = game_datetime(g).date()

        print(f"{date} | {loc} vs {opponent} | {team_score}-{opp_score} | margin: {margin:+}")


if __name__ == "__main__":
    print_last_10_charlotte_games()
