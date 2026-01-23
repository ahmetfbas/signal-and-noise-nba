import os
import requests
from datetime import datetime, timedelta

API_URL = "https://api.balldontlie.io/v1/games"
API_KEY = os.getenv("BALLDONTLIE_API_KEY")
if not API_KEY:
    raise ValueError("BALLDONTLIE_API_KEY environment variable not set")

HEADERS = {"Authorization": API_KEY}


def fetch_games(start_date: str, end_date: str):
    all_games = []
    page = 1

    while True:
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "per_page": 100,
            "page": page
        }

        resp = requests.get(API_URL, headers=HEADERS, params=params, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"API error {resp.status_code}: {resp.text}")

        payload = resp.json()
        all_games.extend(payload.get("data", []))

        if page >= payload.get("meta", {}).get("total_pages", 1):
            break
        page += 1

    return all_games


def game_datetime(game):
    return datetime.fromisoformat(game["date"].replace("Z", "+00:00"))


def game_date(game):
    return game_datetime(game).date()


def is_completed(game):
    return game.get("home_team_score") is not None and game.get("visitor_team_score") is not None


def find_latest_completed_game_date(games):
    completed = [g for g in games if is_completed(g)]
    if not completed:
        return None
    return max(game_date(g) for g in completed)


def print_charlotte_last_10_completed(games, run_date):
    TEAM = "Charlotte Hornets"
    char_games = [
        g for g in games
        if is_completed(g)
        and game_date(g) < run_date
        and (g["home_team"]["full_name"] == TEAM or g["visitor_team"]["full_name"] == TEAM)
    ]

    char_games = sorted(char_games, key=game_datetime, reverse=True)[:10]

    print(f"\n🔎 Charlotte Hornets — last {len(char_games)} COMPLETED games before {run_date}\n")

    if not char_games:
        print("No completed Charlotte games found in this window.")
        return

    # Print oldest -> newest for readability
    for g in reversed(char_games):
        is_home = (g["home_team"]["full_name"] == TEAM)
        opponent = g["visitor_team"]["full_name"] if is_home else g["home_team"]["full_name"]

        team_score = g["home_team_score"] if is_home else g["visitor_team_score"]
        opp_score = g["visitor_team_score"] if is_home else g["home_team_score"]
        margin = team_score - opp_score

        loc = "HOME" if is_home else "AWAY"
        print(f"{game_date(g)} | {loc} vs {opponent} | {team_score}-{opp_score} | margin: {margin:+}")


def main():
    system_today = datetime.utcnow().date()

    # Big window just to be safe (does NOT affect last-10 logic)
    start = (system_today - timedelta(days=220)).isoformat()
    end = system_today.isoformat()

    games = fetch_games(start, end)

    latest_completed = find_latest_completed_game_date(games)
    if latest_completed is None:
        print("No completed games found in the fetched window.")
        return

    print(f"\n✅ Latest COMPLETED game date in API window: {latest_completed}")
    print(f"✅ Total games fetched: {len(games)} | Completed: {sum(1 for g in games if is_completed(g))}\n")

    print_charlotte_last_10_completed(games, latest_completed)


if __name__ == "__main__":
    main()
