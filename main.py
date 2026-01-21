import os
import requests
from datetime import datetime, timedelta

API_URL = "https://api.balldontlie.io/v1/games"
API_KEY = os.getenv("BALLDONTLIE_API_KEY")

if not API_KEY:
    raise ValueError("BALLDONTLIE_API_KEY environment variable not set")

HEADERS = {"Authorization": API_KEY}

# ---------------- API ----------------
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

        resp = requests.get(API_URL, headers=HEADERS, params=params)
        if resp.status_code != 200:
            raise RuntimeError(f"API error {resp.status_code}: {resp.text}")

        payload = resp.json()
        all_games.extend(payload.get("data", []))

        if page >= payload.get("meta", {}).get("total_pages", 1):
            break

        page += 1

    return all_games


# ---------------- DATE HELPERS ----------------
def game_datetime(game):
    return datetime.fromisoformat(game["date"].replace("Z", "+00:00"))


# ---------------- DENSITY HELPERS ----------------
def count_games_in_window(team_id, games, start_date, end_date):
    """
    Counts games where:
    start_date <= game_date < end_date
    """
    count = 0
    for g in games:
        gd = game_datetime(g).date()
        if start_date <= gd < end_date:
            if g["home_team"]["id"] == team_id or g["visitor_team"]["id"] == team_id:
                count += 1
    return count


def density_7d_score(g7):
    if g7 <= 2:
        return 10
    if g7 == 3:
        return 40
    if g7 == 4:
        return 75
    return 95


def density_14d_score(g14):
    if g14 <= 4:
        return 10
    if g14 == 5:
        return 35
    if g14 == 6:
        return 55
    if g14 == 7:
        return 75
    return 95


# ---------------- MAIN ----------------
def main():
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)

    print(f"Yesterday : {yesterday.isoformat()}")
    print(f"Today     : {today.isoformat()}")

    # --- Fetch windows ---
    start_7 = (today - timedelta(days=6)).isoformat()
    start_14 = (today - timedelta(days=13)).isoformat()
    end_date = today.isoformat()

    games_last_7 = fetch_games(start_7, end_date)
    games_last_14 = fetch_games(start_14, end_date)

    # --- Teams playing today ---
    teams_today = {}
    for g in games_last_7:
        if game_datetime(g).date() == today:
            home = g["home_team"]
            away = g["visitor_team"]
            teams_today[home["id"]] = home["full_name"]
            teams_today[away["id"]] = away["full_name"]

    print("\nDENSITY — Teams playing today\n")

    # --- Density calculation ---
    for team_id, team_name in teams_today.items():
        g7 = count_games_in_window(
            team_id,
            games_last_7,
            today - timedelta(days=7),
            today
        )

        g14 = count_games_in_window(
            team_id,
            games_last_14,
            today - timedelta(days=14),
            today
        )

        d7 = density_7d_score(g7)
        d14 = density_14d_score(g14)
        D = round(0.65 * d7 + 0.35 * d14, 1)

        print(
            f"{team_name}\n"
            f"  G7  = {g7} → D7 = {d7}\n"
            f"  G14 = {g14} → D14 = {d14}\n"
            f"  Blended Density D = {D}\n"
        )


if __name__ == "__main__":
    main()
