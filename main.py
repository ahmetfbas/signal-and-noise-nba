import os
import requests
from datetime import datetime, timedelta
from collections import defaultdict

API_URL = "https://api.balldontlie.io/v1/games"
API_KEY = os.getenv("BALLDONTLIE_API_KEY")

if not API_KEY:
    raise ValueError("BALLDONTLIE_API_KEY environment variable not set")

HEADERS = {"Authorization": API_KEY}

# ---------------- API ----------------
def fetch_games(start_date: str, end_date: str):
    """
    Fetch all games between start_date and end_date (inclusive),
    handling pagination.
    Dates must be ISO strings: YYYY-MM-DD
    """
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

        total_pages = payload.get("meta", {}).get("total_pages", 1)
        if page >= total_pages:
            break

        page += 1

    return all_games

def game_datetime(game):
    # API is consistent; we treat this as ground truth
    return datetime.fromisoformat(game["date"].replace("Z", "+00:00"))

def game_day(game) -> str:
    return game_datetime(game).date().isoformat()

# ---------------- DEBUG PRINT ----------------
def print_games_grouped_by_day(games, title):
    print(f"\n{title}")
    print("=" * len(title))

    if not games:
        print("No games.")
        return

    by_day = defaultdict(list)
    for g in games:
        by_day[game_day(g)].append(g)

    for day in sorted(by_day.keys()):
        print(f"📅 {day} — {len(by_day[day])} games")
        for g in by_day[day]:
            away = g["visitor_team"]["full_name"]
            home = g["home_team"]["full_name"]
            tip = game_datetime(g).strftime("%Y-%m-%d %H:%M UTC")
            print(f"  {away} @ {home} | tipoff: {tip}")
        print("-" * 60)
        
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

    target_date = today.isoformat()
    history_start = (today - timedelta(days=14)).isoformat()
    history_end = target_date  # we will enforce < today in logic

    print(f"Yesterday : {yesterday.isoformat()}")
    print(f"Today     : {target_date}")

    # ---------------- FETCH ----------------
    # Today slate
    games_today = fetch_games(target_date, target_date)

    # History window for density (and future metrics)
    games_last_14 = fetch_games(history_start, history_end)

    # ---------------- SANITY: RAW API ----------------
    print_games_grouped_by_day(
        games_last_14,
        f"API sanity — Games from last 14 days ({history_start} → {history_end})"
    )

    print_games_grouped_by_day(
        games_today,
        f"Today slate ({target_date})"
    )

    # ---------------- STEP 1: TEAMS PLAYING TODAY ----------------
    teams_today = set()
    team_id_to_name = {}

    for g in games_today:
        home = g["home_team"]
        away = g["visitor_team"]

        teams_today.add(home["id"])
        teams_today.add(away["id"])

        team_id_to_name[home["id"]] = home["full_name"]
        team_id_to_name[away["id"]] = away["full_name"]

    print("\nTeams playing today:")
    for tid in teams_today:
        print(f"- {team_id_to_name[tid]}")

    # ---------------- STEP 2: DENSITY COUNTS ----------------
    print("\n--- DENSITY COUNTS (raw) ---")

    density_raw = {}

    for team_id in teams_today:
        g7 = count_games_in_window(
            team_id,
            games_last_14,
            today - timedelta(days=7),
            today  # strictly before today
        )

        g14 = count_games_in_window(
            team_id,
            games_last_14,
            today - timedelta(days=14),
            today
        )

        density_raw[team_id] = (g7, g14)

        print(
            f"{team_id_to_name[team_id]} → "
            f"G7 = {g7}, G14 = {g14}"
        )

    # ---------------- STEP 3: MAP → BLEND ----------------
    print("\n--- DENSITY SCORES (mapped & blended) ---")

    for team_id, (g7, g14) in density_raw.items():
        d7 = density_7d_score(g7)
        d14 = density_14d_score(g14)

        density_score = round(0.65 * d7 + 0.35 * d14, 1)

        print(
            f"{team_id_to_name[team_id]}\n"
            f"  G7={g7} → D7={d7}\n"
            f"  G14={g14} → D14={d14}\n"
            f"  Final Density Score = {density_score}\n"
        )


if __name__ == "__main__":
    main()
