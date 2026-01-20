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

# ---------------- METRICS ----------------
def parse_game_date(game):
    """
    Convert API UTC timestamp into NBA local game date.
    Games starting before 06:00 UTC belong to the previous NBA date.
    """
    dt_utc = datetime.fromisoformat(
        game["date"].replace("Z", "+00:00")
    )

    # NBA day rollover rule
    if dt_utc.hour < 6:
        return (dt_utc - timedelta(days=1)).date()

    return dt_utc.date()


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

def days_since_last_game(team_id, games, cutoff_date, debug=False, debug_team_name=None, window_days=21):
    """
    Returns number of days since last game strictly before cutoff_date.
    Debug prints the candidate dates and chosen last game date.
    """
    past_dates = []
    for g in games:
        is_team = (g["home_team"]["id"] == team_id or g["visitor_team"]["id"] == team_id)
        if not is_team:
            continue

        gd = parse_game_date(g)
        if gd < cutoff_date:
            past_dates.append(gd)

    if debug:
        # show a focused window around the cutoff for readability
        start_w = cutoff_date - timedelta(days=window_days)
        window_dates = sorted([d for d in past_dates if start_w <= d < cutoff_date])

        print("\n[DEBUG days_since_last_game]")
        if debug_team_name:
            print(f"Team: {debug_team_name} (id={team_id})")
        else:
            print(f"Team id: {team_id}")
        print(f"Cutoff (target game date): {cutoff_date}")
        print(f"Candidate past game dates found: {len(past_dates)}")
        print(f"Window dates (last {window_days} days before cutoff): {window_dates}")

    if not past_dates:
        if debug:
            print("=> No past dates found in provided games window. Returning None.\n")
        return None

    last_game_date = max(past_dates)
    days = (cutoff_date - last_game_date).days

    if debug:
        print(f"Chosen last game date: {last_game_date}")
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
    # Explicit slate date (can override)
    target_date = datetime.utcnow().date().isoformat()
    # target_date = "2026-01-21"

    cutoff_date = datetime.fromisoformat(target_date).date()

    print(f"NBA Schedule Density — {target_date}\n")

    # Fetch slate games
    games_today = fetch_games(target_date, target_date)
    if not games_today:
        print("No NBA games on this date.")
        return

    # Fetch historical windows
    start_7d = (cutoff_date - timedelta(days=7)).isoformat()
    start_14d = (cutoff_date - timedelta(days=14)).isoformat()

    games_7d = fetch_games(start_7d, target_date)
    games_14d = fetch_games(start_14d, target_date)

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

        debug_team = "Phoenix Suns"  # change this to any full_name you want to inspect
        
        # Days since last game (B2B detection)
        away_days_rest = days_since_last_game(
            away["id"], games_14d, cutoff_date,
            debug=(away["full_name"] == debug_team),
            debug_team_name=away["full_name"]
        )
        
        home_days_rest = days_since_last_game(
            home["id"], games_14d, cutoff_date,
            debug=(home["full_name"] == debug_team),
            debug_team_name=home["full_name"]
        )

        print(f"{away['full_name']} @ {home['full_name']}")
        print(
            f"• {away['full_name']}: "
            f"{density_label(away_D)} (D={away_D}), "
            f"{rest_context_label(away_days_rest)}"
        )
        print(
            f"• {home['full_name']}: "
            f"{density_label(home_D)} (D={home_D}), "
            f"{rest_context_label(home_days_rest)}"
        )
        print()

if __name__ == "__main__":
    main()
