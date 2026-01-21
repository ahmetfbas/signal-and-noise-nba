import os
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

    while True:
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "per_page": 100,
            "page": page
        }

        response = requests.get(API_URL, headers=HEADERS, params=params)
        if response.status_code != 200:
            raise RuntimeError(f"API error {response.status_code}: {response.text}")

        payload = response.json()
        all_games.extend(payload.get("data", []))

        if page >= payload.get("meta", {}).get("total_pages", 1):
            break

        page += 1

    return all_games

# ---------------- HELPERS ----------------
def game_datetime(game):
    return datetime.fromisoformat(game["date"].replace("Z", "+00:00"))

def rest_context_label(days_since):
    if days_since is None:
        return "No recent games"
    if days_since == 1:
        return "Back-to-Back"
    if days_since == 2:
        return "1 off-day"
    if days_since == 3:
        return "2 off-days"
    return "3+ off-days"


def last_game_before(team_id, all_games, current_game):
    """
    Finds the last game this team played before current_game.
    Returns (date, city)
    """
    current_dt = game_datetime(current_game)

    team_games = [
        g for g in all_games
        if (g["home_team"]["id"] == team_id or g["visitor_team"]["id"] == team_id)
        and game_datetime(g) < current_dt
    ]

    if not team_games:
        return None, None

    last_game = max(team_games, key=game_datetime)
    last_date = game_datetime(last_game).date()
    last_city = last_game["home_team"]["city"]  # game location

    return last_date, last_city

# ---------------- MAIN ----------------
def main():
    target_date = datetime.utcnow().date().isoformat()
    print(f"NBA Schedule Debug — {target_date}\n")

    # Fetch slate games
    games_today = fetch_games(target_date, target_date)
    if not games_today:
        return

    # Fetch ONE history window (wide enough)
    history_start = (datetime.fromisoformat(target_date) - timedelta(days=15)).date().isoformat()
    history_end = target_date

    all_recent_games = fetch_games(history_start, history_end)

    for game in games_today:
        away = game["visitor_team"]
        home = game["home_team"]

        target_city = home["city"]
        target_game_date = game_datetime(game).date()

        away_last_date, away_last_city = last_game_before(
            away["id"], all_recent_games, game
        )
        home_last_date, home_last_city = last_game_before(
            home["id"], all_recent_games, game
        )

        away_days_rest = None if away_last_date is None else (target_game_date - away_last_date).days
        home_days_rest = None if home_last_date is None else (target_game_date - home_last_date).days

        print(f"{away['full_name']} @ {home['full_name']}")

        print(
            f"• {away['full_name']}\n"
            f"  Target game date : {target_game_date}\n"
            f"  Last game date   : {away_last_date}\n"
            f"  Target city      : {target_city}\n"
            f"  Last game city   : {away_last_city}\n"
            f"  Rest context     : {rest_context_label(away_days_rest)}"
        )

        print(
            f"• {home['full_name']}\n"
            f"  Target game date : {target_game_date}\n"
            f"  Last game date   : {home_last_date}\n"
            f"  Target city      : {target_city}\n"
            f"  Last game city   : {home_last_city}\n"
            f"  Rest context     : {rest_context_label(home_days_rest)}"
        )

        print()

if __name__ == "__main__":
    main()
