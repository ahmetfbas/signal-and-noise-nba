import os
import requests
from datetime import datetime, timedelta

API_URL = "https://api.balldontlie.io/v1/games"
API_KEY = os.getenv("BALLDONTLIE_API_KEY")

if not API_KEY:
    raise ValueError("BALLDONTLIE_API_KEY environment variable not set")

HEADERS = {
    "Authorization": API_KEY
}

# ---------------- API ----------------
def fetch_games(start_date, end_date):
    params = {
        "start_date": start_date,
        "end_date": end_date,
        "per_page": 100
    }

    response = requests.get(API_URL, headers=HEADERS, params=params)

    if response.status_code != 200:
        print("API error:", response.status_code)
        print(response.text)
        return []

    return response.json()["data"]

# ---------------- DATE NORMALIZATION ----------------
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")

def parse_game_date(game):
    """
    Convert API UTC timestamp into US Eastern calendar date (NBA fan 'game day').
    This avoids brittle UTC cutoff hacks and matches "today in the US".
    """
    dt_utc = datetime.fromisoformat(game["date"].replace("Z", "+00:00"))
    dt_et = dt_utc.astimezone(ET)
    return dt_et.date()

# ---------------- METRICS ----------------
def count_games_before(team_id, games, cutoff_date):
    return sum(
        1
        for g in games
        if (
            (g["home_team"]["id"] == team_id
             or g["visitor_team"]["id"] == team_id)
            and parse_game_date(g) < cutoff_date
        )
    )

def schedule_density_score(g7, g14):
    d7 = g7 / 7
    d14 = g14 / 14
    d_raw = 0.6 * d7 + 0.4 * d14
    return round(100 * d_raw, 1)

def density_label(D):
    if D < 35:
        return "Light"
    elif D < 50:
        return "Moderate"
    elif D < 65:
        return "Heavy"
    else:
        return "Extreme"

def days_since_last_game(team_id, games, cutoff_date, debug=False, team_name=None):
    past_dates = [
        parse_game_date(g)
        for g in games
        if (
            (g["home_team"]["id"] == team_id
             or g["visitor_team"]["id"] == team_id)
            and parse_game_date(g) < cutoff_date
        )
    ]

    if debug:
        print("\n[DEBUG days_since_last_game]")
        print(f"Team: {team_name} (id={team_id})")
        print(f"Cutoff date: {cutoff_date}")
        print(f"Past dates found: {sorted(past_dates)}")

    if not past_dates:
        return None

    last_game = max(past_dates)
    days = (cutoff_date - last_game).days

    if debug:
        print(f"Last game date: {last_game}")
        print(f"Days since last game: {days}\n")

    return days

def rest_context_label(days_since):
    if days_since is None:
        return "No recent games"
    elif days_since == 1:
        return "Back-to-Back"
    elif days_since == 2:
        return "1 day rest"
    else:
        return "3+ days rest"

# ---------------- MAIN ----------------
def main():
    # Slate date (NBA day)
    target_date = datetime.utcnow().date().isoformat()
    # target_date = "2026-01-20"  # manual override if needed

    cutoff_date = datetime.fromisoformat(target_date).date()

    print(f"NBA Schedule Density — {target_date}\n")

    # Games on the slate
    games_today = fetch_games(target_date, target_date)
    if not games_today:
        print("No NBA games on this date.")
        return

    # --------- CRITICAL FIX ----------
    # Historical data must include the FULL previous NBA day
    history_end = (cutoff_date + timedelta(days=1)).isoformat()

    start_7d = (cutoff_date - timedelta(days=7)).isoformat()
    start_14d = (cutoff_date - timedelta(days=14)).isoformat()

    games_7d = fetch_games(start_7d, history_end)
    games_14d = fetch_games(start_14d, history_end)
    # ---------------------------------

    debug_team = "Phoenix Suns"  # set None to disable debug

    for game in games_today:
        away = game["visitor_team"]
        home = game["home_team"]

        # Density
        away_7d = count_games_before(away["id"], games_7d, cutoff_date)
        away_14d = count_games_before(away["id"], games_14d, cutoff_date)
        home_7d = count_games_before(home["id"], games_7d, cutoff_date)
        home_14d = count_games_before(home["id"], games_14d, cutoff_date)

        away_D = schedule_density_score(away_7d, away_14d)
        home_D = schedule_density_score(home_7d, home_14d)

        # Days since last game (B2B logic)
        away_rest = days_since_last_game(
            away["id"], games_14d, cutoff_date,
            debug=(away["full_name"] == debug_team),
            team_name=away["full_name"]
        )

        home_rest = days_since_last_game(
            home["id"], games_14d, cutoff_date,
            debug=(home["full_name"] == debug_team),
            team_name=home["full_name"]
        )

        print(f"{away['full_name']} @ {home['full_name']}")
        print(f"• {away['full_name']}: {density_label(away_D)} (D={away_D}), {rest_context_label(away_rest)}")
        print(f"• {home['full_name']}: {density_label(home_D)} (D={home_D}), {rest_context_label(home_rest)}")
        print()

if __name__ == "__main__":
    main()
